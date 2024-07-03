from datetime import datetime
import graphene

from saleor.graphql.core.fields import PermissionsField
from saleor.graphql.core.types import NonNullList
from saleor.graphql.core.scalars import Date
from saleor.permission.enums import InternalAPIPermissions

from .resolvers import (
    resolve_dardoc_disabled_dates,
    resolve_vendors,
    resolve_dardoc_area,
    resolve_dardoc_timeslots,
)
from .types import DarDocArea, DarDocTimeslots, Vendor


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
    dardoc_area = graphene.Field(
        DarDocArea,
        lat=graphene.Argument(graphene.Float, required=True),
        lng=graphene.Argument(graphene.Float, required=True),
        description="Check if DarDoc are is serviceable by latitude and longitude.",
    )
    dardoc_disabled_dates = graphene.Field(
        graphene.List(Date, required=True, description="DarDoc Disabled Date."),
        emirate=graphene.Argument(
            graphene.String, required=True, description="DarDoc Emirate."
        ),
        description="Check DarDoc's Emirate disabled dates.",
    )
    dardoc_timeslots = graphene.Field(
        graphene.List(DarDocTimeslots, required=True, description="DarDoc Timeslot."),
        dates=graphene.List(Date, required=True, description="DarDoc Date Timeslot."),
        emirate=graphene.Argument(
            graphene.String, required=True, description="DarDoc Emirate."
        ),
        description="DarDoc Timeslots.",
    )

    def resolve_vendor(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Vendor)

    def resolve_vendors(self, info, **kwargs):
        return resolve_vendors(info, **kwargs)

    def resolve_dardoc_area(self, info, lat: float, lng: float):
        return resolve_dardoc_area(info, lat, lng)

    def resolve_dardoc_disabled_dates(self, info, emirate: str):
        return resolve_dardoc_disabled_dates(info, emirate)

    def resolve_dardoc_timeslots(self, info, dates: list[datetime], emirate: str):
        return resolve_dardoc_timeslots(info, dates, emirate)
