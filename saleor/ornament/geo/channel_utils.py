"""User channel helper functions."""
from threading import local
from typing import Optional

from saleor.channel.models import Channel


# User channel is cached directly in a local storage
# it's available in a local thread
_active = local()


def set_channel(channel_slug: str) -> None:
    _active.channel = channel_slug


def get_channel() -> Optional[str]:
    return getattr(_active, "channel", None)


def deactivate():
    """
    Uninstall active channel
    """
    _active.channel = None
    del _active.channel
