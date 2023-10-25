from itertools import groupby
from operator import attrgetter


from saleor.product.models import ProductChannelListing


def resolve_search_products(info):
    qs = (
        ProductChannelListing.objects.filter(visible_in_listings=True)
        .order_by("product_id")
        .prefetch_related("channel", "product__variants__channel_listings")
    )

    products = []

    for _, group in groupby(qs, attrgetter("product_id")):
        listings = list(group)
        product = listings[0].product
        channels = [listing.channel.slug for listing in listings]
        product.channels = channels

        # TODO: allow to fetch all variants (all vendors) prices
        # will be necessary if our app allows to search among different vendors
        current_variant = product.variants.first()
        current_variant_prices = current_variant.channel_listings.select_related(
            "channel"
        ).values("channel__slug", "price_amount", "currency")

        if not current_variant_prices:
            continue

        product.current_variant_prices = current_variant_prices
        products.append(product)

    return products
