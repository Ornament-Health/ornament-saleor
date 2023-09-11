import graphene

from saleor.graphql.core.fields import PermissionsField
from saleor.graphql.core.types import NonNullList
from saleor.permission.enums import InternalAPIPermissions

from .resolvers import resolve_vendors
from .types import Vendor


class VendorsQueries(graphene.ObjectType):
    vendor = graphene.Field(
        Vendor,
        id=graphene.Argument(graphene.ID, required=True),
        description="Lookup a vendor by ID.",
    )
    vendors = PermissionsField(
        NonNullList(Vendor),
        description="List of all vendors.",
        permissions=[InternalAPIPermissions.MANAGE_USERS_VENDORS],
    )

    def resolve_vendor(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Vendor)

    def resolve_vendors(self, info, **kwargs):
        return resolve_vendors(info, **kwargs)
