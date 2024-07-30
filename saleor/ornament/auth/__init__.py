from datetime import datetime
import logging
from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.core.validators import validate_email

from saleor.account.models import User
from saleor.core.exceptions import PermissionDenied
from saleor.core.jwt import create_access_token, create_refresh_token
from saleor.ornament.geo.channel_utils import get_channel
from saleor.ornament.geo.models import City
from saleor.plugins.base_plugin import BasePlugin, ExternalAccessTokens
from saleor.plugins.error_codes import PluginErrorCode

logger = logging.getLogger(__name__)


@dataclass
class OrnamentExternalAccessTokens(ExternalAccessTokens):
    current_channel: Optional[str] = None


class OrnamentSSOAuthBackend(BasePlugin):
    PLUGIN_ID = "saleor.ornament.auth.OrnamentSSOAuthBackend"
    PLUGIN_NAME = "Ornament SSO Auth"
    CONFIGURATION_PER_CHANNEL = False

    def _get_user_info_from_sso_api(self, token: str) -> tuple[str, str, Optional[str]]:
        try:
            response = requests.post(
                settings.ORNAMENT_SSO_VALIDATION_URL,
                json={"token": token},
                timeout=(5, 10),
            )
        except requests.RequestException as exc:
            logger.exception(exc)
            raise PermissionDenied()

        if response.status_code != 200:
            raise PermissionDenied()

        data = response.json()
        login, sso_id, country_code = (
            data.get("login"),
            data.get("sso_id"),
            data.get("country_code"),
        )

        if not login or not sso_id:
            raise PermissionDenied()

        try:
            validate_email(login)
            email = login
        except ValidationError:
            email = f"{sso_id}@orna.me"

        return sso_id, email, country_code

    def _get_city_for_country_code(self, country_code: str) -> Optional[City]:
        return (
            City.objects.select_related("channel")
            .filter(channel__default_country=country_code)
            .first()
        )

    def external_obtain_access_tokens(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> ExternalAccessTokens:
        token = data.get("token")

        if not token:
            msg = "Missing required field - token"
            raise ValidationError(
                {"code": ValidationError(msg, code=PluginErrorCode.NOT_FOUND.value)}
            )

        sso_id, email, country_code = self._get_user_info_from_sso_api(token)

        # @cf::ornament:CORE-2283
        fake_email = f"{sso_id}@orna.me-{int(datetime.now().timestamp())}"
        user, created = User.objects.get_or_create(
            sso_id=sso_id, defaults={User.USERNAME_FIELD: fake_email}
        )

        city = None
        if country_code:
            city = self._get_city_for_country_code(country_code)

        if created:
            user.set_unusable_password()
            user.save(update_fields=("password",))

        # Update email and change other_user's email if it exists,
        # sso-api is main source of email-sso_id pairs, so email from sso is preferable
        if user and user.email != email:
            other_user = User.objects.filter(email=email).first()
            if other_user:
                # This means the user's SSO has changed. This can happen when the user has
                # deleted himself in the main app and then created his account again with
                # the same email. To handle this situation we store the old user with an
                # unusable email which consists of `email + old_sso_id + timestamp` and
                # create a new user with the same email and new sso_id.
                other_user.email = (
                    f"{other_user.email}-{other_user.sso_id or 'no-sso-id'}-"
                    # @cf::ornament:CORE-2283
                    f"{int(datetime.now().timestamp())}"
                )
                other_user.save()
            user.email = email
            user.save(update_fields=("email",))

        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)

        if city and user.city != city:
            update_fields = ["city"]
            user.city = city

            if not user.city_approved and settings.AUTO_CITY_APPROVED:
                user.city_approved = True
                update_fields.append("city_approved")

            user.save(update_fields=update_fields)

        channel = user.city.channel.slug if user.city else get_channel()

        return OrnamentExternalAccessTokens(
            user=user,
            token=access_token,
            refresh_token=refresh_token,
            current_channel=channel,
        )
