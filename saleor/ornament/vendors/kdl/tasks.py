import io
import os
import re
import ftplib
import logging
from typing import Optional
from uuid import UUID
from jinja2 import Template
import requests

from ftplib import FTP
from lxml import etree
from datetime import timedelta

from zeep import Client, Settings as WSDL_Settings
from django.conf import settings
from django.utils import timezone

from saleor.celeryconf import app
from saleor.order import events, models
from saleor.ornament.utils.notification_api import NotificationApi
from saleor.utils import get_safe_lxml_parser
from saleor.order.actions import create_fulfillments_internal
from saleor.ornament.vendors.kdl.utils import collect_data_for_email

# from saleor.utils.notifications import slack_send_message_task

from .utils import (
    make_order_xml_tree,
    xml_tree_as_bytes,
    make_preorder_data,
    parse_ftp_dir_listing,
    detect_ftp_timezone_shift,
)


logger = logging.getLogger(__name__)

XML_INPUT_DIR = "/Input"
XML_OUTPUT_DIR = "/Output"
PDF_OUTPUT_DIR = "/OutputPDF"
XML_IGNORE_DIR = f"{XML_OUTPUT_DIR}Ignore"
PDF_IGNORE_DIR = f"{PDF_OUTPUT_DIR}Ignore"
FTP_IGNORE_TIMEOUT = 60 * 60 * 24

XML_FILENAME_REGEX = re.compile(r"^(\d{9,})_(\d{14}).xml$", re.I)
PDF_FILENAME_REGEX = re.compile(r"^(\d{9,})_(\d{14}).pdf$", re.I)

# Imageset API DB has the limitation of 10 chars
IMAGESET_API_SOURCE = "lab@home"


@app.task(autoretry_for=[Exception])
def place_preorder_via_wsdl(order_id: UUID) -> None:
    order = (
        models.Order.objects.select_related("user", "shipping_address")
        .prefetch_related("lines")
        .get(pk=order_id)
    )
    kdl_wsdl_client_settings = WSDL_Settings(strict=False, xml_huge_tree=True)
    client = Client(settings.KDL_WSDL_URL, settings=kdl_wsdl_client_settings)
    order_data = make_preorder_data(order)
    if order_data is None:
        logger.info(f"WSDL order_data is empty for order #{order.id}")
        return

    logger.info(f"Sending order #{order.pk} ({order_data}) to KDL over WSDL")

    try:
        result = client.service.SetOrder(order=order_data)
    except TypeError as e:
        logger.critical(
            f"Exception in KDL WSDL response for order #{order.pk}", exc_info=True
        )
        return

    logger.info(f"Got response from KDL WSDL: {result}")
    if "errors" in result:
        logger.critical(
            f"Errors in KDL WSDL response for order #{order.pk}: {result['errors']}"
        )
        return

    kdl_preorder_id = result["PreOrderID"]
    order.external_lab_id = kdl_preorder_id
    order.save(update_fields=["external_lab_id"])
    events.order_placed_to_lab_event(order=order, user=order.user, lab_name="KDL")


@app.task(autoretry_for=[Exception])
def place_xml_order_via_ftp(order_id: int) -> None:
    order = (
        models.Order.objects.select_related("user", "shipping_address")
        .prefetch_related("lines")
        .get(pk=order_id)
    )
    xml_data = make_order_xml_tree(order)
    xml_doc = io.BytesIO(xml_tree_as_bytes(xml_data))
    logger.info(f"Sending XML order #{order.pk} to KDL")
    with FTP(
        settings.KDL_FTP_HOST, settings.KDL_FTP_LOGIN, settings.KDL_FTP_PASSWORD
    ) as ftp:
        ftp.storlines(
            # This produces the 10-digit filename according to KDL rules in the Input
            # folder, i.e. `Input/0123456789.xml`, where 0 is a region code, 1234 is a
            # client number and 56789 is an order number in our system (req. 5 digits).
            f"STOR {XML_INPUT_DIR}/{settings.KDL_REGION_CODE}"
            f"{settings.KDL_CLINIC_ID[-4:]}{order.pk:05}.xml",
            xml_doc,
        )
    events.order_placed_to_lab_event(order=order, user=order.user, lab_name="KDL")


def get_default_pid_by_sso_id(sso_id: str) -> Optional[str]:
    response = requests.post(
        f"{settings.ORNAMENT_INTERNAL_DATA_API}/internal/data-api/v1.0/user/login",
        json={"ssoId": sso_id},
    )

    if response.status_code != 200 and response.json().get("message").get("code") in (
        "440020",
        "550010",
    ):
        logger.debug(f"User with sso_id {sso_id} doesn't have an Ornament account.")
        return None

    return response.json().get("defaultProfile", {}).get("pid")


