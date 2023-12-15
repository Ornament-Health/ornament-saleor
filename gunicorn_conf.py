from saleor.ornament.geo.utils import download_geo_lite_db


def on_starting(server):
    """Executes code before the master process is initialized"""
    download_geo_lite_db()


bind = ":8000"
worker_class = "saleor.asgi.gunicorn_worker.UvicornWorker"
workers = 2
