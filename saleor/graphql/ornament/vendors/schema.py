from datetime import datetime
import graphene

from saleor.graphql.core.fields import PermissionsField
from saleor.graphql.core.types import NonNullList
from saleor.graphql.core.scalars import Date
from saleor.permission.enums import InternalAPIPermissions

from .resolvers import (
    resolve_vendor_disabled_dates,
    resolve_vendors,
    resolve_vendor_area,
    resolve_vendor_timeslots,
)
from .types import VendorArea, VendorTimeslots, Vendor


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
    vendor_area = graphene.Field(
        VendorArea,
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned.",
            required=True,
        ),
        lat=graphene.Argument(graphene.Float, required=True),
        lng=graphene.Argument(graphene.Float, required=True),
        description="Check if Vendor area is serviceable by latitude and longitude.",
    )
    vendor_disabled_dates = graphene.Field(
        graphene.List(Date, required=True, description="Vendor Disabled Date."),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned.",
            required=True,
        ),
        area=graphene.Argument(
            graphene.String, required=True, description="Vendor Area."
        ),
        description="Check Vendor's Area disabled dates.",
    )
    vendor_timeslots = graphene.Field(
        graphene.List(VendorTimeslots, required=True, description="Vendor Timeslot."),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned.",
            required=True,
        ),
        dates=graphene.List(Date, required=True, description="Vendor Date Timeslot."),
        area=graphene.Argument(
            graphene.String, required=True, description="Vendor Area."
        ),
        description="Vendor Timeslots.",
    )

    def resolve_vendor(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Vendor)

    def resolve_vendors(self, info, **kwargs):
        return resolve_vendors(info, **kwargs)

    def resolve_vendor_area(self, info, channel: str, lat: float, lng: float):
        return resolve_vendor_area(info, channel, lat, lng)

    def resolve_vendor_disabled_dates(self, info, channel: str, area: str):
        return resolve_vendor_disabled_dates(info, channel, area)

    def resolve_vendor_timeslots(
        self, info, channel: str, dates: list[datetime], area: str
    ):
        return resolve_vendor_timeslots(info, channel, dates, area)
