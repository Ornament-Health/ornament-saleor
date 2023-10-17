import graphene


from ...permission.enums import DiscountPermissions
from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import DEPRECATED_IN_3X_INPUT
from ..core.doc_category import DOC_CATEGORY_DISCOUNTS
from ..core.fields import FilterConnectionField, PermissionsField
from ..core.types import FilterInputObjectType
from ..core.utils import from_global_id_or_error
from ..translations.mutations import SaleTranslate, VoucherTranslate
from .filters import SaleFilter, VoucherFilter
from .mutations import (
    SaleAddCatalogues,
    SaleChannelListingUpdate,
    SaleCreate,
    SaleDelete,
    SaleRemoveCatalogues,
    SaleUpdate,
    VoucherAddCatalogues,
    VoucherChannelListingUpdate,
    VoucherCreate,
    VoucherDelete,
    VoucherRemoveCatalogues,
    VoucherUpdate,
)
from .mutations.bulk_mutations import SaleBulkDelete, VoucherBulkDelete
from .resolvers import (
    resolve_sale,
    resolve_sales,
    resolve_voucher,
    resolve_vouchers,
    resolve_voucher_by_code,
    resolve_voucher_by_subscription_code,
)
from .sorters import SaleSortingInput, VoucherSortingInput
from .types import Sale, SaleCountableConnection, Voucher, VoucherCountableConnection

# @cf::ornament.saleor.graphql.discount
from saleor.graphql.discount.enums import SubscriptionEnum

# @cf::ornament.saleor.graphql.discount
SubscriptionEnumType = graphene.Enum.from_enum(SubscriptionEnum)


class VoucherFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS
        filterset_class = VoucherFilter


class SaleFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS
        filterset_class = SaleFilter


class DiscountQueries(graphene.ObjectType):
    sale = PermissionsField(
        Sale,
        id=graphene.Argument(graphene.ID, description="ID of the sale.", required=True),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a sale by ID.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
        doc_category=DOC_CATEGORY_DISCOUNTS,
    )
    sales = FilterConnectionField(
        SaleCountableConnection,
        filter=SaleFilterInput(description="Filtering options for sales."),
        sort_by=SaleSortingInput(description="Sort sales."),
        query=graphene.String(
            description=(
                "Search sales by name, value or type. "
                f"{DEPRECATED_IN_3X_INPUT} Use `filter.search` input instead."
            )
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="List of the shop's sales.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
        doc_category=DOC_CATEGORY_DISCOUNTS,
    )
    voucher = PermissionsField(
        Voucher,
        id=graphene.Argument(
            graphene.ID, description="ID of the voucher.", required=True
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a voucher by ID.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
        doc_category=DOC_CATEGORY_DISCOUNTS,
    )
    vouchers = FilterConnectionField(
        VoucherCountableConnection,
        filter=VoucherFilterInput(description="Filtering options for vouchers."),
        sort_by=VoucherSortingInput(description="Sort voucher."),
        query=graphene.String(
            description=(
                "Search vouchers by name or code. "
                f"{DEPRECATED_IN_3X_INPUT} Use `filter.search` input instead."
            )
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="List of the shop's vouchers.",
        permissions=[
            DiscountPermissions.MANAGE_DISCOUNTS,
        ],
        doc_category=DOC_CATEGORY_DISCOUNTS,
    )
    # @cf::ornament.saleor.graphql.discount
    voucher_by_code = graphene.Field(
        Voucher,
        code=graphene.Argument(graphene.String, required=True),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Lookup a voucher by Code.",
    )
    # @cf::ornament.saleor.graphql.discount
    voucher_by_subscription_code = graphene.Field(
        Voucher,
        subscription_code=SubscriptionEnumType(description="App subscription code"),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Lookup a voucher by app subscription code.",
    )

    @staticmethod
    def resolve_sale(_root, _info, *, id, channel=None):
        _, id = from_global_id_or_error(id, Sale)
        return resolve_sale(id, channel)

    @staticmethod
    def resolve_sales(_root, info: ResolveInfo, *, channel=None, **kwargs):
        qs = resolve_sales(info, channel_slug=channel, **kwargs)
        kwargs["channel"] = channel
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, SaleCountableConnection)

    @staticmethod
    def resolve_voucher(_root, _info: ResolveInfo, *, id, channel=None):
        _, id = from_global_id_or_error(id, Voucher)
        return resolve_voucher(id, channel)

    @staticmethod
    def resolve_vouchers(_root, info: ResolveInfo, *, channel=None, **kwargs):
        qs = resolve_vouchers(info, channel_slug=channel, **kwargs)
        kwargs["channel"] = channel
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, VoucherCountableConnection)

    # @cf::ornament.saleor.graphql.discount
    @staticmethod
    def resolve_voucher_by_code(_root, info: ResolveInfo, *, code, channel=None):
        return resolve_voucher_by_code(code, channel)

    # @cf::ornament.saleor.graphql.discount
    @staticmethod
    def resolve_voucher_by_subscription_code(
        _root, info: ResolveInfo, *, subscription_code: str, channel=None
    ):
        return resolve_voucher_by_subscription_code(subscription_code, channel)


class DiscountMutations(graphene.ObjectType):
    sale_create = SaleCreate.Field()
    sale_delete = SaleDelete.Field()
    sale_bulk_delete = SaleBulkDelete.Field()
    sale_update = SaleUpdate.Field()
    sale_catalogues_add = SaleAddCatalogues.Field()
    sale_catalogues_remove = SaleRemoveCatalogues.Field()
    sale_translate = SaleTranslate.Field()
    sale_channel_listing_update = SaleChannelListingUpdate.Field()

    voucher_create = VoucherCreate.Field()
    voucher_delete = VoucherDelete.Field()
    voucher_bulk_delete = VoucherBulkDelete.Field()
    voucher_update = VoucherUpdate.Field()
    voucher_catalogues_add = VoucherAddCatalogues.Field()
    voucher_catalogues_remove = VoucherRemoveCatalogues.Field()
    voucher_translate = VoucherTranslate.Field()
    voucher_channel_listing_update = VoucherChannelListingUpdate.Field()
