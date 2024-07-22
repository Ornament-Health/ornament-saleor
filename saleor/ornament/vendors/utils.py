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
from django.core.cache import cache
from django.forms import model_to_dict

from saleor.graphql.ornament.vendors.types import VendorDealType
from saleor.order.fetch import OrderLineInfo
from saleor.order.models import Order
from saleor.ornament.vendors.kdl import tasks as kdl_tasks
from saleor.account.models import User, Address
from saleor.ornament.utils.slack import Slack
from saleor.ornament.vendors.dardoc.utils import (
    get_dardoc_address_id,
    get_dardoc_patient_id,
    get_or_create_dardoc_user,
)
from saleor.ornament.vendors.models import Vendor
from saleor.product.models import ProductVariant

logger = logging.getLogger(__name__)

DEFAULT_DESCRIPTION_VERSION = "2.24.3"


@dataclass
class MedicalData:
    biomarker_ids: list[int]
    medical_exams_ids: list[int]


def form_slack_error_message(error_text: str) -> dict:
    return {
        "attachments": [
            {
                "color": "#ff0000",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": error_text,
                        },
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": (
                                    f"Server *{settings.SLACK_ENVIRONMENT}*, "
                                    f"Region *{settings.SLACK_REGION}*"
                                ),
                            }
                        ],
                    },
                ],
            }
        ]
    }


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


def get_vendor_deal_type(vendor_name: str) -> Optional[VendorDealType]:
    key = f"vendor_deal_type:{vendor_name}"
    cached = cache.get(key)
    ttl = settings.VENDOR_DEAL_TYPE_CACHE_TTL

    if cached:
        if cached == "null":
            return None
        return VendorDealType(**cached)

    vendor = Vendor.objects.filter(name=vendor_name).first()

    if not vendor or not vendor.deal_type:
        cache.set(key, "null", ttl)
        return None

    deal_type_dict = model_to_dict(vendor.deal_type, exclude="id")
    cache.set(key, deal_type_dict, ttl)

    return VendorDealType(**deal_type_dict)


def check_deal_types_valid(deal_types: list[Optional[VendorDealType]]) -> bool:
    if not deal_types:
        return False

    return all(d.__dict__ == deal_types[0].__dict__ for d in deal_types if d)


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


def apply_dardoc_vendor_address_augmentation(address_data: dict) -> dict:
    if not address_data.get("street_address_1"):
        address_data["street_address_1"] = settings.DEFAULT_DARDOC_STREET_ADDRESS
    if not address_data.get("country_area"):
        address_data["country_area"] = settings.DEFAULT_DARDOC_COUNTRY_AREA
    return address_data


def apply_dardoc_checkout_address_update(
    user: User, shipping_address: dict, shipping_address_instance: Address
) -> None:
    dardoc_user_id = get_or_create_dardoc_user(user, shipping_address_instance)

    if not dardoc_user_id:
        error_message = (
            f"Cant get or create DarDoc user! Check service logs \n"
            f"User sso_id: {user.sso_id}"
        )
        slack_error_text = f"<!channel> \n" f":bangbang: {error_message}"
        slack_message = form_slack_error_message(slack_error_text)
        logger.error(error_message)
        Slack.send_message_task.delay(slack_message)
        return

    dardoc_patient_id = get_dardoc_patient_id(user, dardoc_user_id)

    dardoc_address_id = get_dardoc_address_id(
        user, dardoc_user_id, shipping_address_instance
    )

    if not dardoc_address_id:
        error_message = (
            f"Cant get or create DarDoc address! Check service logs \n"
            f"User sso_id: {user.sso_id}"
        )
        slack_error_text = f"<!channel> \n" f":bangbang: {error_message}"
        slack_message = form_slack_error_message(slack_error_text)
        logger.error(f"{error_message}; Shipping address: {shipping_address}")
        Slack.send_message_task.delay(slack_message)
        return

    return


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
        vendor_logic = vendor_order_logic_map.get(vendor_name.lower())
        if vendor_logic:
            vendor_logic(order)

    return


def apply_vendors_notification(
    order: Order, order_lines_info: list[OrderLineInfo]
) -> None:
    vendors = set([l.variant.name for l in order_lines_info if l.variant])
    vendor_name = get_vendor_name(vendors)

    if vendor_name:
        vendor_notification = vendor_order_notification_map.get(vendor_name.lower())
        if vendor_notification:
            vendor_notification(order)

    return


def apply_vendor_address_augmentation(
    variants: list[ProductVariant], address_data: dict
) -> dict:
    vendors = set([v.name for v in variants])
    vendor_name = get_vendor_name(vendors)

    if vendor_name:
        vendor_address_augmentation = vendor_address_augmentation_map.get(
            vendor_name.lower()
        )
        if vendor_address_augmentation:
            return vendor_address_augmentation(address_data)

    return address_data


def apply_vendor_checkout_address_update(
    variants: list[ProductVariant],
    user: User,
    shipping_address: dict,
    shipping_address_instance: Address,
) -> None:
    vendors = set([v.name for v in variants])
    vendor_name = get_vendor_name(vendors)

    if vendor_name:
        vendor_checkout_address_update = vendor_checkout_address_update_map.get(
            vendor_name.lower()
        )
        if vendor_checkout_address_update:
            return vendor_checkout_address_update(
                user, shipping_address, shipping_address_instance
            )

    return


vendor_order_logic_map = {"kdl": apply_kdl_order_logic}
vendor_order_notification_map = {"kdl": apply_kdl_order_notification}
vendor_address_augmentation_map = {
    "kdl": apply_kdl_vendor_address_augmentation,
    "dardoc": apply_dardoc_vendor_address_augmentation,
}
vendor_checkout_address_update_map = {"dardoc": apply_dardoc_checkout_address_update}
