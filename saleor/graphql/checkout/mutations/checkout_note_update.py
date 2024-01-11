import graphene

from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_34
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.mutations import BaseMutation
from ...core.types import CheckoutError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Checkout
from .utils import get_checkout


# @cf:ornament.saleor.checkout
class CheckoutNoteUpdate(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="The checkout with the added gift card or voucher."
    )

    class Arguments:
        id = graphene.ID(
            description="The checkout's ID." + ADDED_IN_34,
            required=False,
        )
        note = graphene.String(description="Free form note for checkout")

    class Meta:
        description = "Updates a customer note for a checkout."
        doc_category = DOC_CATEGORY_CHECKOUT
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CHECKOUT_UPDATED,
                description="A checkout was updated.",
            )
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        id=None,
        note,
    ):
        checkout = get_checkout(cls, info, id=id)
        manager = get_plugin_manager_promise(info.context).get()
        checkout.note = note
        checkout.save(update_fields=["note"])
        cls.call_event(manager.checkout_updated, checkout)

        return CheckoutNoteUpdate(checkout=checkout)
