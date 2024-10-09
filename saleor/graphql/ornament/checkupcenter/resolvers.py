import datetime
import logging

import graphene_django_optimizer as gql_optimizer
from django.conf import settings
from django.core.exceptions import ValidationError
from graphql_relay import from_global_id

from saleor.ornament.checkupcenter import CheckUpStateStatus, models
from saleor.ornament.utils.fsm_api import FSMApi

logger = logging.getLogger(__name__)


def resolve_checkup_categories(info, **kwargs):
    qs = models.CheckUpCategory.objects.all()
    return gql_optimizer.query(qs, info)


def resolve_checkup_product_categories(info, **kwargs):
    qs = models.CheckUpProductCategory.objects.all()
    return gql_optimizer.query(qs, info)


def resolve_checkups(info, **kwargs):
    user = info.context.user
    qs = (
        models.CheckUp.objects.filter(user=user)
        .active()
        .order_by("category_id", "is_personalized")
    )
    return gql_optimizer.query(qs, info)


def resolve_checkups_internal(info, **kwargs):
    pid = kwargs.get("pid")
    is_personalized = kwargs.get("is_personalized")
    qs = (
        models.CheckUp.objects.filter(profile_uuid=pid, is_personalized=is_personalized)
        .active()
        .order_by("category_id", "is_personalized")
    )
    return gql_optimizer.query(qs, info)


def resolve_checkup_states(info, **kwargs):
    if not kwargs.get("checkup_id"):
        return []

    user = info.context.user

    model, checkup_id = from_global_id(kwargs.get("checkup_id"))
    if not model == "CheckUp":
        raise ValidationError({"id": "ID value type is incorrect."})

    checkup = models.CheckUp.objects.filter(id=checkup_id).active().first()
    if not checkup:
        raise ValidationError({"id": "CheckUp is not found."})

    qs = models.CheckUpState.objects.filter(
        checkup__user=user, checkup=checkup
    ).order_by("-date_from")

    # @cf::ornament:CORE-2283
    date_most_filled_state_expiration = datetime.datetime.now() - datetime.timedelta(
        days=settings.CHECKUP_MOST_FILLED_STATE_EXPIRATION_DAYS
    )

    full = qs.filter(status=CheckUpStateStatus.FULL).first()
    partial = qs.filter(status=CheckUpStateStatus.PARTIAL).first()
    most_filled = qs.filter(
        status=CheckUpStateStatus.MOST_FILLED,
        date_to__gte=date_most_filled_state_expiration,
    ).first()

    return [i for i in (full, partial, most_filled) if i]


def resolve_checkup_states_internal(info, **kwargs):
    if not kwargs.get("checkup_id"):
        return []

    model, checkup_id = from_global_id(kwargs.get("checkup_id"))
    if not model == "CheckUp":
        raise ValidationError({"id": "ID value type is incorrect."})

    checkup = models.CheckUp.objects.filter(id=checkup_id).active().first()

    if not checkup:
        raise ValidationError({"id": "CheckUp is not found."})

    qs = models.CheckUpState.objects.filter(checkup=checkup).order_by("-date_from")

    # @cf::ornament:CORE-2283
    date_most_filled_state_expiration = datetime.datetime.now() - datetime.timedelta(
        days=settings.CHECKUP_MOST_FILLED_STATE_EXPIRATION_DAYS
    )

    full = qs.filter(status=CheckUpStateStatus.FULL).first()
    partial = qs.filter(status=CheckUpStateStatus.PARTIAL).first()
    most_filled = qs.filter(
        status=CheckUpStateStatus.MOST_FILLED,
        date_to__gte=date_most_filled_state_expiration,
    ).first()

    return [i for i in (full, partial, most_filled) if i]


def resolve_fsm_variable_sku_matches(info, **kwargs):
    if not kwargs.get("language_code"):
        return []

    return FSMApi.get_rules_transitions(kwargs["language_code"])
