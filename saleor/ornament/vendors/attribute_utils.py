import json
import logging

from django.conf import settings
from django.core.management.base import CommandError

from saleor.attribute.models.base import AttributeValue
from saleor.attribute.models.product import AssignedProductAttributeValue
from saleor.ornament.vendors.utils import form_rich_text

logger = logging.getLogger(__name__)


class AttributeUtils:
    attribute_ids = json.loads(settings.ATTRIBUTE_IDS)

    @staticmethod
    def add_biomaterial_attribute_data(
        product_id: int, biomaterial: str
    ) -> AssignedProductAttributeValue:
        attribute_id = AttributeUtils.attribute_ids["kdl-biomaterials"]
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
        attribute_id = AttributeUtils.attribute_ids["kdl-preparation"]
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

        assigned_product_attribute_values = []

        for b in set(medical_data_ids):
            if attribute_values.get(b):
                assigned_product_attribute_values.append(
                    AssignedProductAttributeValue(
                        value_id=attribute_values.get(b),
                        product_id=product_id,
                    )
                )
            else:
                logger.error(
                    f"No medical data (biomarkers or medical_exams) found for: {b}"
                )

        return assigned_product_attribute_values

    @staticmethod
    def add_color_attribute_data(
        product_id: int,
        color_slug: str,
        color_attribute_values: dict[str, AttributeValue],
    ) -> AssignedProductAttributeValue:
        color_attribute_value = color_attribute_values.get(color_slug)

        if not color_attribute_value:
            raise CommandError(
                f"""Can't find color attribute value for slug {color_slug}"""
            )

        return AssignedProductAttributeValue(
            value_id=color_attribute_value.pk,
            product_id=product_id,
        )
