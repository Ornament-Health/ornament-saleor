import os
import csv

from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import DecimalValidator

from saleor.product.models import ProductVariantChannelListing, ProductVariant
from saleor.channel.models import Channel
from saleor.warehouse.models import Stock


class Command(BaseCommand):
    help = "Sync KDL channel product prices with CSV file"

    def add_arguments(self, parser):
        parser.add_argument("filename", help="Path to CSV file with target data")

    def handle(self, *args, **options):
        filename = options.get("filename")

        if not os.path.isfile(filename):  # type: ignore
            raise CommandError(f'CSV file "{filename}" does not exist.')

        # get csv data
        with open(filename, encoding="utf8", mode="rt") as csvfile:  # type: ignore
            reader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
            data = [i for i in reader]

        decimal_validator = DecimalValidator(
            max_digits=settings.DEFAULT_MAX_DIGITS,
            decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        )

        def price_validator(value):
            dvalue = None
            try:
                if value.strip() == "-":
                    dvalue = Decimal(-1)
                else:
                    dvalue = Decimal(value)
                    decimal_validator(dvalue)
                error = None
            except InvalidOperation:
                error = f'Defined price "{value}" is not valid decimal value.'
            except ValidationError as e:
                error = e.messages[0]
            except Exception as e:
                error = str(e)

            return (value if dvalue is None else dvalue, error)

        def make_kdl_sku(sku: str) -> str:
            return f"KDL-{sku}"

        csv_keys = ("local_provider", "sku", "price")

        if not data or set(csv_keys).difference(data[0].keys()):
            raise CommandError(
                f"CSV is empty of not contains all required columns ({csv_keys})."
            )

        channels = set(i["local_provider"] for i in data)
        if len(channels) > 1:
            raise CommandError(
                f"Multiple channels provided. Please export data only for one channel (local_provider)"
            )

        channel_slug = channels.pop()
        channel = Channel.objects.filter(slug=channel_slug).first()
        kdl_skus = set(make_kdl_sku(i["sku"]) for i in data)

        product_variant_channel_listings_q = (
            ProductVariantChannelListing.objects.filter(
                variant__sku__in=kdl_skus, channel=channel
            ).prefetch_related("channel", "variant")
        )

        prices = {make_kdl_sku(d["sku"]): d["price"] for d in data}

        errors = []
        for pvcl in product_variant_channel_listings_q:
            sku = pvcl.variant.sku

            if sku:
                price = prices.pop(sku)

                if price:
                    validated_price, error = price_validator(price)

                    if error:
                        errors.append({"sku": sku, "price": price, "error": error})
                        continue

                    pvcl.price_amount = validated_price
                    pvcl.discounted_price_amount = validated_price

        variants = ProductVariant.objects.filter(sku__in=(prices.keys()))
        new_product_variant_channel_listings = []
        new_warehouse_stocks = []

        for variant in variants:
            if variant.sku:
                price = prices.get(variant.sku)
                new_product_variant_channel_listings.append(
                    ProductVariantChannelListing(
                        variant=variant,
                        channel=channel,
                        currency="RUB",
                        price_amount=price,
                        discounted_price_amount=price,
                    )
                )
                new_warehouse_stocks.append(
                    Stock(
                        warehouse_id="2e83f67b-a080-4710-9ee8-4bf3bc0e0b58",
                        product_variant=variant,
                        quantity=1,
                        quantity_allocated=0,
                    )
                )

        # update existing product variants listings
        ProductVariantChannelListing.objects.bulk_update(
            product_variant_channel_listings_q,
            ["price_amount", "discounted_price_amount"],
        )

        # create new product variants listings
        ProductVariantChannelListing.objects.bulk_create(
            new_product_variant_channel_listings
        )

        # create new stock for product variants listings
        Stock.objects.bulk_create(new_warehouse_stocks)

        return print(errors) if errors else None