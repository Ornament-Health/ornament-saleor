from datetime import datetime
import os
import csv

from django.core.management.base import BaseCommand, CommandError
from slugify import slugify

from saleor.attribute.models.base import AttributeValue
from saleor.attribute.models.product import (
    AssignedProductAttributeValue,
)
from saleor.ornament.vendors.utils import (
    form_description,
    get_current_timestamp,
    random_string,
)
from saleor.product.models import Product, ProductVariant, ProductChannelListing
from saleor.channel.models import Channel
from saleor.ornament.vendors.kdl.utils import attributes_ids


class Command(BaseCommand):
    help = "Import KDL products with CSV file"

    def add_arguments(self, parser):
        parser.add_argument("filename", help="Path to CSV file with target data")

    def get_preparation_attributes_data(
        self, product: Product, id: int, preparation: str
    ) -> tuple[
        AttributeValue,
        AssignedProductAttributeValue,
    ]:
        name = preparation[:50] + "..."
        rich_text = {
            "time": get_current_timestamp(),
            "blocks": [
                {
                    "id": random_string(10),
                    "data": {"text": preparation},
                    "type": "paragraph",
                }
            ],
            # TODO::ornament move to settings
            "version": "2.24.3",
        }
        slug = f'{product.pk}_{attributes_ids["kdl_preparation"]}'

        attribute_value = AttributeValue(
            id=id,
            name=name,
            attribute_id=attributes_ids["kdl_preparation"],
            slug=slug,
            rich_text=rich_text,
            sort_order=0,
        )
        assigned_product_attribute_value = AssignedProductAttributeValue(
            id=id,
            value_id=id,
            assignment_id=id,
            product=product,
            sort_order=0,
        )

        return (
            attribute_value,
            assigned_product_attribute_value,
        )

    def get_duration_unit_attributes_data(self, product: Product, id: int) -> tuple[
        AttributeValue,
        AssignedProductAttributeValue,
    ]:
        slug = f'{product.pk}_{attributes_ids["kdl_duration_unit"]}'

        attribute_value = AttributeValue(
            id=id,
            name=2,
            attribute_id=attributes_ids["kdl_duration_unit"],
            slug=slug,
            sort_order=0,
        )

        assigned_product_attribute_value = AssignedProductAttributeValue(
            id=id,
            value_id=id,
            assignment_id=id,
            product=product,
            sort_order=0,
        )

        return (
            attribute_value,
            assigned_product_attribute_value,
        )

    def get_max_duration_attributes_data(
        self, product: Product, id: int, duration: str
    ) -> tuple[
        AttributeValue,
        AssignedProductAttributeValue,
    ]:
        slug = f'{product.pk}_{attributes_ids["kdl_max_duration"]}'

        attribute_value = AttributeValue(
            id=id,
            name=duration,
            attribute_id=attributes_ids["kdl_max_duration"],
            slug=slug,
            sort_order=0,
        )

        assigned_product_attribute_value = AssignedProductAttributeValue(
            id=id,
            value_id=id,
            assignment_id=id,
            product=product,
            sort_order=0,
        )

        return (
            attribute_value,
            assigned_product_attribute_value,
        )

    def get_biomaterial_attributes_data(
        self, product: Product, id: int, biomaterial: str
    ) -> tuple[
        AttributeValue,
        AssignedProductAttributeValue,
    ]:
        value = biomaterial.replace("\n", ", ")
        slug = f'{product.pk}_{attributes_ids["kdl_biomaterials"]}'

        attribute_value = AttributeValue(
            id=id,
            name=value,
            attribute_id=attributes_ids["kdl_biomaterials"],
            slug=slug,
            plain_text=value,
            sort_order=0,
        )

        assigned_product_attribute_value = AssignedProductAttributeValue(
            id=id,
            value_id=id,
            assignment_id=id,
            product=product,
            sort_order=0,
        )

        return (
            attribute_value,
            assigned_product_attribute_value,
        )

    def get_last_attribute_id(self, attribute_id: int) -> int:
        last_attribute_value = (
            AttributeValue.objects.filter(attribute_id=attribute_id)
            .order_by("-id")
            .first()
        )
        return last_attribute_value.pk if last_attribute_value else 0

    def handle(self, *args, **options):
        filename = options.get("filename")

        if not os.path.isfile(filename):  # type: ignore
            raise CommandError(f'CSV file "{filename}" does not exist.')

        # get csv data
        with open(filename, encoding="utf8", mode="rt") as csvfile:  # type: ignore
            reader = csv.DictReader(csvfile, delimiter=";", quotechar='"')
            data = [i for i in reader]

        csv_keys = (
            "sku",
            "name",
            "preparation",
            "description",
            "duration",
            "biomaterial",
        )

        if not data or set(csv_keys).difference(data[0].keys()):
            raise CommandError(
                f"CSV is empty of not contains all required columns ({csv_keys})."
            )

        current_products = Product.objects.values_list("name", flat=True)
        data = [d for d in data if d["sku"] not in current_products]

        channels = Channel.objects.filter(is_active=True)

        products = [
            Product(
                product_type_id=1,
                name=d["sku"],
                slug=slugify(d["sku"], lowercase=True, max_length=100),
                description=form_description(d["name"], d["description"]),
                description_plaintext=d["description"],
                category_id=1000,
                search_index_dirty=True,
            )
            for d in data
        ]

        inserted_products = Product.objects.bulk_create(
            products, ignore_conflicts=False
        )

        product_variants = []
        product_channel_listings = []
        attribute_values = []
        assigned_product_attribute_values = []

        data = {d["sku"]: d for d in data}

        prep_last_attribute_value_id = self.get_last_attribute_id(
            attributes_ids["kdl_preparation"]
        )
        bio_last_attribute_value_id = self.get_last_attribute_id(
            attributes_ids["kdl_biomaterials"]
        )
        duration_unit_last_attribute_value_id = self.get_last_attribute_id(
            attributes_ids["kdl_duration_unit"]
        )
        max_duration_last_attribute_value_id = self.get_last_attribute_id(
            attributes_ids["kdl_max_duration"]
        )

        i_preparation = 0
        i_biomaterial = 0
        i_duration_unit = 0
        i_max_duration = 0

        now = datetime.now()

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

                if data_product["preparation"]:
                    i_preparation += 1
                    curr_prep_id = prep_last_attribute_value_id + i_preparation

                    preparation = data_product["preparation"]

                    (
                        attribute_value,
                        assigned_product_attribute_value,
                    ) = self.get_preparation_attributes_data(
                        product, curr_prep_id, preparation
                    )

                    attribute_values.append(attribute_value)
                    assigned_product_attribute_values.append(
                        assigned_product_attribute_value
                    )

                if data_product["biomaterial"]:
                    i_biomaterial += 1
                    curr_bio_id = bio_last_attribute_value_id + i_biomaterial

                    biomaterial = data_product["biomaterial"]

                    (
                        attribute_value,
                        assigned_product_attribute_value,
                    ) = self.get_biomaterial_attributes_data(
                        product, curr_bio_id, biomaterial
                    )

                    attribute_values.append(attribute_value)
                    assigned_product_attribute_values.append(
                        assigned_product_attribute_value
                    )

                if data_product["duration"]:
                    i_duration_unit += 1
                    i_max_duration += 1
                    curr_duration_unit_id = (
                        duration_unit_last_attribute_value_id + i_duration_unit
                    )
                    curr_max_duration_id = (
                        max_duration_last_attribute_value_id + i_max_duration
                    )

                    duration = data_product["duration"]

                    (
                        attribute_value_d_u,
                        assigned_product_attribute_value_d_u,
                    ) = self.get_duration_unit_attributes_data(
                        product, curr_duration_unit_id
                    )

                    (
                        attribute_value_m_d,
                        assigned_product_attribute_value_m_d,
                    ) = self.get_max_duration_attributes_data(
                        product, curr_max_duration_id, duration
                    )

                    attribute_values.append(attribute_value_d_u)
                    assigned_product_attribute_values.append(
                        assigned_product_attribute_value_d_u
                    )

                    attribute_values.append(attribute_value_m_d)
                    assigned_product_attribute_values.append(
                        assigned_product_attribute_value_m_d
                    )

        ProductChannelListing.objects.bulk_create(product_channel_listings)
        ProductVariant.objects.bulk_create(product_variants)

        AttributeValue.objects.bulk_create(attribute_values)
        AssignedProductAttributeValue.objects.bulk_create(
            assigned_product_attribute_values
        )

        return
