import json
import logging
import os
from typing import Optional

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from saleor.attribute.models.base import AttributeValue
from saleor.attribute.models.product import (
    AssignedProductAttribute,
    AssignedProductAttributeValue,
)
from saleor.ornament.vendors.kdl.management.utils import (
    AttributeUtils,
    fetch_medical_data,
)


logger = logging.getLogger(__name__)

POPULATE_DB_PATH = os.path.join(
    settings.PROJECT_ROOT, "saleor", "ornament", "vendors", "kdl", "sql"
)


class Command(BaseCommand):
    help = "Recreate all products attributes"

    def get_attributes_by_key(
        self, lab_meta: dict, key: str, product_id: int, ornament: bool = False
    ) -> Optional[dict]:
        node = "ornament" if ornament else "lab"

        if attr_by_id := (lab_meta.get("details", {}).get(node, {}).get(key)):
            return {"product_id": product_id, "value": attr_by_id}

        return None

    def add_sex_attribute_data(
        self,
        attribute: dict,
        attribute_id: int,
        sex_attribute_values: dict[str, AttributeValue],
    ) -> AssignedProductAttributeValue:
        product_id = attribute["product_id"]

        assignedproductattribute = AssignedProductAttribute(
            product_id=product_id,
            assignment_id=attribute_id,
        )

        assignedproductattribute.save()

        sex_attribute_value = sex_attribute_values.get(attribute["value"])

        if not sex_attribute_value:
            raise CommandError(
                f"""Can't find sex attribute for value {attribute["value"]}"""
            )

        return AssignedProductAttributeValue(
            assignment_id=assignedproductattribute.pk,
            value_id=sex_attribute_value.pk,
            product_id=product_id,
        )

    def handle(self, *args, **options):
        path = os.path.join(
            POPULATE_DB_PATH, "source_data_json", "product_product.json"
        )

        medical_data = fetch_medical_data()

        biomarkers_attribute_values = [
            AttributeValue(
                name=b_id,
                attribute_id=AttributeUtils.attrubutes_ids["biomarkers"],
                slug=b_id,
                sort_order=b_id,
            )
            for b_id in medical_data.biomarker_ids
        ]
        medical_exams_attribute_values = [
            AttributeValue(
                name=m_id,
                attribute_id=AttributeUtils.attrubutes_ids["medical_exams"],
                slug=m_id,
                sort_order=m_id,
            )
            for m_id in medical_data.medical_exams_ids
        ]
        inserted_biomarkers_attribute_values = AttributeValue.objects.bulk_create(
            biomarkers_attribute_values
        )
        inserted_medical_exams_attribute_values = AttributeValue.objects.bulk_create(
            medical_exams_attribute_values
        )
        biomarkers_attribute_values_ids: dict[int, int] = {
            int(b.name): b.pk for b in inserted_biomarkers_attribute_values
        }
        medical_exams_attribute_values_ids: dict[int, int] = {
            int(m.name): m.pk for m in inserted_medical_exams_attribute_values
        }

        with open(path, "r") as data:
            rows = json.load(data)

            assigned_product_attribute_values = []

            sex_attribute_values = AttributeValue.objects.filter(name__in=["M", "F"])
            sex_attribute_values = {v.name: v for v in sex_attribute_values}

            for r in rows:
                id = r["id"]
                lab_meta = json.loads(r["meta"])

                biomaterial = self.get_attributes_by_key(lab_meta, "biomaterials", id)
                preparation = self.get_attributes_by_key(lab_meta, "preparation", id)
                max_duration = self.get_attributes_by_key(lab_meta, "MaxDuration", id)
                duration_unit = self.get_attributes_by_key(lab_meta, "DurationUnit", id)
                age_from = self.get_attributes_by_key(
                    lab_meta, "ageFrom", id, ornament=True
                )
                age_to = self.get_attributes_by_key(
                    lab_meta, "ageTo", id, ornament=True
                )
                sex = self.get_attributes_by_key(lab_meta, "sex", id, ornament=True)
                biomarkers = self.get_attributes_by_key(
                    lab_meta, "biomarkers", id, ornament=True
                )
                medical_exams = self.get_attributes_by_key(
                    lab_meta,
                    "medical_exams",
                    id,
                    ornament=True,
                )

                if biomaterial:
                    assigned_product_attribute_values.append(
                        AttributeUtils.add_biomaterial_attribute_data(
                            biomaterial["product_id"], biomaterial["value"]
                        )
                    )

                if preparation:
                    assigned_product_attribute_values.append(
                        AttributeUtils.add_preparation_attribute_data(
                            preparation["product_id"], preparation["value"]
                        )
                    )

                if max_duration:
                    assigned_product_attribute_values.append(
                        AttributeUtils.add_numeric_attribute_data(
                            max_duration["product_id"],
                            max_duration["value"],
                            AttributeUtils.attrubutes_ids["kdl-max_duration"],
                        )
                    )
                if duration_unit:
                    assigned_product_attribute_values.append(
                        AttributeUtils.add_numeric_attribute_data(
                            duration_unit["product_id"],
                            duration_unit["value"],
                            AttributeUtils.attrubutes_ids["kdl-duration_unit"],
                        )
                    )
                if age_from:
                    assigned_product_attribute_values.append(
                        AttributeUtils.add_numeric_attribute_data(
                            age_from["product_id"],
                            age_from["value"],
                            AttributeUtils.attrubutes_ids["age-from"],
                        )
                    )
                if age_to:
                    assigned_product_attribute_values.append(
                        AttributeUtils.add_numeric_attribute_data(
                            age_to["product_id"],
                            age_to["value"],
                            AttributeUtils.attrubutes_ids["age-to"],
                        )
                    )
                if sex:
                    assigned_product_attribute_values.append(
                        self.add_sex_attribute_data(
                            sex,
                            AttributeUtils.attrubutes_ids["sex"],
                            sex_attribute_values,
                        )
                    )
                if biomarkers:
                    assigned_product_attribute_values += (
                        AttributeUtils.add_medical_attributes_data(
                            biomarkers["product_id"],
                            biomarkers["value"],
                            AttributeUtils.attrubutes_ids["biomarkers"],
                            biomarkers_attribute_values_ids,
                        )
                    )
                if medical_exams:
                    assigned_product_attribute_values += (
                        AttributeUtils.add_medical_attributes_data(
                            medical_exams["product_id"],
                            medical_exams["value"],
                            AttributeUtils.attrubutes_ids["medical_exams"],
                            medical_exams_attribute_values_ids,
                        )
                    )

            AssignedProductAttributeValue.objects.bulk_create(
                assigned_product_attribute_values
            )

            return
