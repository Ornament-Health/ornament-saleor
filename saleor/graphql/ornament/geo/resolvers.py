import graphene_django_optimizer as gql_optimizer

from saleor.ornament.geo.models import City
from saleor.ornament.vendors.models import Vendor


def resolve_cities(info, **kwargs):
    qs = City.objects.all()
    return gql_optimizer.query(qs, info)
