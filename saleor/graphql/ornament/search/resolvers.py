from itertools import groupby
from operator import attrgetter

from saleor.ornament.vendors.models import Vendor
from saleor.product.models import ProductChannelListing


def resolve_search_products(info):
    qs = (
        ProductChannelListing.objects.filter(visible_in_listings=True)
        .order_by("product_id")
        .prefetch_related("channel", "product__variants__channel_listings")
    )
    vendors = Vendor.objects.values_list("name", flat=True)

    products = []

    for _, group in groupby(qs, attrgetter("product_id")):
        listings = list(group)
        product = listings[0].product
        channels = [listing.channel.slug for listing in listings]
        product.channels = channels

        variants = product.variants.all()
        product_prices = []
        product_vendors = set()

        for variant in variants:
            if not variant.name in vendors:
                continue

            variant_prices = variant.channel_listings.select_related("channel").values(
                "channel__slug", "price_amount", "currency"
            )
            variant_prices = [{**v, "vendor": variant.name} for v in variant_prices]
            product_prices += variant_prices
            product_vendors.add(variant.name)

        if not product_prices:
            continue

        product.variants_prices = product_prices
        product.vendors = product_vendors
        # legacy (for old app versions support), deprecated
        product.variant_id = variants[0].id

        products.append(product)

    return products
