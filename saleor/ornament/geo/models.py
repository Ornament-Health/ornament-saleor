from django.db import models
from django.utils import timezone

from saleor.utils.models import AutoNowUpdateFieldsMixin
from saleor.channel.models import Channel

MAPCOORDINATES_HELP_TEXT = (
    '<a href="http://www.mapcoordinates.net/ru" target="_blank">'
    "http://www.mapcoordinates.net/ru</a>"
)


class City(AutoNowUpdateFieldsMixin, models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    latitude = models.DecimalField(
        max_digits=18, decimal_places=15, help_text=MAPCOORDINATES_HELP_TEXT
    )
    longitude = models.DecimalField(
        max_digits=18, decimal_places=15, help_text=MAPCOORDINATES_HELP_TEXT
    )
    created = models.DateTimeField(default=timezone.now, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        db_table = "ornament_geo_city"

    def __str__(self):
        return self.name