@app.task(autoretry_for=[Exception])
def upload_pdf_to_imageset_api(
    order_id: UUID, user_id: int, full_path: str, sso_id: str
) -> None:
    error = None
    iid = None

    params = {
        "ssoId": sso_id,
        "source": IMAGESET_API_SOURCE,
    }

    user_default_pid = get_default_pid_by_sso_id(sso_id)

    if user_default_pid:
        params["pid"] = user_default_pid

    with open(full_path, "rb") as f:
        files = {"file": f}
        response = requests.post(
            settings.ORNAMENT_IMAGESET_API_UPLOAD_PDF_URL,
            params=params,
            files=files,
        )
    if response.status_code == 200:
        iid = response.json()["iid"]
    else:
        error = response.text
    events.order_result_imageset_upload_event(
        order_id=order_id, user_id=user_id, lab_name="KDL", error=error, iid=iid
    )
    os.remove(full_path)
    # If everything went well we fetch the whole order with all lines and pass it for
    # automatic fulfillment. Local import to avoid circular import.
    whole_order = models.Order.objects.prefetch_related("lines").get(pk=order_id)
    from saleor.order import utils

    create_fulfillments_internal(whole_order)

    utils.update_order_status(order=whole_order)


@app.task(autoretry_for=[Exception])
def send_order_confirmation(order_id: UUID):
    email_data = collect_data_for_email(order_id)
    with open(settings.KDL_ORDER_EMAIL_TEMPLATE_PATH, "r") as f:
        email_html = f.read()
    t = Template(email_html)
    body = t.render(**email_data.context)
    NotificationApi.send_email(
        recipients=email_data.recipient_list, subject=email_data.subject, body=body
    )


