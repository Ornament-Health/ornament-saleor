import enum
from itertools import chain
from dataclasses import dataclass
from datetime import datetime
import asyncio
import secrets
import string

import aiohttp
from asgiref.sync import async_to_sync
from saleor.attribute.models.base import AttributeValue

from saleor.attribute.models.product import AssignedProductAttributeValue

# TODO::ornament move to settings
thesaurus_api_url_1_0 = "https://api.ornament.health/thesaurus-api/public/v1.0"
thesaurus_api_url_1_1 = "https://api.ornament.health/thesaurus-api/public/v1.1"


@dataclass
class MedicalData:
    biomarker_ids: list[int]
    medical_exams_ids: list[int]


@async_to_sync
async def fetch_medical_data() -> MedicalData:
    async with aiohttp.ClientSession() as session:
        requests = [
            session.post(
                f"{thesaurus_api_url_1_1}/biomarkers",
                json={"lang": "RU"},
            ),
            session.post(
                f"{thesaurus_api_url_1_0}/medical-exams",
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


# TODO::ornament move to common vendors utils
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
        # TODO::ornament move to settings
        "version": "2.24.3",
    }


def form_description(name: str, description: str) -> dict:
    description_dict = {
        "time": get_current_timestamp(),
        "blocks": [form_description_block(name, "header")],
        # TODO::ornament move to settings
        "version": "2.24.3",
    }

    if description:
        blocks = description.split("\n")

        for block in blocks:
            description_dict["blocks"].append(
                form_description_block(block, "paragraph")
            )

    return description_dict


class KdlDurationUnitEnum(enum.Enum):
    HOUR = 1
    DAY = 2


class AttributeUtils:
    attrubutes_ids = {
        "color": 1,
        "featured": 2,
        "featured-collection": 3,
        "icon": 4,
        "kdl-biomaterials": 5,
        "kdl-preparation": 6,
        "kdl-max_duration": 7,
        "kdl-duration_unit": 8,
        "sex": 9,
        "age-from": 10,
        "age-to": 11,
        "biomarkers": 12,
        "medical_exams": 13,
    }

    @staticmethod
    def add_biomaterial_attribute_data(
        product_id: int, biomaterial: str
    ) -> AssignedProductAttributeValue:
        attribute_id = AttributeUtils.attrubutes_ids["kdl-biomaterials"]
        name = biomaterial.replace("\n", ", ")
        slug = f"{product_id}_{attribute_id}"

        biomaterial_attribute_value = AttributeValue(
            name=name,
            attribute_id=attribute_id,
            slug=slug,
            plain_text=name,
            sort_order=attribute_id,
        )

        biomaterial_attribute_value.save()

        return AssignedProductAttributeValue(
            value_id=biomaterial_attribute_value.pk,
            product_id=product_id,
        )

    @staticmethod
    def add_preparation_attribute_data(
        product_id: int, preparation: str
    ) -> AssignedProductAttributeValue:
        attribute_id = AttributeUtils.attrubutes_ids["kdl-preparation"]
        name = preparation[:20] + "..."
        rich_text = form_rich_text(preparation)
        slug = f"{product_id}_{attribute_id}"

        preparation_attribute_value = AttributeValue(
            name=name,
            attribute_id=attribute_id,
            slug=slug,
            rich_text=rich_text,
            sort_order=attribute_id,
        )

        preparation_attribute_value.save()

        return AssignedProductAttributeValue(
            value_id=preparation_attribute_value.pk,
            product_id=product_id,
        )

    @staticmethod
    def add_numeric_attribute_data(
        product_id: int, attribute_data_value: int, attribute_id: int
    ) -> AssignedProductAttributeValue:
        slug = f"{product_id}_{attribute_id}"

        attribute_value = AttributeValue(
            name=attribute_data_value,
            attribute_id=attribute_id,
            slug=slug,
            sort_order=attribute_id,
        )

        attribute_value.save()

        return AssignedProductAttributeValue(
            value_id=attribute_value.pk,
            product_id=product_id,
        )

    @staticmethod
    def add_medical_attributes_data(
        product_id: int,
        medical_data_ids: list[int],
        attribute_values: dict[int, int],
    ) -> list[AssignedProductAttributeValue]:
        if not medical_data_ids:
            return []

        return [
            AssignedProductAttributeValue(
                value_id=attribute_values.get(b),
                product_id=product_id,
            )
            for b in set(medical_data_ids)
        ]
