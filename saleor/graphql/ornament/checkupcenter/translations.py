import graphene

from saleor.graphql.translations.types import BaseTranslationType
import saleor.ornament.checkupcenter.models as checkupcenter_models


class CheckUpProductCategoryTranslation(BaseTranslationType):
    id = graphene.GlobalID(
        required=True, description="The ID of the CheckUpProduct translation."
    )
    name = graphene.String(description="Translated CheckUpProduct name.")

    class Meta:
        model = checkupcenter_models.CheckUpProductCategoryTranslation
        interfaces = [graphene.relay.Node]
        # only_fields = ["id", "name"]


class CheckUpCategoryTranslation(
    BaseTranslationType[checkupcenter_models.CheckUpCategoryTranslation]
):
    id = graphene.GlobalID(
        required=True, description="The ID of the CheckUpCategory translation."
    )
    name = graphene.String(description="Translated CheckUpCategory name.")
    description = graphene.String(description="Translated CheckUpCategory description.")

    class Meta:
        model = checkupcenter_models.CheckUpCategoryTranslation
        interfaces = [graphene.relay.Node]
        # only_fields = ["id", "name", "description"]


class CheckUpTemplateTranslation(BaseTranslationType):
    id = graphene.GlobalID(
        required=True, description="The ID of the CheckUpTemplate translation."
    )
    name = graphene.String(description="Translated CheckUpTemplate name.")
    description = graphene.String(description="Translated CheckUpTemplate description.")

    class Meta:
        model = checkupcenter_models.CheckUpTemplateTranslation
        interfaces = [graphene.relay.Node]
        # only_fields = ["id", "name", "description"]
