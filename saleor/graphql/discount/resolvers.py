from django.db.models import Exists, OuterRef, QuerySet
from django.conf import settings

from ...channel.models import Channel
from ...discount import models
from ..channel import ChannelContext, ChannelQsContext
from ..core.context import get_database_connection_name
from .filters import filter_sale_search, filter_voucher_search

# @cf::ornament.saleor.graphql.discount
from saleor.graphql.core.utils import from_global_id_or_error
from saleor.graphql.discount.enums import SubscriptionEnum
from saleor.graphql.discount.types.vouchers import Voucher


def resolve_voucher(info, id, channel):
    sale = (
        models.Voucher.objects.using(get_database_connection_name(info.context))
        .filter(id=id)
        .first()
    )
    return ChannelContext(node=sale, channel_slug=channel) if sale else None


def resolve_vouchers(info, channel_slug, **kwargs) -> ChannelQsContext:
    qs = models.Voucher.objects.using(get_database_connection_name(info.context)).all()
    if channel_slug:
        qs = qs.filter(channel_listings__channel__slug=channel_slug)

    # DEPRECATED: remove filtering by `query` argument when it's removed from the schema
    if query := kwargs.get("query"):
        qs = filter_voucher_search(qs, None, query)

    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


def resolve_sale(info, id, channel):
    promotion = (
        models.Promotion.objects.using(get_database_connection_name(info.context))
        .filter(old_sale_id=id)
        .first()
    )
    return ChannelContext(node=promotion, channel_slug=channel) if promotion else None


def resolve_sales(info, channel_slug, **kwargs) -> ChannelQsContext:
    connection_name = get_database_connection_name(info.context)
    qs = models.Promotion.objects.using(connection_name).filter(
        old_sale_id__isnull=False
    )
    if channel_slug:
        channel = Channel.objects.using(connection_name).filter(slug=channel_slug)
        rule_channel = models.PromotionRule.channels.through.objects.using(
            connection_name
        ).filter(channel__in=channel)
        rules = models.PromotionRule.objects.using(connection_name).filter(
            Exists(rule_channel.filter(promotionrule_id=OuterRef("id")))
        )
        qs = qs.filter(Exists(rules.filter(promotion_id=OuterRef("pk"))))

    # DEPRECATED: remove filtering by `query` argument when it's removed from the schema
    if query := kwargs.get("query"):
        qs = filter_sale_search(qs, None, query)

    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


def resolve_promotion(info, id):
    return (
        models.Promotion.objects.using(get_database_connection_name(info.context))
        .filter(id=id)
        .first()
    )


def resolve_promotions(info) -> QuerySet:
    return models.Promotion.objects.using(
        get_database_connection_name(info.context)
    ).all()


# @cf::ornament.saleor.graphql.discount
def resolve_voucher_by_code(code, channel):
    voucher = models.Voucher.objects.filter(code=code).first()
    return ChannelContext(node=voucher, channel_slug=channel) if voucher else None


# @cf::ornament.saleor.graphql.discount
subscription_voucher_map = {
    SubscriptionEnum.WEEKLY.value: settings.SUBSCRIPTION_VOUCHER_WEEKLY,
    SubscriptionEnum.MONTHLY.value: settings.SUBSCRIPTION_VOUCHER_MONTHLY,
    SubscriptionEnum.ANNUAL.value: settings.SUBSCRIPTION_VOUCHER_ANNUAL,
    SubscriptionEnum.PROMO.value: settings.SUBSCRIPTION_VOUCHER_PROMO,
    SubscriptionEnum.THREE_MONTH.value: settings.SUBSCRIPTION_VOUCHER_THREE_MONTH,
    SubscriptionEnum.UNKNOWN.value: settings.SUBSCRIPTION_VOUCHER_UNKNOWN,
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
