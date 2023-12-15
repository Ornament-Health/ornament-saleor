import graphene_django_optimizer as gql_optimizer

from saleor.ornament.vendors.models import Vendor


def resolve_vendors(info, **kwargs):
    qs = Vendor.objects.all()
    return gql_optimizer.query(qs, info)
