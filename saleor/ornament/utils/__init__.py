from typing import Optional

from saleor.core.exceptions import PermissionDenied
from saleor.ornament.geo.channel_utils import get_channel


def check_channel_access(channel_slug: Optional[str]) -> None:
    current_channel = get_channel()

    if channel_slug != current_channel:
        raise PermissionDenied(message=("You don't have access to this channel"))
