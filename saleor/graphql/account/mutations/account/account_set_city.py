# @cf::ornament.geo
from enum import Enum
from typing import cast

import graphene

from saleor.account import models
from saleor.graphql.account.types import User
from saleor.graphql.core.mutations import BaseMutation
from saleor.graphql.core.types.common import Error
from saleor.graphql.core import ResolveInfo
from saleor.graphql.ornament.geo import types
from saleor.graphql.plugins.dataloaders import get_plugin_manager_promise


class SetCityErrorCodes(Enum):
    SET_CITY_ERROR = "set_city_error"


SetCityErrorCode = graphene.Enum.from_enum(SetCityErrorCodes)


class SetCityError(Error):
    code = SetCityErrorCode(description="Set account city error", required=True)

    class Meta:
        description = "Represents errors in set city mutation"
        doc_category = "SetCity"


class SetCity(BaseMutation):
    user = graphene.Field(User, description="A user instance with new city.")

    class Arguments:
        city = graphene.ID(
            description="City ID of user's current location.",
            name="city",
            required=True,
        )

    class Meta:
        model = models.User
        description = "Sets the user's city to apply connected channel"
        error_type_class = SetCityError
        error_type_field = "account_errors"
        object_type = types.City

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, city):
        city = cls.get_node_or_error(info, city, only_type=types.City)
        user = info.context.user
        user = cast(models.User, user)
        user.city = city
        user.city_approved = True
        user.save(update_fields=["city", "city_approved", "updated_at"])

        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.customer_updated, user)

        return cls(user=user)
