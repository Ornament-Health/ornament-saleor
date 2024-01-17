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
    ProductVariantChannelListing,
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
        "rating",
        "color slug",
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

    def add_featured_attribute_data(
        self,
        product_id: int,
        featured_attribute_values: dict[str, AttributeValue],
    ) -> AssignedProductAttributeValue:
        assigned_product_attribute = AssignedProductAttribute(
            product_id=product_id,
            assignment_id=AttributeUtils.attrubutes_ids["featured"],
        )

        assigned_product_attribute.save()

        featured_slug = f"{AttributeUtils.attrubutes_ids['featured']}_true"

        featured_attribute_value = featured_attribute_values.get(featured_slug)

        if not featured_attribute_value:
            raise CommandError(
                f"""Can't find featured attribute value for slug {featured_slug}"""
            )

        return AssignedProductAttributeValue(
            assignment_id=assigned_product_attribute.pk,
            value_id=featured_attribute_value.pk,
            product_id=product_id,
        )

    def add_color_attribute_data(
        self,
        product_id: int,
        color_slug: str,
        color_attribute_values: dict[str, AttributeValue],
    ) -> AssignedProductAttributeValue:
        assigned_product_attribute = AssignedProductAttribute(
            product_id=product_id,
            assignment_id=AttributeUtils.attrubutes_ids["color"],
        )

        assigned_product_attribute.save()

        color_attribute_value = color_attribute_values.get(color_slug)

        if not color_attribute_value:
            raise CommandError(
                f"""Can't find color attribute value for slug {color_slug}"""
            )

        return AssignedProductAttributeValue(
            assignment_id=assigned_product_attribute.pk,
            value_id=color_attribute_value.pk,
            product_id=product_id,
        )

    def check_row_required_data(self, row: tuple) -> bool:
        return all([row[0], row[1], row[2]])

    def get_attribute_assignments(
        self,
        product: Product,
        db_attribute_value: AttributeValue,
        attribute_name: str,
    ) -> tuple[bool, int]:
        recreate = False
        reassign_pk = 0

        assigned_value = product.attributevalues.filter(
            value_id=db_attribute_value.pk
        ).first()

        if assigned_value:
            return recreate, reassign_pk

        assigned_attribute = product.attributes.filter(
            assignment_id=AttributeUtils.attrubutes_ids[attribute_name]
        ).first()

        if not assigned_attribute:
            db_attribute_value.delete()
            recreate = True
        else:
            reassign_pk = assigned_attribute.pk

        return recreate, reassign_pk

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
                "rating": s[11],
                "color_slug": s[12],
            }
            for s in sheet.iter_rows(min_row=2, values_only=True)
            if self.check_row_required_data(s)
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

        duration_unit_attribute_values = AttributeValue.objects.filter(
            attribute_id=AttributeUtils.attrubutes_ids["kdl-duration_unit"]
        )
        duration_unit_attribute_values = {
            v.slug: v for v in duration_unit_attribute_values
        }

        featured_attribute_values = AttributeValue.objects.filter(
            attribute_id=AttributeUtils.attrubutes_ids["featured"]
        )
        featured_attribute_values = {v.slug: v for v in featured_attribute_values}

        color_attribute_values = AttributeValue.objects.filter(
            attribute_id=AttributeUtils.attrubutes_ids["color"]
        )
        color_attribute_values = {v.slug: v for v in color_attribute_values}

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

        featured_assigned_product_attributes = AssignedProductAttribute.objects.filter(
            assignment_id=AttributeUtils.attrubutes_ids["featured"]
        )
        featured_assigned_product_attributes = {
            v.product.pk: v.pk for v in featured_assigned_product_attributes
        }

        color_assigned_product_attributes = AssignedProductAttribute.objects.filter(
            assignment_id=AttributeUtils.attrubutes_ids["color"]
        )
        color_assigned_product_attributes = {
            v.product.pk: v.pk for v in color_assigned_product_attributes
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
                    description_plaintext=d["description"] or "",
                    category_id=category.pk,
                    search_index_dirty=True,
                    rating=d["rating"],
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

                if data_product["is_popular"] == 1:
                    assigned_product_attribute_values.append(
                        self.add_featured_attribute_data(
                            product.pk, featured_attribute_values
                        )
                    )

                    if popular_collection:
                        collection_products.append(
                            CollectionProduct(
                                collection_id=popular_collection.pk,
                                product_id=product.pk,
                            )
                        )

                if data_product["color_slug"]:
                    assigned_product_attribute_values.append(
                        self.add_color_attribute_data(
                            product.pk,
                            data_product["color_slug"],
                            color_attribute_values,
                        )
                    )

        ProductChannelListing.objects.bulk_create(product_channel_listings)
        ProductVariant.objects.bulk_create(product_variants)

        CollectionProduct.objects.bulk_create(collection_products)
        AssignedProductAttributeValue.objects.bulk_create(
            assigned_product_attribute_values
        )

        # UPDATE
        data_to_delist = [
            f"KDL-{k}" for k, v in data_to_update.items() if v["is_hidden"] == 1
        ]
        data_to_update = {
            k: v for k, v in data_to_update.items() if v["is_hidden"] != 1
        }

        products_to_update = Product.objects.filter(
            name__in=data_to_update.keys()
        ).prefetch_related("attributevalues", "attributes")

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
                p.description_plaintext = data_product["description"] or ""

                if data_product["rating"]:
                    p.rating = float(data_product["rating"])
                else:
                    p.rating = None

                p.save()

                if (
                    data_product["biomaterial"]
                    and "N/A" not in data_product["biomaterial"]
                ):
                    name = data_product["biomaterial"].replace("\n", ", ")
                    slug = f'{product_id}_{AttributeUtils.attrubutes_ids["kdl-biomaterials"]}'
                    db_attribute_value = biomaterial_attribute_values.get(slug)

                    if db_attribute_value:
                        (
                            recreate,
                            reassign_pk,
                        ) = self.get_attribute_assignments(
                            p,
                            db_attribute_value,
                            "kdl-biomaterials",
                        )

                        if recreate:
                            assigned_product_attribute_values_to_insert.append(
                                AttributeUtils.add_biomaterial_attribute_data(
                                    product_id,
                                    data_product["biomaterial"],
                                )
                            )
                        elif reassign_pk:
                            assigned_product_attribute_values_to_insert.append(
                                AssignedProductAttributeValue(
                                    assignment_id=reassign_pk,
                                    value_id=db_attribute_value.pk,
                                    product_id=product_id,
                                )
                            )

                        if not recreate:
                            db_attribute_value.name = name
                            db_attribute_value.plain_text = name
                            attribute_values_to_update.append(db_attribute_value)
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
                    db_attribute_value = preparation_attribute_values.get(slug)

                    if db_attribute_value:
                        (
                            recreate,
                            reassign_pk,
                        ) = self.get_attribute_assignments(
                            p,
                            db_attribute_value,
                            "kdl-preparation",
                        )

                        if recreate:
                            assigned_product_attribute_values_to_insert.append(
                                AttributeUtils.add_preparation_attribute_data(
                                    product_id,
                                    preparation,
                                )
                            )
                        elif reassign_pk:
                            assigned_product_attribute_values_to_insert.append(
                                AssignedProductAttributeValue(
                                    assignment_id=reassign_pk,
                                    value_id=db_attribute_value.pk,
                                    product_id=product_id,
                                )
                            )

                        if not recreate:
                            db_attribute_value.name = name
                            db_attribute_value.rich_text = rich_text
                            attribute_values_to_update.append(db_attribute_value)

                    else:
                        assigned_product_attribute_values_to_insert.append(
                            AttributeUtils.add_preparation_attribute_data(
                                product_id, preparation
                            )
                        )

                if data_product["duration"] and "N/A" not in str(
                    data_product["duration"]
                ):
                    duration = int(data_product["duration"])
                    duration_slug = f'{product_id}_{AttributeUtils.attrubutes_ids["kdl-max_duration"]}'
                    duration_unit_slug = f'{product_id}_{AttributeUtils.attrubutes_ids["kdl-duration_unit"]}'
                    duration_db_attribute_value = duration_attribute_values.get(
                        duration_slug
                    )
                    duration_unit_db_attribute_value = (
                        duration_unit_attribute_values.get(duration_unit_slug)
                    )

                    if duration_db_attribute_value:
                        (
                            recreate,
                            reassign_pk,
                        ) = self.get_attribute_assignments(
                            p,
                            duration_db_attribute_value,
                            "kdl-max_duration",
                        )

                        if recreate:
                            assigned_product_attribute_values_to_insert.append(
                                AttributeUtils.add_numeric_attribute_data(
                                    product_id,
                                    duration,
                                    AttributeUtils.attrubutes_ids["kdl-max_duration"],
                                )
                            )
                        elif reassign_pk:
                            assigned_product_attribute_values_to_insert.append(
                                AssignedProductAttributeValue(
                                    assignment_id=reassign_pk,
                                    value_id=duration_db_attribute_value.pk,
                                    product_id=product_id,
                                )
                            )

                        if not recreate:
                            duration_db_attribute_value.name = str(duration)
                            attribute_values_to_update.append(
                                duration_db_attribute_value
                            )

                    if duration_unit_db_attribute_value:
                        (
                            recreate,
                            reassign_pk,
                        ) = self.get_attribute_assignments(
                            p,
                            duration_unit_db_attribute_value,
                            "kdl-duration_unit",
                        )

                        if recreate:
                            assigned_product_attribute_values_to_insert.append(
                                AttributeUtils.add_numeric_attribute_data(
                                    product_id,
                                    duration,
                                    AttributeUtils.attrubutes_ids["kdl-duration_unit"],
                                )
                            )
                        elif reassign_pk:
                            assigned_product_attribute_values_to_insert.append(
                                AssignedProductAttributeValue(
                                    assignment_id=reassign_pk,
                                    value_id=duration_unit_db_attribute_value.pk,
                                    product_id=product_id,
                                )
                            )

                        if not recreate:
                            duration_unit_db_attribute_value.name = "2"
                            attribute_values_to_update.append(
                                duration_unit_db_attribute_value
                            )

                    if not all(
                        [duration_db_attribute_value, duration_unit_db_attribute_value]
                    ):
                        assigned_product_attribute_values_to_insert.append(
                            AttributeUtils.add_numeric_attribute_data(
                                product_id,
                                duration,
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

                if data_product["color_slug"]:
                    db_assigned_product_attribute = (
                        color_assigned_product_attributes.get(product_id)
                    )
                    if db_assigned_product_attribute:
                        assigned_value = AssignedProductAttributeValue.objects.filter(
                            assignment_id=db_assigned_product_attribute
                        ).first()

                        db_value_for_current_slug = color_attribute_values.get(
                            data_product["color_slug"]
                        )

                        if assigned_value:
                            if (
                                db_value_for_current_slug
                                and assigned_value.value != db_value_for_current_slug
                            ):
                                assigned_value.value = db_value_for_current_slug
                                assigned_value.save()
                        elif db_value_for_current_slug:
                            assigned_product_attribute_values_to_insert.append(
                                AssignedProductAttributeValue(
                                    assignment_id=db_assigned_product_attribute,
                                    value_id=db_value_for_current_slug.pk,
                                    product_id=product_id,
                                )
                            )

                    else:
                        assigned_product_attribute_values_to_insert.append(
                            self.add_color_attribute_data(
                                product_id,
                                data_product["color_slug"],
                                color_attribute_values,
                            )
                        )

                is_popular = data_product["is_popular"]

                db_assigned_featured_product_attribute = (
                    featured_assigned_product_attributes.get(product_id)
                )

                if is_popular != 1 and db_assigned_featured_product_attribute:
                    AssignedProductAttributeValue.objects.filter(
                        assignment_id=db_assigned_featured_product_attribute
                    ).delete()
                    AssignedProductAttribute.objects.filter(
                        id=db_assigned_featured_product_attribute
                    ).delete()
                elif is_popular == 1 and not db_assigned_featured_product_attribute:
                    assigned_product_attribute_values_to_insert.append(
                        self.add_featured_attribute_data(
                            product_id, featured_attribute_values
                        )
                    )

                if popular_collection:
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

        ProductVariantChannelListing.objects.filter(
            variant__sku__in=data_to_delist
        ).delete()

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