def check_for_new_results() -> None:
    kdl_files_indexed_by_order_id = {"orphans": {"xml": [], "pdf": []}, "index": {}}
    with FTP(
        settings.KDL_FTP_HOST, settings.KDL_FTP_LOGIN, settings.KDL_FTP_PASSWORD
    ) as ftp:
        try:
            paths = (XML_OUTPUT_DIR, PDF_OUTPUT_DIR, XML_IGNORE_DIR, PDF_IGNORE_DIR)
            ignore_timeout = timezone.now() - timedelta(seconds=FTP_IGNORE_TIMEOUT)

            # try to detect time shift in minutes
            time_shift_munites = detect_ftp_timezone_shift(ftp)

            # generate output directories
            ftp.cwd("/")
            dirs = ftp.nlst()
            for dirname in paths:
                if not dirname.lstrip("/") in dirs:
                    ftp.mkd(dirname)

            # erase old and get new xml files
            ftp.cwd(XML_OUTPUT_DIR)
            files = []
            ftp.dir(files.append)
            files = parse_ftp_dir_listing(files, time_shift=time_shift_munites)
            for index, file in enumerate(files):
                if file["type"] == "file" and file["date"] > ignore_timeout:
                    continue
                if file["type"] == "file":  # old file to be moved to ignore dir
                    ftp.rename(file["name"], f"{XML_IGNORE_DIR}/{file['name']}")
                files[index] = None
            new_xml_files = [
                [i.group(), *i.groups()]  # filename, kdl order id, order date
                for i in (XML_FILENAME_REGEX.match(f["name"]) for f in files if f)
                if i
            ]

            # erase old and get new pdf files
            ftp.cwd(PDF_OUTPUT_DIR)
            files = []
            ftp.dir(files.append)
            files = parse_ftp_dir_listing(files, time_shift=time_shift_munites)
            for index, file in enumerate(files):
                if file["type"] == "file" and file["date"] > ignore_timeout:
                    continue
                if file["type"] == "file":  # old file to be moved to ignore dir
                    ftp.rename(file["name"], f"{PDF_IGNORE_DIR}/{file['name']}")
                files[index] = None
            new_pdf_files = [
                [i.group(), *i.groups()]  # filename, kdl order id, order date
                for i in (PDF_FILENAME_REGEX.match(f["name"]) for f in files if f)
                if i
            ]
        except ftplib.all_errors as e:
            logger.warning(f"KDL: FTP xml and pdf file listing retrieving error ({e}).")
            return

        # XML files processing
        ftp.cwd(XML_OUTPUT_DIR)
        for xml_filename, kdl_order_id, order_date in new_xml_files:
            try:
                data = io.BytesIO()
                ftp.retrbinary(f"RETR {xml_filename}", data.write)
                data.seek(0)
                xml_data = etree.parse(data, parser=get_safe_lxml_parser())
            except ftplib.all_errors as e:
                logger.warning(
                    f"KDL: Error was encountered while processing FTP connection ({xml_filename}, {e})."
                )
                continue  # totally ignore files, which can't be reached via ftp
            except etree.Error as e:
                logger.warning(
                    f"KDL: Invalid new XML file {xml_filename} found on remote FTP ({e})."
                )
                continue  # ignore non xml files located on remote ftp

            xml_kdl_order_id = xml_data.xpath("//root/Order/@OrderID")
            xml_kdl_order_id = xml_kdl_order_id and xml_kdl_order_id[0] or None
            xml_kdl_preorder_id = xml_data.xpath(
                "//root/Order/Patient/InsuranceCompany/text()"
            )
            xml_kdl_preorder_id = xml_kdl_preorder_id and xml_kdl_preorder_id[0] or None

            if xml_kdl_order_id is None or not xml_kdl_order_id == kdl_order_id:
                kdl_files_indexed_by_order_id["orphans"]["xml"].append(xml_filename)
            else:
                if kdl_order_id not in kdl_files_indexed_by_order_id["index"]:
                    kdl_files_indexed_by_order_id["index"][kdl_order_id] = {
                        "id": kdl_order_id,
                        "order_exists": False,
                        "files": [],
                    }
                kdl_files_indexed_by_order_id["index"][kdl_order_id]["files"].append(
                    {
                        "date": order_date,
                        "kdl_preorder_id": xml_kdl_preorder_id,
                        "xml": xml_filename,
                        "pdf": None,
                        "pdf_is_loaded": False,
                    }
                )

        # PDF files processing
        ftp.cwd(PDF_OUTPUT_DIR)
        for pdf_filename, kdl_order_id, order_date in new_pdf_files:
            kdl_order_entry = kdl_files_indexed_by_order_id["index"].get(
                kdl_order_id, {}
            )
            kdl_order_file_entry = {}
            for i in kdl_order_entry.get("files", []):
                if order_date == i["date"]:
                    kdl_order_file_entry = i
                    break
            kdl_preorder_id = kdl_order_file_entry.get("kdl_preorder_id")

            if not kdl_order_file_entry:
                kdl_files_indexed_by_order_id["orphans"]["pdf"].append(pdf_filename)
            else:
                kdl_order_file_entry["pdf"] = pdf_filename

            if not kdl_order_entry or not kdl_order_file_entry or not kdl_preorder_id:
                # temporary disable logging because of huge size of log file
                # logger.warning(
                #     f"KDL: Got PDF results from KDL with wrong Date: '{order_date}' or "
                #     f"OrderID: '{kdl_order_id}' or PreOrderID: '{kdl_preorder_id}' in "
                #     f"'{pdf_filename}' file, please check manually."
                # )
                continue

            order = (
                models.Order.objects.select_related("user")
                .only("user__sso_id")  # We don't need to fetch the whole order here
                .filter(external_lab_id=kdl_preorder_id)
                .first()
            )
            if order is None:
                logger.warning(
                    f"KDL: New PDF file found with the name {pdf_filename} but failed to "
                    f"find the Order with KDL #{kdl_preorder_id}, please check manually"
                )
                continue
            kdl_order_entry["order_exists"] = True

            pdf_filepath = os.path.join(settings.KDL_PDF_STORAGE_DIR, pdf_filename)
            try:
                with open(pdf_filepath, "wb+") as f:
                    ftp.retrbinary(f"RETR {pdf_filename}", f.write)
            except ftplib.all_errors as e:
                logger.warning(
                    f"KDL: New PDF file found with the name {pdf_filename} but failed to "
                    f"find the order with KDL #{kdl_preorder_id}, please check manually"
                )
                continue
            kdl_order_file_entry["pdf_is_loaded"] = True

            # update external order_id (kdl_order_id) value in order
            order.external_lab_order_id = kdl_order_id
            order.save(update_fields=["external_lab_order_id"])

            # create new order event and send file to imageset api

            events.order_result_downloaded_from_lab_event(
                order=order,
                user_id=order.user.pk,
                lab_name="KDL",
                filename=pdf_filename,
            )
            upload_pdf_to_imageset_api.delay(
                order_id=order.pk,
                user_id=order.user.pk,
                full_path=pdf_filepath,
                sso_id=order.user.sso_id,
            )

        kdl_files_to_be_deleted = []
        for value in kdl_files_indexed_by_order_id["index"].values():
            for file in value["files"]:
                if not (
                    file["kdl_preorder_id"] is None
                    or (
                        file["kdl_preorder_id"]
                        and file["pdf"]
                        and file["pdf_is_loaded"]
                        and value["order_exists"]
                    )
                ):
                    continue

                # mark as to be deleted files with empty BookingId or valid processed files
                kdl_files_to_be_deleted.append(file)

        ftp.cwd(XML_OUTPUT_DIR)
        # erase xml invalid files
        for xml_filename in kdl_files_indexed_by_order_id["orphans"]["xml"]:
            try:
                ftp.delete(xml_filename)
            except ftplib.all_errors as e:
                pass  # do nothing on error while waste clearing

        # erase xml unsuitable or processed files
        for value in kdl_files_to_be_deleted:
            try:
                ftp.delete(value["xml"])
            except ftplib.all_errors as e:
                pass  # do nothing on error while waste clearing

        ftp.cwd(PDF_OUTPUT_DIR)
        # erase pdf unsuitable or processed files
        for value in kdl_files_to_be_deleted:
            if not value["pdf"]:  # if xml file exists and pdf is not
                continue
            try:
                ftp.delete(value["pdf"])
            except ftplib.all_errors as e:
                pass  # do nothing on error while waste clearing

        # # generate slack report
        # # ---------------------
        # slack_block = []

        # # incorrect xml files
        # if kdl_files_indexed_by_order_id["orphans"]["xml"]:
        #     slack_block.append(
        #         f"Удалены некорректные файлы xml с пустым OrderID:\n    %s"
        #         % "\n    ".join(kdl_files_indexed_by_order_id[None]["xml"])
        #     )

        # # empty BookingId files
        # files = [
        #     (i["xml"], i["pdf"])
        #     for i in kdl_files_to_be_deleted
        #     if not i["kdl_preorder_id"]
        # ]
        # if files:
        #     files = filter(bool, reduce(tuple.__add__, files, ()))
        #     slack_block.append(
        #         f"Удалены файлы с пустым BookingId:\n    %s" % "\n    ".join(files)
        #     )

        # # standalone xml files
        # files = [
        #     j["xml"]
        #     for i in kdl_files_indexed_by_order_id["index"].values()
        #     for j in i["files"]
        #     if j["kdl_preorder_id"] and not j["pdf"]
        # ]
        # if files:
        #     slack_block.append(
        #         f"XML файлы без сзязанных PDF файлов:\n    %s" % "\n    ".join(files)
        #     )

        # # standalone pdf files
        # if kdl_files_indexed_by_order_id["orphans"]["pdf"]:
        #     slack_block.append(
        #         f"PDF файлы без сзязанных xml файлов:\n    %s"
        #         % "\n    ".join(kdl_files_indexed_by_order_id["orphans"]["pdf"])
        #     )

        # # xml and pdf couples without related Order in DB
        # files = [
        #     f'{j["xml"]} ({j["pdf"]})'
        #     for i in kdl_files_indexed_by_order_id["index"].values()
        #     for j in i["files"]
        #     if j["kdl_preorder_id"] and j["pdf"] and not i["order_exists"]
        # ]
        # if files:
        #     slack_block.append(
        #         f"XML (PDF) файлы без соответствующего заказа в БД:\n    %s"
        #         % "\n    ".join(files)
        #     )

        # # xml and pdf couples with errors while downloading files
        # files = [
        #     f'{j["xml"]} ({j["pdf"]})'
        #     for i in kdl_files_indexed_by_order_id["index"].values()
        #     for j in i["files"]
        #     if i["order_exists"]
        #     and j["pdf"]
        #     and j["kdl_preorder_id"]
        #     and not j["pdf_is_loaded"]
        # ]
        # if files:
        #     slack_block.append(
        #         f"Корректные файлы, не загруженные из-за ошибок FTP:\n    %s"
        #         % "\n    ".join(files)
        #     )

        # if settings.SLACK_SYNC_RESULTS and slack_block:
        #     # send slack report chunked by max limit size (in slack - 3001 characters)
        #     blocks = [
        #         {
        #             "type": "section",
        #             "text": {
        #                 "type": "plain_text",
        #                 "text": "Результат синхронизации KDL по FTP.",
        #                 "emoji": True,
        #             },
        #         },
        #         {"type": "divider"},
        #         {
        #             "type": "section",
        #             "text": {
        #                 "type": "mrkdwn",
        #                 "text": "",
        #             },
        #         },
        #     ]

        #     lines = "\n\n".join(slack_block).split("\n")
        #     line_last = len(lines) - 1

        #     chunk, chunk_first, chunk_size, chunk_size_max = [], True, 0, 1024 * 2.5
        #     for index, line in enumerate(lines):
        #         chunk.append(line)
        #         chunk_size += len(line)
        #         if chunk_size < chunk_size_max and index < line_last:
        #             continue

        #         if chunk_first:
        #             blocks[-1]["text"]["text"] = (
        #                 f"```{timezone.now()} {settings.SLACK_ENVIRONMENT}"
        #                 f"\n\n{chr(10).join(chunk)}```"
        #             )
        #             payload = blocks
        #         else:
        #             blocks[-1]["text"]["text"] = f"```{(chr(10)).join(chunk)}```"
        #             payload = blocks[-1:]

        #         slack_send_message_task.delay({"blocks": payload})
        #         chunk, chunk_size, chunk_first = [], 0, False
