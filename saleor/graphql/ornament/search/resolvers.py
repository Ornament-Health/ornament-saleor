from itertools import groupby
from operator import attrgetter


from saleor.product.models import ProductChannelListing


def resolve_search_products(info):
    qs = (
        ProductChannelListing.objects.filter(visible_in_listings=True)
        .order_by("product_id")
        .prefetch_related("channel")
    )
    products = []
    for _, group in groupby(qs, attrgetter("product_id")):
        listings = list(group)
        product = listings[0].product
        channels = [listing.channel.slug for listing in listings]
        # channels = [listing.channel_id for listing in listings]
        product.channels = channels
        products.append(product)
    return products
