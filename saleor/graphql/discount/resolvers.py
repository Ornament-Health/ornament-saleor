from django.conf import settings

from ...discount import models
from ..channel import ChannelContext, ChannelQsContext
from .filters import filter_sale_search, filter_voucher_search

# @cf::ornament.saleor.graphql.discount
from saleor.graphql.core.utils import from_global_id_or_error
from saleor.graphql.discount.enums import SubscriptionEnum
from saleor.graphql.discount.types.vouchers import Voucher


def resolve_voucher(id, channel):
    sale = models.Voucher.objects.filter(id=id).first()
    return ChannelContext(node=sale, channel_slug=channel) if sale else None


def resolve_vouchers(info, channel_slug, **kwargs) -> ChannelQsContext:
    qs = models.Voucher.objects.all()
    if channel_slug:
        qs = qs.filter(channel_listings__channel__slug=channel_slug)

    # DEPRECATED: remove filtering by `query` argument when it's removed from the schema
    if query := kwargs.get("query"):
        qs = filter_voucher_search(qs, None, query)

    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


def resolve_sale(id, channel):
    sale = models.Sale.objects.filter(id=id).first()
    return ChannelContext(node=sale, channel_slug=channel) if sale else None


def resolve_sales(info, channel_slug, **kwargs) -> ChannelQsContext:
    qs = models.Sale.objects.all()
    if channel_slug:
        qs = qs.filter(channel_listings__channel__slug=channel_slug)

    # DEPRECATED: remove filtering by `query` argument when it's removed from the schema
    if query := kwargs.get("query"):
        qs = filter_sale_search(qs, None, query)

    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


# @cf::ornament.saleor.graphql.discount
def resolve_voucher_by_code(code, channel):
    voucher = models.Voucher.objects.filter(code=code).first()
    return ChannelContext(node=voucher, channel_slug=channel) if voucher else None


# @cf::ornament.saleor.graphql.discount
subscription_voucher_map = {
    SubscriptionEnum.ANNUAL.value: settings.SUBSCRIPTION_VAUCHER_ANNUAL,
    SubscriptionEnum.MONTHLY.value: settings.SUBSCRIPTION_VAUCHER_MONTHLY,
    SubscriptionEnum.PROMO.value: settings.SUBSCRIPTION_VAUCHER_PROMO,
    SubscriptionEnum.THREE_MONTH.value: settings.SUBSCRIPTION_VAUCHER_THREE_MONTH,
    SubscriptionEnum.UNKNOWN.value: settings.SUBSCRIPTION_VAUCHER_UNKNOWN,
}


# @cf::ornament.saleor.graphql.discount
def resolve_voucher_by_subscription_code(subscription_code: str, channel):
    voucher_node_id = subscription_voucher_map.get(
        subscription_code, SubscriptionEnum.MONTHLY.value
    )

    if not voucher_node_id:
        return None

    _, id = from_global_id_or_error(voucher_node_id, Voucher)
    voucher = models.Voucher.objects.filter(id=id).first()
    return ChannelContext(node=voucher, channel_slug=channel) if voucher else None
