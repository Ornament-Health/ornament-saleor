import logging
from typing import Optional

import geoip2.database
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from saleor.core.utils import get_client_ip
from saleor.ornament.geo.channel_utils import set_channel
from saleor.ornament.geo.models import City
from saleor.graphql.context import get_context_value

logger = logging.getLogger(__name__)


class GeoChannelMiddleware(MiddlewareMixin):
    """
    Middleware that detects a current request location info and
    automatically sets city and channel.
    """

    def process_request(self, request):
        city = None
        app_context = get_context_value(request)
        user = app_context.user

        if user and user.is_authenticated and user.city:
            city = user.city
        else:
            client_ip = get_client_ip(request)
            with geoip2.database.Reader(settings.GEO_LITE_DB_FILE_PATH) as reader:
                try:
                    geodata = reader.city(client_ip)

                    # if geodata and geodata.country.iso_code == "RU":
                    if geodata:
                        city: Optional[City] = (
                            City.objects.all()
                            .extra(
                                select={
                                    "distance": "6371 * acos("
                                    "  sin(radians({latitude})) * sin(radians(latitude)) +"
                                    "  cos(radians({latitude})) * cos(radians(latitude)) *"
                                    "  cos(radians({longitude}) - radians(longitude))"
                                    ")".format(
                                        latitude=geodata.location.latitude,
                                        longitude=geodata.location.longitude,
                                    )
                                }
                            )
                            .order_by("distance")
                            .first()
                        )
                except Exception as e:
                    logger.warning(f"GeoIP geodata failed. Error: {e}")
                    city = None

        if (
            city
            and user
            and user.is_authenticated
            and not user.city
            and not user.city_approved
        ):
            user.city = city
            user.save(update_fields=["city"])

        channel: str = city.channel.slug if city else settings.DEFAULT_CHANNEL_SLUG

        set_channel(channel)
