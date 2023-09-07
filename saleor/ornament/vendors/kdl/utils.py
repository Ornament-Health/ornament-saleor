import json

from ftplib import FTP
from lxml import etree
from typing import List, Optional
from datetime import datetime, timedelta
from ftpparser import FTPParser

from django.conf import settings
from django.utils import timezone

from saleor.account import Sex
from saleor.order.models import Order

# TODO[ornament]: VoucherScope, KDLDiscount
# from saleor.discount import VoucherScope
# from saleor.discount.models import KDLDiscount


def add_sub_element(
    parent: etree.Element, name: str, value: str = None
) -> etree.SubElement:
    sub_element = etree.SubElement(parent, name)
    if value is not None:
        sub_element.text = value
    return sub_element


def make_order_xml_tree(order: Order) -> etree.Element:
    now = timezone.now().replace(microsecond=0)
    root_element = etree.Element("root")

    header_element = add_sub_element(root_element, "Header")
    add_sub_element(header_element, "Version", "4")
    add_sub_element(header_element, "FileDate", now.date().isoformat())
    add_sub_element(header_element, "FileTime", now.time().isoformat())
    add_sub_element(header_element, "GenTime", "0")
    add_sub_element(header_element, "FileType", "Order")
    add_sub_element(header_element, "LaboratoryID", "kdltest_united")
    add_sub_element(header_element, "LaboratoryName", "КДЛТЕСТ")
    add_sub_element(header_element, "ClinicID", settings.KDL_CLINIC_ID)
    add_sub_element(header_element, "ClinicName", settings.KDL_CLINIC_NAME)
    add_sub_element(header_element, "Direction", "FromClinic")

    order_element = add_sub_element(root_element, "Order")
    add_sub_element(order_element, "OrderID", str(order.pk))

    patient_element = add_sub_element(root_element, "Patient")
    full_name = order.shipping_address.last_name
    add_sub_element(patient_element, "LastName", full_name)
    add_sub_element(patient_element, "FirstMiddleName", full_name)
    date_of_birth = order.shipping_address.date_of_birth
    add_sub_element(
        patient_element,
        "DOB",
        date_of_birth.isoformat() if date_of_birth else "0000-00-00",
    )
    add_sub_element(
        patient_element, "Sex", order.shipping_address.sex or Sex.UNSPECIFIED
    )
    address = ", ".join(
        [
            order.shipping_address.city,
            order.shipping_address.country_area,
            order.shipping_address.street_address_1,
        ]
    )
    add_sub_element(patient_element, "HomeAddress", address)
    add_sub_element(patient_element, "Email", order.get_customer_email())
    add_sub_element(patient_element, "PhoneNumber", str(order.shipping_address.phone))

    tests_element = add_sub_element(root_element, "Tests")
    for line in order.lines.all():
        add_sub_element(tests_element, "TestShortName", line.product_sku)

    # TODO: temporary solution to add service SKUs which are required by KDL to present
    #  in each order. The whole logic may be refactored later so that these SKUs will
    #  be added during the order creation.
    for _, sku in settings.KDL_MANDATORY_ORDER_SKU_LIST:
        add_sub_element(tests_element, "TestShortName", sku)

    return root_element


def xml_tree_as_bytes(xml_data: etree.Element) -> bytes:
    return etree.tostring(
        xml_data, xml_declaration=True, encoding="UTF-8", pretty_print=True
    )


