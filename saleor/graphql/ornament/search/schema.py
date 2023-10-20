import graphene
from saleor.graphql.core.types.common import NonNullList

from saleor.permission.enums import ProductPermissions
from saleor.graphql.core.fields import PermissionsField

from .resolvers import resolve_search_products
from .types import SearchProduct


class SearchProductsQueries(graphene.ObjectType):
    search_products = PermissionsField(
        NonNullList(SearchProduct),
        description="All products with available channel listings",
        permissions=[ProductPermissions.MANAGE_PRODUCTS],
    )

    def resolve_search_products(self, info):
        return resolve_search_products(info)
