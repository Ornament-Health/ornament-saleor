import asyncio
from dataclasses import dataclass
from datetime import datetime
from itertools import chain
import logging
import secrets
import string
from typing import Optional

import aiohttp
from asgiref.sync import async_to_sync
from django.conf import settings

from saleor.order.fetch import OrderLineInfo
from saleor.order.models import Order
from saleor.ornament.vendors.kdl import tasks as kdl_tasks
from saleor.ornament.vendors.models import Vendor
from saleor.product.models import ProductVariant

logger = logging.getLogger(__name__)

DEFAULT_DESCRIPTION_VERSION = "2.24.3"


@dataclass
class MedicalData:
    biomarker_ids: list[int]
    medical_exams_ids: list[int]


@async_to_sync
async def fetch_medical_data() -> MedicalData:
    async with aiohttp.ClientSession() as session:
        requests = [
            session.post(
                f"{settings.THESAURUS_API_URL_1_1}/biomarkers",
                json={"lang": "RU"},
            ),
            session.post(
                f"{settings.THESAURUS_API_URL_1_0}/medical-exams",
                json={},
            ),
        ]
        result = await asyncio.gather(*requests)

        biomarkers_response, medical_exams_response = result

        biomarkers = await biomarkers_response.json()
        medical_exams = await medical_exams_response.json()

        biomarker_ids = [b["id"] for b in biomarkers["biomarkers"]]
        medical_exams_ids = [
            exam_object["examTypeObjectId"]
            for exam_object in chain.from_iterable(
                [exam["objects"] for exam in medical_exams["exams"]]
            )
        ]

        return MedicalData(
            biomarker_ids=biomarker_ids, medical_exams_ids=medical_exams_ids
        )


def random_string(size) -> str:
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return "".join(secrets.choice(letters) for _ in range(size))


def get_current_timestamp() -> float:
    now = datetime.now()
    return now.timestamp()


def form_description_block(text: str, block_type: str) -> dict:
    return {
        "id": random_string(10),
        "data": {"text": text},
        "type": block_type,
    }


def form_rich_text(text: str) -> dict:
    return {
        "time": get_current_timestamp(),
        "blocks": [form_description_block(text, "paragraph")],
        "version": DEFAULT_DESCRIPTION_VERSION,
    }


def form_description(name: str, description: Optional[str]) -> dict:
    description_dict = {
        "time": get_current_timestamp(),
        "blocks": [form_description_block(name, "header")],
        "version": DEFAULT_DESCRIPTION_VERSION,
    }

    if description:
        blocks = description.split("\n")

        for block in blocks:
            description_dict["blocks"].append(
                form_description_block(block, "paragraph")
            )

    return description_dict


def apply_kdl_order_logic(order: Order):
    kdl_tasks.place_preorder_via_wsdl.delay(order_id=order.pk)


def apply_kdl_order_notification(order: Order):
    kdl_tasks.send_order_confirmation.delay(order_id=order.pk)


def apply_kdl_vendor_address_augmentation(address_data: dict) -> dict:
    address_data["postal_code"] = settings.DEFAULT_KDL_POSTAL_CODE
    address_data["country_area"] = settings.DEFAULT_KDL_COUNTRY_AREA
    return address_data


def get_vendor_name(vendors: set[str]) -> Optional[str]:
    if len(vendors) < 1:
        logger.error("get_vendor_name: no valid Vendor in order lines")
        return None

    if len(vendors) > 1:
        logger.error("get_vendor_name: found more then 1 valid Vendors in order lines")
        return None

    vendor_name = vendors.pop()

    if Vendor.objects.filter(name=vendor_name).exists():
        return vendor_name

    return None


def apply_vendors_logic(order: Order, order_lines_info: list[OrderLineInfo]) -> None:
    vendors = set([l.variant.name for l in order_lines_info if l.variant])
    vendor_name = get_vendor_name(vendors)

    if vendor_name:
        vendor_logic = vendor_order_logic_map.get(vendor_name)
        if vendor_logic:
            vendor_logic(order)

    return


def apply_vendors_notification(
    order: Order, order_lines_info: list[OrderLineInfo]
) -> None:
    vendors = set([l.variant.name for l in order_lines_info if l.variant])
    vendor_name = get_vendor_name(vendors)

    if vendor_name:
        vendor_notification = vendor_order_notification_map.get(vendor_name)
        if vendor_notification:
            vendor_notification(order)

    return


def apply_vendor_address_augmentation(
    variants: list[ProductVariant], address_data: dict
) -> dict:
    vendors = set([v.name for v in variants])
    vendor_name = get_vendor_name(vendors)

    if vendor_name:
        vendor_address_augmentation = vendor_address_augmentation_map.get(vendor_name)
        if vendor_address_augmentation:
            return vendor_address_augmentation(address_data)

    return address_data


vendor_order_logic_map = {"KDL": apply_kdl_order_logic}
vendor_order_notification_map = {"KDL": apply_kdl_order_notification}
vendor_address_augmentation_map = {"KDL": apply_kdl_vendor_address_augmentation}