def make_preorder_data(order: Order) -> dict:
    if not order.shipping_address or not len(order.lines.all()):
        return None

    now = timezone.now().replace(microsecond=0)
    full_name = order.shipping_address.last_name
    date_of_birth = order.shipping_address.date_of_birth
    phone = str(order.shipping_address.phone).replace("+7", "", 1)
    sex = order.shipping_address.sex or Sex.UNSPECIFIED

    laboratory_id = settings.KDL_LABORATORY_ID
    laboratory_name = settings.KDL_LABORATORY_NAME
    promocode = order.voucher and order.voucher.name
    kdl_discount = KDLDiscount.get_for_order(order)
    if kdl_discount:
        clinic_id = kdl_discount.clinic_id
        doctor_id = kdl_discount.doctor_id
        promocode = kdl_discount.discount_title
        laboratory_id = kdl_discount.laboratory_id
        laboratory_name = kdl_discount.laboratory_name
    elif order.voucher is None or order.voucher.scope == VoucherScope.RETAIL:
        clinic_id = settings.KDL_CLINIC_NOVOUCHER_ID
        doctor_id = settings.KDL_DOCTOR_NOVOUCHER_ID
    else:
        clinic_id = settings.KDL_CLINIC_ID
        doctor_id = ""

    mandatory_order_sku_list = KDLDiscount.get_mandatory_order_sku_list(kdl_discount)
    home_address = ", ".join(
        [order.shipping_address.city, order.shipping_address.street_address_1]
    )
    try:
        customer_note = json.loads(order.customer_note)
    except json.JSONDecodeError:
        customer_note = {}
    patient_note = customer_note.get("note", "")
    preferred_date = customer_note.get("date")
    preferred_time = customer_note.get("time")
    preferred_time_text = ""
    if preferred_date and preferred_time:
        patient_note = f"{preferred_date} {preferred_time} {patient_note}".strip()
        preferred_time_text = (
            f"Желаемое время визита к пациенту: {preferred_date}, {preferred_time}"
        )
    if promocode:
        patient_note = f'Промокод: "{promocode}", {patient_note}'
    tests = [{"TestShortName": line.product_sku} for line in order.lines.all()]
    tests.extend([{"TestShortName": sku} for _, sku in mandatory_order_sku_list])
    return {
        "Header": {
            "ClinicID": clinic_id,
            "ClinicName": settings.KDL_CLINIC_NAME,
            "FileDate": now.date().isoformat(),
            "FileTime": now.time().isoformat(),
            "FileType": "PreOrder",
            "LaboratoryID": laboratory_id,
            "LaboratoryName": laboratory_name,
            "Direction": "FromClinic",
        },
        "Order": {
            "OrderID": 0,
            "OrderComment": f"ОРНАМЕНТ {patient_note}",
            "Doctor": doctor_id,
            "TestPassingType": 2,
            "Patient": {
                "LastName": full_name,
                "FirstMiddleName": full_name,
                "Sex": sex,
                # TODO: remove this stub when front-end implements real DOB sending
                "DOB": date_of_birth.isoformat() if date_of_birth else "1970-01-01",
                "Email": order.get_customer_email(),
                "PhoneNumber": phone,
                "HomeAddress": home_address,
                "Address": {
                    "District": order.shipping_address.city,
                    "Country": order.shipping_address.city,
                    "Street": order.shipping_address.street_address_1,
                    "Comment": preferred_time_text,
                },
            },
            "Tests": {"Test": tests},
        },
    }


def detect_ftp_timezone_shift(ftp: FTP) -> int:
    # Creates dir in root dir to check current time of the server side
    parser, dirname = FTPParser(), "timeshiftcheck"

    ftp.cwd("/")
    root = ftp.nlst()
    if dirname in root:
        ftp.rmd(dirname)

    files = []

    ftp.mkd(dirname)
    ftp.dir(files.append)
    ftp.rmd(dirname)

    ftptime = next((i for i in parser.parse(files) if i[0] == dirname), None)
    ftptime = (
        timezone.make_aware(datetime.fromtimestamp(ftptime[2])).astimezone(timezone.utc)
        if ftptime
        else timezone.now()
    )
    nowtime = timezone.now()

    # accuracy is half of an hour
    return round((nowtime - ftptime).total_seconds() / 60 / 30) * 30


def parse_ftp_dir_listing(
    items: List[str], time_shift: Optional[int] = 0
) -> List[dict]:
    result, now = [], timezone.now()

    parser = FTPParser()
    files = parser.parse(items)
    for file in files:
        date = now
        if file[2]:
            date = timezone.make_aware(datetime.fromtimestamp(file[2])).astimezone(
                timezone.utc
            ) + timedelta(minutes=time_shift)

        result.append(
            {
                "name": file[0],
                "size": file[1],
                "type": "file" if not file[3] and file[4] else "dir",
                "date": date,
            }
        )

    return result
