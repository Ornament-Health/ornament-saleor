import graphene

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

    class Meta:
        description = "Represents Deal Type for vendor."
