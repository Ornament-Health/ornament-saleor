import graphene

from saleor.graphql.core.scalars import Date
from saleor.graphql.core.types import ModelObjectType
from saleor.ornament.vendors import models as vendors_models


class Vendor(ModelObjectType[vendors_models.Vendor]):
    id = graphene.GlobalID(required=True)
    name = graphene.String(description="Vendor name.", required=True)
    slug = graphene.String(description="Vendor slug.", required=True)
    transaction_flow = graphene.Boolean(
        description="Is transaction flow enabled for Vendor.", required=True
    )

    class Meta:
        model = vendors_models.Vendor
        interfaces = [graphene.relay.Node]
        fields = ["id", "name", "slug", "transaction_flow"]
        description = "Represents a Vendor."


class VendorDealType(graphene.ObjectType):
    transaction_flow = graphene.Boolean(
        description="Vendor transaction flow", required=True
    )
    home_visit = graphene.Boolean(description="Vendor home visit", required=True)
    shipment = graphene.Boolean(description="Vendor shipment", required=True)
    map_location = graphene.Boolean(description="Vendor map location", required=True)
    visit_time = graphene.Boolean(description="Vendor visit time", required=True)

    class Meta:
        description = "Represents Deal Type for vendor."


class DarDocArea(graphene.ObjectType):
    is_serviceable = graphene.Boolean(
        description="Is DarDoc area serviceable", required=True
    )
    area = graphene.String(description="DarDoc area name", required=False)
    city = graphene.String(description="DarDoc area city", required=False)

    class Meta:
        description = "Represents DarDoc area."


class DarDocTimeslots(graphene.ObjectType):
    date = Date(
        description="Date of available timeslots",
        required=True,
    )
    timeslots = graphene.List(
        graphene.String,
        description="DarDoc timeslots (09:00 - 09:30AM)",
        required=True,
    )

    class Meta:
        description = "Represents DarDoc date timeslots."
