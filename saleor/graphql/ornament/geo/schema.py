import graphene

from saleor.graphql.utils import login_required

from saleor.graphql.core.fields import FilterConnectionField
from saleor.graphql.core.connection import (
    create_connection_slice,
    filter_connection_queryset,
)
from .resolvers import resolve_cities
from .types import City, CityCountableConnection


class GeoQueries(graphene.ObjectType):
    city = graphene.Field(
        City,
        id=graphene.Argument(graphene.ID, required=True),
        description="Lookup a city by ID.",
    )
    cities = FilterConnectionField(
        CityCountableConnection, description="List of the cities."
    )

    @login_required()
    def resolve_city(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, City)

    @login_required()
    def resolve_cities(self, info, **kwargs):
        qs = resolve_cities(info, **kwargs)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, CityCountableConnection)
