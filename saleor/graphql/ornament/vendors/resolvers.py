from datetime import datetime
import graphene_django_optimizer as gql_optimizer

from saleor.graphql.ornament.vendors.types import VendorArea, VendorTimeslots
from saleor.ornament.services.dardoc_api import DarDocApi
from saleor.ornament.vendors.models import Vendor


def get_dardoc_area(lat: float, lng: float) -> VendorArea:
    dardoc_api = DarDocApi()
    is_area_serviceable = dardoc_api.is_area_serviceable(str(lat), str(lng))

    if not is_area_serviceable:
        return VendorArea(is_serviceable=False)

    return VendorArea(
        is_serviceable=is_area_serviceable.isServiceable,
        area=is_area_serviceable.area,
        city=is_area_serviceable.city,
    )


def get_dardoc_disabled_dates(area: str) -> list[datetime]:
    dardoc_api = DarDocApi()
    return dardoc_api.disabled_dates(area)


def get_dardoc_timeslots(dates: list[datetime], area: str) -> list[VendorTimeslots]:
    dardoc_api = DarDocApi()
    timeslots = dardoc_api.timeslots_by_dates(dates, area)
    return [VendorTimeslots(date=t.date, timeslots=t.timeslots) for t in timeslots]


# TODO consider moving this relation to DB with structured rules and 1+ channel-vendor model
channel_vendor_area_map = {"dardoc": get_dardoc_area}
channel_vendor_disabled_dates_map = {"dardoc": get_dardoc_disabled_dates}
channel_vendor_timeslots_map = {"dardoc": get_dardoc_timeslots}


def resolve_vendors(info, **kwargs):
    qs = Vendor.objects.all()
    return gql_optimizer.query(qs, info)


def resolve_vendor_area(info, channel: str, lat: float, lng: float):
    processor = channel_vendor_area_map.get(channel)

    if processor:
        return processor(lat, lng)

    return VendorArea(is_serviceable=False)


def resolve_vendor_disabled_dates(info, channel: str, area: str) -> list[datetime]:
    processor = channel_vendor_disabled_dates_map.get(channel)

    if processor:
        return processor(area)

    return []


def resolve_vendor_timeslots(
    info, channel: str, dates: list[datetime], area: str
) -> list[VendorTimeslots]:
    processor = channel_vendor_timeslots_map.get(channel)

    if processor:
        return processor(dates, area)

    return []
