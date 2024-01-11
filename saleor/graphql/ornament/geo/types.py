import graphene

from saleor.graphql.core.types import ModelObjectType
from saleor.graphql.core.connection import CountableConnection
from saleor.ornament.geo import models as geo_models


class City(ModelObjectType[geo_models.City]):
    id = graphene.GlobalID(required=True)
    name = graphene.String(description="City name.", required=True)
    latitude = graphene.Float(description="City point latitude.")
    longitude = graphene.Float(description="City point latitude.")

    class Meta:
        model = geo_models.City
        interfaces = [graphene.relay.Node]
        fields = ["name", "latitude", "longitude"]
        description = "Represents a City."


class CityCountableConnection(CountableConnection):
    class Meta:
        doc_category = "Geo"
        node = City
