from datetime import date, datetime
import graphene_django_optimizer as gql_optimizer

from saleor.graphql.ornament.vendors.types import DarDocArea, DarDocTimeslots
from saleor.ornament.services.dardoc_api import DarDocApi
from saleor.ornament.vendors.models import Vendor


def resolve_vendors(info, **kwargs):
    qs = Vendor.objects.all()
    return gql_optimizer.query(qs, info)


def resolve_dardoc_area(info, lat: float, lng: float):
    dardoc_api = DarDocApi()
    is_area_serviceable = dardoc_api.is_area_serviceable(str(lat), str(lng))

    if not is_area_serviceable:
        return DarDocArea(is_serviceable=False)

    return DarDocArea(
        is_serviceable=is_area_serviceable.isServiceable,
        area=is_area_serviceable.area,
        city=is_area_serviceable.city,
    )


def resolve_dardoc_disabled_dates(info, emirate: str) -> list[datetime]:
    dardoc_api = DarDocApi()
    return dardoc_api.disabled_dates(emirate)


def resolve_dardoc_timeslots(info, dates, emirate) -> list[DarDocTimeslots]:
    dardoc_api = DarDocApi()
    timeslots = dardoc_api.timeslots_by_dates(dates, emirate)
    return [DarDocTimeslots(date=t.date, timeslots=t.timeslots) for t in timeslots]
