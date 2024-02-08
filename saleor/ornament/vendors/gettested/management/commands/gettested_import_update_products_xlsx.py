from datetime import datetime
import os
import secrets
import string

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import DecimalValidator
from slugify import slugify
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.utils import exceptions as openpyxl_exceptions

from saleor.attribute.models.base import AttributeValue
from saleor.attribute.models.product import (
    AssignedProductAttribute,
    AssignedProductAttributeValue,
)
from saleor.product.models import (
    Product,
    ProductVariant,
    ProductChannelListing,
    Category,
    ProductVariantChannelListing,
)
from saleor.warehouse.models import Stock
from saleor.channel.models import Channel

GETTESTED_SKU_PREFIX = "GT"

decimal_validator = DecimalValidator(
    max_digits=settings.DEFAULT_MAX_DIGITS,
    decimal_places=settings.DEFAULT_DECIMAL_PLACES,
)


class Command(BaseCommand):
    help = "Import/Update GetTested products with XLSX file"
    known_header_rows = ["Suffix", "Test", "Test method", "Description", "GBP"]

    def add_arguments(self, parser):
        parser.add_argument("filename", help="Path to XLSX file with target data")

    def check_sheet_header_cols(self, sheet: Worksheet) -> None:
        sheet_header_cols: set = set(
            [s for s in sheet.iter_rows(min_row=4, max_row=4, values_only=True)][0]
        )

        if set(self.known_header_rows).difference(sheet_header_cols):
            raise CommandError(
                f"Sheet header does not contain all known columns: {self.known_header_rows}"
            )

    def form_gettested_sku(self, name, suffix):
        name = name.replace("\t", "").replace("\n", "")
        return f"{GETTESTED_SKU_PREFIX} {name} ({suffix})"

    def check_row_required_data(self, row: tuple) -> bool:
        return all([row[1], row[3], row[9], row[22]])

    def random_string(self, size: int) -> str:
        letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
        return "".join(secrets.choice(letters) for _ in range(size))

    def get_current_timestamp(self) -> float:
        now = datetime.now()
        return now.timestamp()

    def form_description_block(self, text: str, block_type: str) -> dict:
        return {
            "id": self.random_string(10),
            "data": {"text": text},
            "type": block_type,
        }

    def form_description(self, name: str, description: str) -> dict:
        description_dict = {
            "time": self.get_current_timestamp(),
            "blocks": [self.form_description_block(name, "header")],
            "version": "2.24.3",
        }

        if description:
            blocks = description.split("\n")

            for block in blocks:
                description_dict["blocks"].append(
                    self.form_description_block(block, "paragraph")
                )

        return description_dict

    def add_test_method_attribute_data(
        self, product_id: int, test_method: str
    ) -> AssignedProductAttributeValue:
        attribute_id = 14
        name = test_method.replace("\n", ", ")
        slug = f"{product_id}_{attribute_id}"

        test_method_attribute_value = AttributeValue(
            name=name,
            attribute_id=attribute_id,
            slug=slug,
            plain_text=name,
            sort_order=attribute_id,
        )

        test_method_assigned_product_attribute = AssignedProductAttribute(
            product_id=product_id,
            assignment_id=attribute_id,
        )

        test_method_attribute_value.save()
        test_method_assigned_product_attribute.save()

        return AssignedProductAttributeValue(
            assignment_id=test_method_assigned_product_attribute.pk,
            value_id=test_method_attribute_value.pk,
            product_id=product_id,
        )

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

        sheet = wb["Test"]

        self.check_sheet_header_cols(sheet)

        data = {
            self.form_gettested_sku(s[3], s[1]): {
                "sku": self.form_gettested_sku(s[3], s[1]),
                "name": s[3],
                "description": s[22],
                "price_GBP": s[9],
                "test_method": s[6],
            }
            for s in sheet.iter_rows(min_row=5, values_only=True)
            if self.check_row_required_data(s)
        }

        current_products = Product.objects.values_list("name", flat=True)

        gettested_category = Category.objects.filter(slug="gettested-default").first()
        gettested_channel = Channel.objects.filter(slug="uk-gettested").first()

        if not all([gettested_category, gettested_channel]):
            raise CommandError(
                f"Please check 'gettested-default' category and 'uk-gettested' channel if they exist"
            )

        data_to_update = {k: v for k, v in data.items() if k in current_products}
        data_to_insert = {k: v for k, v in data.items() if k not in current_products}

        test_method_attribute_values = AttributeValue.objects.filter(attribute_id=14)
        test_method_attribute_values = {v.slug: v for v in test_method_attribute_values}

        new_products = []

        for d in data_to_insert.values():
            new_products.append(
                Product(
                    product_type_id=1,
                    name=d["sku"],
                    slug=slugify(d["sku"], lowercase=True, max_length=100),
                    description=self.form_description(d["name"], d["description"]),
                    description_plaintext=d["description"],
                    category_id=gettested_category.pk,
                    search_index_dirty=True,
                )
            )

        inserted_products = Product.objects.bulk_create(
            new_products, ignore_conflicts=False
        )

        product_variants = []
        product_channel_listings = []

        now = datetime.now()

        assigned_product_attribute_values = []

        for product in inserted_products:
            product_variants.append(
                ProductVariant(
                    sku=product.name,
                    name="GetTested",
                    product=product,
                    track_inventory=False,
                )
            )
            product_channel_listings.append(
                ProductChannelListing(
                    channel=gettested_channel,
                    product=product,
                    visible_in_listings=True,
                    available_for_purchase_at=now,
                    currency="GBP",
                    is_published=True,
                    published_at=now,
                )
            )

            product_data = data_to_insert.get(product.name) or {}
            test_method = product_data.get("test_method")

            if test_method:
                assigned_product_attribute_values.append(
                    self.add_test_method_attribute_data(product.pk, test_method)
                )

        inserted_variants = ProductVariant.objects.bulk_create(product_variants)
        ProductChannelListing.objects.bulk_create(product_channel_listings)

        new_product_variant_channel_listings = []
        new_warehouse_stocks = []

        for variant in inserted_variants:
            if variant.sku:
                product_data = data_to_insert.get(variant.sku) or {}
                # inserted_skus_prices.append(variant.sku)
                price = product_data.get("price_GBP")

                if price:
                    new_product_variant_channel_listings.append(
                        ProductVariantChannelListing(
                            variant=variant,
                            channel=gettested_channel,
                            currency="GBP",
                            price_amount=price,
                            discounted_price_amount=price,
                        )
                    )
                    new_warehouse_stocks.append(
                        Stock(
                            warehouse_id="08061547-682e-4196-bfcf-273a859aca25",
                            product_variant=variant,
                            quantity=1,
                            quantity_allocated=0,
                        )
                    )

        # create new product variants listings
        ProductVariantChannelListing.objects.bulk_create(
            new_product_variant_channel_listings
        )

        # create new stock for product variants listings
        Stock.objects.bulk_create(new_warehouse_stocks)

        # UPDATE
        products_to_update = Product.objects.filter(name__in=data_to_update.keys())
        product_variant_channel_listings_to_update = (
            ProductVariantChannelListing.objects.filter(
                variant__sku__in=data_to_update.keys(), channel=gettested_channel
            ).prefetch_related("channel", "variant")
        )
        attribute_values_to_update = []

        for product in products_to_update:
            data_product = data_to_update.get(product.name)

            if data_product:
                sku = data_product.get("sku")
                name = data_product.get("name")
                description = data_product.get("description")
                test_method = data_product.get("test_method")

                if sku:
                    product.name = sku
                    product.search_index_dirty = True

                if name and description:
                    product.description = self.form_description(name, description)
                    product.description_plaintext = description
                    product.search_index_dirty = True

                if test_method:
                    slug = f"{product.pk}_{14}"
                    db_attribute_value = test_method_attribute_values.get(slug)

                    if db_attribute_value:
                        db_attribute_value.name = test_method
                        db_attribute_value.plain_text = name
                        attribute_values_to_update.append(db_attribute_value)
                    else:
                        assigned_product_attribute_values.append(
                            self.add_test_method_attribute_data(product.pk, test_method)
                        )

        for (
            product_variant_channel_listing
        ) in product_variant_channel_listings_to_update:
            sku = product_variant_channel_listing.variant.sku

            if sku:
                data_product = data_to_update.get(sku) or {}
                price = data_product.get("price_GBP")

                if price:
                    product_variant_channel_listing.price_amount = price
                    product_variant_channel_listing.discounted_price_amount = price

        AssignedProductAttributeValue.objects.bulk_create(
            assigned_product_attribute_values
        )

        AttributeValue.objects.bulk_update(
            attribute_values_to_update, ["name", "plain_text"]
        )

        Product.objects.bulk_update(
            products_to_update,
            ["name", "description", "search_index_dirty"],
        )

        ProductVariantChannelListing.objects.bulk_update(
            product_variant_channel_listings_to_update,
            ["price_amount", "discounted_price_amount"],
        )

        return
