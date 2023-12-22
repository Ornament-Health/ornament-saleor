from datetime import datetime
import os
import re
from itertools import chain

from django.core.management.base import BaseCommand, CommandError
from slugify import slugify
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.utils import exceptions as openpyxl_exceptions

from saleor.attribute.models.base import AttributeValue
from saleor.attribute.models.product import (
    AssignedProductAttribute,
    AssignedProductAttributeValue,
)
from saleor.ornament.vendors.kdl.management.utils import (
    AttributeUtils,
    fetch_medical_data,
    form_description,
    form_rich_text,
)
from saleor.product.models import (
    Product,
    ProductVariant,
    ProductChannelListing,
    CollectionProduct,
    Category,
    Collection,
)
from saleor.channel.models import Channel


class Command(BaseCommand):
    help = "Import/Update KDL products with XLSX file"
    known_header_rows = [
        "SKU",
        "Наименование теста (KDL)",
        "Категория",
        "Подготовка к исследованию",
        "Описание",
        "Срок",
        "Биоматериал",
        "Биомаркеры",
        "medical_exam_type_object",
        "is popular",
        "is hidden",
    ]

    def add_arguments(self, parser):
        parser.add_argument("filename", help="Path to XLSX file with target data")

    def check_kdl_sheet_header_cols(self, sheet: Worksheet) -> None:
        sheet_header_cols: set = set(
            [s for s in sheet.iter_rows(min_row=1, max_row=1, values_only=True)][0]
        )

        if set(self.known_header_rows).difference(sheet_header_cols):
            raise CommandError(
                f"Sheet header does not contain all known columns: {self.known_header_rows}"
            )

    def get_medical_data_ids(self, col_data: str, ids: list[int]) -> list[int]:
        data_strings = col_data.split("\n")

        try:
            found_ids = chain.from_iterable(
                [re.findall(r"\d+", b.split("-")[-1]) for b in data_strings if b]
            )
            return [id for id in found_ids if int(id) in ids]
        except (IndexError, ValueError):
            raise CommandError(f"Can not parse medical data column: {col_data}")

    def handle(self, *args, **options):
        filename = options.get("filename")

        if not filename or not os.path.isfile(filename):
            raise CommandError(f'Source file "{filename}" does not exist.')

        try:
            wb = load_workbook(filename)
        except openpyxl_exceptions.InvalidFileException:
            raise CommandError(
                f"openpyxl does not support the old .xls file format, please use .xlsx file format."
            )

        sheet = wb["KDL-import"]

        self.check_kdl_sheet_header_cols(sheet)

        medical_data = fetch_medical_data()

        data = {
            s[0]: {
                "sku": s[0],
                "name": s[1],
                "category": s[2],
                "preparation": s[3],
                "description": s[4],
                "duration": s[5],
                "biomaterial": s[6],
                "biomarkers": self.get_medical_data_ids(
                    str(s[7]), medical_data.biomarker_ids
                ),
                "medical_exams": self.get_medical_data_ids(
                    str(s[8]), medical_data.medical_exams_ids
                ),
                "is_popular": s[9],
                "is_hidden": s[10],
            }
            for s in sheet.iter_rows(min_row=2, values_only=True)
        }

        current_products = Product.objects.values_list("name", flat=True)

        categories = Category.objects.all()
        categories = {c.name: c for c in categories}

        data_to_update = {k: v for k, v in data.items() if k in current_products}
        data_to_insert = {
            k: v
            for k, v in data.items()
            if k not in current_products and v["is_hidden"] != 1
        }

        channels = Channel.objects.filter(is_active=True)
        popular_collection = Collection.objects.filter(name="Популярное").first()

        biomaterial_attribute_values = AttributeValue.objects.filter(
            attribute_id=AttributeUtils.attrubutes_ids["kdl-biomaterials"]
        )
        biomaterial_attribute_values = {v.slug: v for v in biomaterial_attribute_values}
        preparation_attribute_values = AttributeValue.objects.filter(
            attribute_id=AttributeUtils.attrubutes_ids["kdl-preparation"]
        )
        preparation_attribute_values = {v.slug: v for v in preparation_attribute_values}
        duration_attribute_values = AttributeValue.objects.filter(
            attribute_id=AttributeUtils.attrubutes_ids["kdl-max_duration"]
        )
        duration_attribute_values = {v.slug: v for v in duration_attribute_values}
        biomarkers_assigned_product_attributes = (
            AssignedProductAttribute.objects.filter(
                assignment_id=AttributeUtils.attrubutes_ids["biomarkers"]
            )
        )
        biomarkers_assigned_product_attributes = {
            v.product.pk: v.pk for v in biomarkers_assigned_product_attributes
        }
        medical_exams_assigned_product_attributes = (
            AssignedProductAttribute.objects.filter(
                assignment_id=AttributeUtils.attrubutes_ids["medical_exams"]
            )
        )
        medical_exams_assigned_product_attributes = {
            v.product.pk: v.pk for v in medical_exams_assigned_product_attributes
        }

        popular_collection_assignments = CollectionProduct.objects.filter(
            collection=popular_collection
        )
        popular_collection_assignments = {
            v.product.pk: v for v in popular_collection_assignments
        }

        new_products = []

        for d in data_to_insert.values():
            category = categories.get(d["category"])

            if not category:
                raise CommandError(
                    f"""Can't find category: {d["category"]}, product: {d["sku"]}"""
                )

            new_products.append(
                Product(
                    product_type_id=1,
                    name=d["sku"],
                    slug=slugify(d["sku"], lowercase=True, max_length=100),
                    description=form_description(d["name"], d["description"]),
                    description_plaintext=d["description"],
                    category_id=category.pk,
                    search_index_dirty=True,
                )
            )

        inserted_products = Product.objects.bulk_create(
            new_products, ignore_conflicts=False
        )

        product_variants = []
        product_channel_listings = []
        assigned_product_attribute_values = []
        collection_products = []

        now = datetime.now()

        biomarkers_attribute_values = AttributeValue.objects.filter(
            attribute_id=AttributeUtils.attrubutes_ids["biomarkers"]
        ).values_list("pk", "name")
        biomarkers_attribute_values_ids: dict[int, int] = {
            int(b[1]): b[0] for b in biomarkers_attribute_values
        }
        medical_exams_attribute_values = AttributeValue.objects.filter(
            attribute_id=AttributeUtils.attrubutes_ids["medical_exams"]
        ).values_list("pk", "name")
        medical_exams_attribute_values_ids: dict[int, int] = {
            int(m[1]): m[0] for m in medical_exams_attribute_values
        }

        for product in inserted_products:
            data_product = data.get(product.name)

            if data_product:
                product_variants.append(
                    ProductVariant(
                        sku=f'KDL-{data_product["sku"]}',
                        name="KDL",
                        product=product,
                        track_inventory=False,
                    )
                )

                for channel in channels:
                    product_channel_listings.append(
                        ProductChannelListing(
                            channel=channel,
                            product=product,
                            visible_in_listings=True,
                            available_for_purchase_at=now,
                            currency="RUB",
                            is_published=True,
                            published_at=now,
                        )
                    )

                if (
                    data_product["biomaterial"]
                    and "N/A" not in data_product["biomaterial"]
                ):
                    assigned_product_attribute_values.append(
                        AttributeUtils.add_biomaterial_attribute_data(
                            product.pk,
                            data_product["biomaterial"],
                        )
                    )
                if (
                    data_product["preparation"]
                    and "N/A" not in data_product["preparation"]
                ):
                    assigned_product_attribute_values.append(
                        AttributeUtils.add_preparation_attribute_data(
                            product.pk,
                            data_product["preparation"],
                        )
                    )
                if data_product["duration"] and "N/A" not in str(
                    data_product["duration"]
                ):
                    assigned_product_attribute_values.append(
                        AttributeUtils.add_numeric_attribute_data(
                            product.pk,
                            int(data_product["duration"]),
                            AttributeUtils.attrubutes_ids["kdl-max_duration"],
                        )
                    )
                    assigned_product_attribute_values.append(
                        AttributeUtils.add_numeric_attribute_data(
                            product.pk,
                            # 2 - legacy: duration unit DAYS
                            2,
                            AttributeUtils.attrubutes_ids["kdl-duration_unit"],
                        )
                    )
                if data_product["biomarkers"]:
                    assigned_product_attribute_values += (
                        AttributeUtils.add_medical_attributes_data(
                            product.pk,
                            [int(b) for b in data_product["biomarkers"]],
                            AttributeUtils.attrubutes_ids["biomarkers"],
                            biomarkers_attribute_values_ids,
                        )
                    )

                if data_product["medical_exams"]:
                    assigned_product_attribute_values += (
                        AttributeUtils.add_medical_attributes_data(
                            product.pk,
                            [int(m) for m in data_product["medical_exams"]],
                            AttributeUtils.attrubutes_ids["medical_exams"],
                            medical_exams_attribute_values_ids,
                        )
                    )
                if data_product["is_popular"] == 1 and popular_collection:
                    collection_products.append(
                        CollectionProduct(
                            collection_id=popular_collection.pk, product_id=product.pk
                        )
                    )

        ProductChannelListing.objects.bulk_create(product_channel_listings)
        ProductVariant.objects.bulk_create(product_variants)

        CollectionProduct.objects.bulk_create(collection_products)
        AssignedProductAttributeValue.objects.bulk_create(
            assigned_product_attribute_values
        )

        # UPDATE
        products_to_update = Product.objects.filter(name__in=data_to_update.keys())
        attribute_values_to_update = []
        assigned_product_attribute_values_to_insert = []
        collection_products_to_insert = []

        for p in products_to_update:
            data_product = data_to_update.get(p.name)
            product_id = p.pk

            if data_product:
                category = categories.get(data_product["category"])
                if category:
                    p.category = category

                p.description = form_description(
                    data_product["name"], data_product["description"]
                )
                p.description_plaintext = data_product["description"]

                if (
                    data_product["biomaterial"]
                    and "N/A" not in data_product["biomaterial"]
                ):
                    name = data_product["biomaterial"].replace("\n", ", ")
                    slug = f'{product_id}_{AttributeUtils.attrubutes_ids["kdl-biomaterials"]}'
                    db_attribute = biomaterial_attribute_values.get(slug)

                    if db_attribute:
                        db_attribute.name = name
                        db_attribute.plain_text = name
                        attribute_values_to_update.append(db_attribute)
                    else:
                        assigned_product_attribute_values_to_insert.append(
                            AttributeUtils.add_biomaterial_attribute_data(
                                product_id,
                                data_product["biomaterial"],
                            )
                        )

                if (
                    data_product["preparation"]
                    and "N/A" not in data_product["preparation"]
                ):
                    preparation = data_product["preparation"]
                    name = preparation[:20] + "..."
                    rich_text = form_rich_text(preparation)
                    slug = f'{product_id}_{AttributeUtils.attrubutes_ids["kdl-preparation"]}'
                    db_attribute = preparation_attribute_values.get(slug)

                    if db_attribute:
                        db_attribute.name = name
                        db_attribute.rich_text = rich_text
                        attribute_values_to_update.append(db_attribute)
                    else:
                        assigned_product_attribute_values_to_insert.append(
                            AttributeUtils.add_preparation_attribute_data(
                                product_id, preparation
                            )
                        )

                if data_product["duration"] and "N/A" not in str(
                    data_product["duration"]
                ):
                    duration = data_product["duration"]
                    slug = f'{product_id}_{AttributeUtils.attrubutes_ids["kdl-max_duration"]}'
                    db_attribute = duration_attribute_values.get(slug)

                    if db_attribute:
                        db_attribute.name = duration
                        attribute_values_to_update.append(db_attribute)
                    else:
                        assigned_product_attribute_values_to_insert.append(
                            AttributeUtils.add_numeric_attribute_data(
                                product_id,
                                int(duration),
                                AttributeUtils.attrubutes_ids["kdl-max_duration"],
                            )
                        )
                        assigned_product_attribute_values_to_insert.append(
                            AttributeUtils.add_numeric_attribute_data(
                                product_id,
                                2,
                                AttributeUtils.attrubutes_ids["kdl-duration_unit"],
                            )
                        )

                if data_product["biomarkers"]:
                    biomarkers = [int(b) for b in data_product["biomarkers"]]
                    db_assigned_product_attribute = (
                        biomarkers_assigned_product_attributes.get(product_id)
                    )

                    if db_assigned_product_attribute:
                        AssignedProductAttributeValue.objects.filter(
                            assignment_id=db_assigned_product_attribute
                        ).delete()

                        assigned_product_attribute_values_to_insert += [
                            AssignedProductAttributeValue(
                                assignment_id=db_assigned_product_attribute,
                                value_id=biomarkers_attribute_values_ids.get(m),
                                product_id=product_id,
                            )
                            for m in set(biomarkers)
                        ]
                    else:
                        assigned_product_attribute_values_to_insert += (
                            AttributeUtils.add_medical_attributes_data(
                                product_id,
                                biomarkers,
                                AttributeUtils.attrubutes_ids["biomarkers"],
                                biomarkers_attribute_values_ids,
                            )
                        )

                if data_product["medical_exams"]:
                    medical_exams = [int(m) for m in data_product["medical_exams"]]
                    db_assigned_product_attribute = (
                        medical_exams_assigned_product_attributes.get(product_id)
                    )

                    if db_assigned_product_attribute:
                        AssignedProductAttributeValue.objects.filter(
                            assignment_id=db_assigned_product_attribute
                        ).delete()

                        assigned_product_attribute_values_to_insert += [
                            AssignedProductAttributeValue(
                                assignment_id=db_assigned_product_attribute,
                                value_id=medical_exams_attribute_values_ids.get(m),
                                product_id=product_id,
                            )
                            for m in set(medical_exams)
                        ]
                    else:
                        assigned_product_attribute_values_to_insert += (
                            AttributeUtils.add_medical_attributes_data(
                                product_id,
                                medical_exams,
                                AttributeUtils.attrubutes_ids["medical_exams"],
                                medical_exams_attribute_values_ids,
                            )
                        )

                if popular_collection:
                    is_popular = data_product["is_popular"]
                    product_popular_collection_assignment = (
                        popular_collection_assignments.get(product_id)
                    )

                    if is_popular != 1 and product_popular_collection_assignment:
                        product_popular_collection_assignment.delete()
                    elif is_popular == 1 and not product_popular_collection_assignment:
                        collection_products_to_insert.append(
                            CollectionProduct(
                                collection_id=popular_collection.pk,
                                product_id=product_id,
                            )
                        )

        Product.objects.bulk_update(
            products_to_update,
            ["category", "description", "description_plaintext"],
            batch_size=500,
        )
        AttributeValue.objects.bulk_update(
            attribute_values_to_update,
            ["name", "plain_text", "rich_text"],
            batch_size=500,
        )
        AssignedProductAttributeValue.objects.bulk_create(
            assigned_product_attribute_values_to_insert,
            batch_size=500,
        )
        CollectionProduct.objects.bulk_create(collection_products_to_insert)

        return
