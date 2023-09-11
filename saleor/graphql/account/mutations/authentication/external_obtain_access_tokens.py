import graphene
from django.utils import timezone

from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_AUTH
from ....core.fields import JSONString
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import User


class ExternalObtainAccessTokens(BaseMutation):
    """Obtain external access tokens by a custom plugin."""

    token = graphene.String(description="The token, required to authenticate.")
    refresh_token = graphene.String(
        description="The refresh token, required to re-generate external access token."
    )
    csrf_token = graphene.String(
        description="CSRF token required to re-generate external access token."
    )
    user = graphene.Field(User, description="A user instance.")
    # @cf::ornament.geo
    current_channel = graphene.String(
        required=False, description="Current user channel"
    )

    class Arguments:
        plugin_id = graphene.String(
            description="The ID of the authentication plugin.", required=True
        )
        input = JSONString(
            required=True,
            description="The data required by plugin to create authentication data.",
        )

    class Meta:
        description = "Obtain external access tokens for user by custom plugin."
        doc_category = DOC_CATEGORY_AUTH
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input, plugin_id
    ):
        request = info.context
        manager = get_plugin_manager_promise(info.context).get()
        access_tokens_response = manager.external_obtain_access_tokens(
            plugin_id, input, request
        )
        setattr(info.context, "refresh_token", access_tokens_response.refresh_token)

        if access_tokens_response.user and access_tokens_response.user.id:
            info.context._cached_user = access_tokens_response.user
            access_tokens_response.user.last_login = timezone.now()
            access_tokens_response.user.save(update_fields=["last_login", "updated_at"])

        return cls(
            token=access_tokens_response.token,
            refresh_token=access_tokens_response.refresh_token,
            csrf_token=access_tokens_response.csrf_token,
            user=access_tokens_response.user,
            # @cf::ornament.geo
            current_channel=access_tokens_response.current_channel,
        )
