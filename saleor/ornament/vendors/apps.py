from django.apps import AppConfig

from saleor.ornament.geo.utils import download_geo_lite_db


class OrnamentVendorsConfig(AppConfig):
    name = "saleor.ornament.vendors"

    def ready(self) -> None:
        download_geo_lite_db()
        return super().ready()
