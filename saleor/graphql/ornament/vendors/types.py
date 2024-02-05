import graphene

from saleor.graphql.core.types import ModelObjectType
from saleor.ornament.vendors import models as vendors_models


class Vendor(ModelObjectType[vendors_models.Vendor]):
    id = graphene.GlobalID(required=True)
    name = graphene.String(description="Vendor name.", required=True)
    slug = graphene.String(description="Vendor slug.", required=True)
    transaction_flow = graphene.String(
        description="Is transaction flow enabled for Vendor.", required=True
    )

    class Meta:
        model = vendors_models.Vendor
        interfaces = [graphene.relay.Node]
        fields = ["id", "name", "slug", "transaction_flow"]
        description = "Represents a Vendor."
