# @cf::ornament.vendors
from enum import Enum

import graphene
from django.core.exceptions import ValidationError

from saleor.account import models
from saleor.account.error_codes import AccountErrorCode
from saleor.graphql.account.types import User
from saleor.graphql.core import ResolveInfo
from saleor.graphql.core.mutations import BaseMutation
from saleor.graphql.core.scalars import UUID
from saleor.graphql.core.types.common import Error
from saleor.graphql.ornament.vendors import types
from saleor.graphql.plugins.dataloaders import get_plugin_manager_promise
from saleor.permission.enums import InternalAPIPermissions


class SetVendorErrorCodes(Enum):
    SET_VENDOR_ERROR = "set_vendor_error"


SetVendorErrorCode = graphene.Enum.from_enum(SetVendorErrorCodes)


class SetVendorError(Error):
    code = SetVendorErrorCode(description="Set account vendor error", required=True)

    class Meta:
        description = "Represents errors in set vendor mutation"
        doc_category = "SetVendor"


class SetVendor(BaseMutation):
    user = graphene.Field(User, description="A user instance with new vendor.")

    class Arguments:
        vendor = graphene.ID(
            description="Vendor ID",
            name="vendor",
            required=True,
        )
        sso_id = UUID(description="SSO UUID.", required=True)

    class Meta:
        model = models.User
        description = "Sets the user's vendor to apply rules"
        error_type_class = SetVendorError
        error_type_field = "account_errors"
        object_type = types.Vendor
        permissions = (InternalAPIPermissions.MANAGE_USERS_VENDORS,)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, vendor, sso_id):
        vendor = cls.get_node_or_error(info, vendor, only_type=types.Vendor)
        user = models.User.objects.filter(sso_id=sso_id).first()

        if not user:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "User with this sso_id doesn't exist",
                        code=AccountErrorCode.NOT_FOUND.value,
                    )
                }
            )

        if user.vendor != vendor:
            user.vendor = vendor
            user.save(update_fields=["vendor"])

        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.customer_updated, user)

        return cls(user=user)
