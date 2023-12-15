import graphene

from saleor.graphql.core.connection import (
    create_connection_slice,
    filter_connection_queryset,
)
from saleor.graphql.core.enums import LanguageCodeEnum
from saleor.graphql.core.fields import FilterConnectionField
from saleor.graphql.utils import login_required

from . import filters, mutations, resolvers, types


class CheckUpCenterQueries(graphene.ObjectType):
    checkup_categories = FilterConnectionField(
        types.CheckUpCategoryCountableConnection,
        description="List of the checkup categories.",
    )

    checkup_product_categories = FilterConnectionField(
        types.CheckUpProductCategoryCountableConnection,
        description="List of the checkup product categories.",
    )

    checkups = FilterConnectionField(
        types.CheckUpCountableConnection,
        description="List of the checkups.",
        filter=filters.CheckUpFilterInput(),
    )

    checkup_states = graphene.List(
        types.CheckUpState,
        description="List of the checkup states related to CheckUp.",
        checkup_id=graphene.Argument(graphene.ID, required=False),
    )

    fsm_variable_sku_matches = graphene.List(
        types.FsmVariableSkuMatches,
        description="List of fsm variable sku matches.",
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description="A language code.",
            required=True,
        ),
    )

    @login_required
    def resolve_checkup_categories(self, info, **kwargs):
        qs = resolvers.resolve_checkup_categories(info, **kwargs)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(
            qs, info, kwargs, types.CheckUpCategoryCountableConnection
        )

    @login_required
    def resolve_checkup_product_categories(self, info, **kwargs):
        qs = resolvers.resolve_checkup_product_categories(info, **kwargs)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(
            qs, info, kwargs, types.CheckUpProductCategoryCountableConnection
        )

    @login_required
    def resolve_checkups(self, info, **kwargs):
        qs = resolvers.resolve_checkups(info, **kwargs)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(
            qs, info, kwargs, types.CheckUpCountableConnection
        )

    @login_required
    def resolve_checkup_states(self, info, **kwargs):
        return resolvers.resolve_checkup_states(info, **kwargs)

    @login_required
    def resolve_fsm_variable_sku_matches(self, info, **kwargs):
        return resolvers.resolve_fsm_variable_sku_matches(info, **kwargs)


class CheckUpCenterMutations(graphene.ObjectType):
    checkup_matching_event_create = mutations.CheckUpMatchingEventCreate.Field()
    checkup_calculation_event_create = mutations.CheckUpCalculationEventCreate.Field()
    checkup_personalization_event_create = (
        mutations.CheckUpPersonalizationEventCreate.Field()
    )
    checkup_state_update_approvement = mutations.CheckUpStateUpdateApprovement.Field()
