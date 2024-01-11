from enum import Enum

import graphene
from django.core.exceptions import ValidationError

from saleor.account.models import User
from saleor.graphql.core.mutations import BaseMutation
from saleor.graphql.core.scalars import UUID
from saleor.graphql.core.types.common import AccountError, Error
from saleor.ornament.checkupcenter import CheckUpStateStatus, tasks
from saleor.permission.enums import InternalAPIPermissions

from . import enums, types


class CheckupErrorCodes(Enum):
    CHECKUP_ERROR = "checkup_error"


CheckupErrorCode = graphene.Enum.from_enum(CheckupErrorCodes)


class CheckupError(Error):
    code = CheckupErrorCode(description="The error code.", required=True)

    class Meta:
        description = "Represents errors in account mutations."
        doc_category = "Checkup"


class CheckUpMatchingEventCreate(BaseMutation):
    status = graphene.Boolean(description="Status of event emitting.")

    class Arguments:
        sso_id = UUID(description="SSO UUID.", required=True)
        profile_id = UUID(description="Profile UUID.", required=True)
        sex = enums.CheckUpSexEnum(description="Profile sex.", required=True)
        age = graphene.Int(description="Profile age.", required=True)

    class Meta:
        description = "Emit CheckUp matching event."
        doc_category = "Checkup"
        error_type_class = CheckupError
        error_type_field = "checkup_errors"
        permissions = (InternalAPIPermissions.MANAGE_CHECKUPS,)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = User.objects.filter(is_active=True, sso_id=data["sso_id"]).first()
        status = False
        if user:
            status = True
            tasks.handle_checkup_matching_event_task.delay(
                user.id, data["profile_id"], data["sex"], data["age"]
            )

        return CheckUpMatchingEventCreate(status=status)


class CheckUpCalculationEventCreate(BaseMutation):
    status = graphene.Boolean(description="Status of event emitting.")

    class Arguments:
        sso_id = UUID(description="SSO UUID.", required=True)
        profile_id = UUID(description="Profile UUID.", required=True)

    class Meta:
        description = "Emit CheckUp calculation event."
        doc_category = "Checkup"
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (InternalAPIPermissions.MANAGE_CHECKUPS,)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = User.objects.filter(is_active=True, sso_id=data["sso_id"]).first()
        status = False
        if user:
            status = True
            tasks.handle_checkup_calculation_event_task.delay(
                user.id, data["profile_id"]
            )

        return CheckUpCalculationEventCreate(status=status)


class CheckUpStateUpdateApprovement(BaseMutation):
    checkup_id = graphene.ID(description="CheckUp ID.")
    approvement = enums.CheckUpStateApprovement(
        description="CheckUp partial state approvement."
    )

    class Arguments:
        checkup_id = graphene.ID(description="CheckUp ID.", required=True)
        approvement = enums.CheckUpStateApprovement(
            description="CheckUp partial state approvement.", required=True
        )

    class Meta:
        description = "Update status in checkup's partial state."
        doc_category = "Checkup"
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        checkup_id = data["checkup_id"]
        approvement = data["approvement"]

        user = info.context.user
        checkup = graphene.Node.get_node_from_global_id(info, checkup_id, types.CheckUp)
        if checkup is None:
            raise ValidationError({"checkup_id": "CheckUp is not found."})
        elif not checkup.user_id == user.id:
            raise ValidationError({"checkup_id": "User is not owner of the CheckUp."})

        state = checkup.checkup_states.filter(status=CheckUpStateStatus.PARTIAL).first()
        if not state:
            raise ValidationError({"checkup_id": "CheckUp has no partial state."})

        state.approvement = approvement
        state.save()

        return CheckUpStateUpdateApprovement(
            checkup_id=checkup_id, approvement=approvement
        )


class SKUMatch(graphene.InputObjectType):
    sku = graphene.String(required=True, description="Personalized SKU value.")
    rules = graphene.List(
        graphene.Int,
        required=True,
        description="List of ids of matched rules.",
    )
    actions = graphene.List(
        graphene.String,
        required=True,
        description="List of actions of matched rules.",
    )


class CheckUpPersonalizationEventCreate(BaseMutation):
    status = graphene.Boolean(description="Status of event emitting.")

    class Arguments:
        sso_id = UUID(description="SSO UUID.", required=True)
        profile_id = UUID(description="Profile UUID.", required=True)
        matches = graphene.List(
            SKUMatch,
            required=False,
            description="List of SKU-rule matches.",
        )

    class Meta:
        description = "Emit CheckUp personalization event."
        doc_category = "Checkup"
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (InternalAPIPermissions.MANAGE_CHECKUPS,)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = User.objects.filter(is_active=True, sso_id=data["sso_id"]).first()
        status = False
        if user:
            status = True
            tasks.handle_checkup_personalization_event_task.delay(
                user.id, data["profile_id"], data.get("matches", [])
            )

        return CheckUpPersonalizationEventCreate(status=status)
