import datetime
from typing import Optional

import graphene
import graphene_django_optimizer as gql_optimizer
from django.conf import settings
from django.db.models import Prefetch
from django.utils import timezone

from saleor.graphql.channel import ChannelContext
from saleor.graphql.ornament.checkupcenter.translations import (
    CheckUpCategoryTranslation,
    CheckUpProductCategoryTranslation,
    CheckUpTemplateTranslation,
)
from saleor.graphql.core.connection import create_connection_slice
from saleor.graphql.core.connection import CountableConnection
from saleor.graphql.core.enums import LanguageCodeEnum
from saleor.graphql.core.types import ModelObjectType
from saleor.graphql.core.types.common import NonNullList
from saleor.graphql.product.dataloaders.products import ProductByIdLoader
from saleor.graphql.product.types import Product
from saleor.graphql.utils import get_user_or_app_from_context
from saleor.ornament.checkupcenter import CheckUpStateStatus, models

from . import enums


def prefetch_checkup_products(info, *args, **kwargs):
    requestor = get_user_or_app_from_context(info.context)
    qs = models.CheckUpProduct.objects.annotate_available_by_rules(requestor)

    return Prefetch(
        "checkup_products",
        queryset=gql_optimizer.query(qs, info),
        to_attr="prefetched_products",
    )


def resolve_translation(instance, _info, language_code):
    """Get translation object from instance based on language code."""
    return instance.translations.filter(language_code=language_code).first()


class CheckUpCategory(ModelObjectType[models.CheckUpCategory]):
    id = graphene.GlobalID(required=True)
    name = graphene.String(description="Checkup category name.", required=True)
    description = graphene.String(description="Category description", required=True)
    ext_id = graphene.String(description="External id.", required=True)
    translation = graphene.Field(
        CheckUpCategoryTranslation,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description="A language code to return the translation for.",
            required=True,
        ),
        description=(
            "Returns translated CheckUpCategory fields for the given language code."
        ),
        resolver=resolve_translation,
    )

    class Meta:
        model = models.CheckUpCategory
        interfaces = [graphene.relay.Node]
        fields = ["id", "name", "description", "emoji", "ext_id", "translation"]
        description = "Represents a CheckUpCategory"


class CheckUpCategoryCountableConnection(CountableConnection):
    class Meta:
        doc_category = "Checkup"
        node = CheckUpCategory


class CheckUpProductCategory(ModelObjectType[models.CheckUpProductCategory]):
    id = graphene.GlobalID(required=True)
    name = graphene.String(description="Checkup product category name.", required=False)
    human_part_id = graphene.Int(description="Human part id.", required=False)
    translation = graphene.Field(
        CheckUpProductCategoryTranslation,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description="A language code to return the translation for.",
            required=True,
        ),
        description=(
            "Returns translated CheckUpProductCategory fields for the given language code."
        ),
        resolver=resolve_translation,
    )

    class Meta:
        model = models.CheckUpProductCategory
        interfaces = [graphene.relay.Node]
        fields = ["id", "name", "human_part_id", "translation"]
        description = "Represents a CheckUpProductCategory"


class CheckUpProductCategoryCountableConnection(CountableConnection):
    class Meta:
        doc_category = "Checkup"
        node = CheckUpProductCategory


class CheckUpProductMetaItem(graphene.ObjectType):
    biomarkers = graphene.List(graphene.Int, required=True, description="Biomarker ids")
    medical_exams = graphene.List(
        graphene.Int, required=True, description="Medical Exams ids"
    )
    rules = graphene.List(graphene.Int, required=True, description="Personalized Rules")


class CheckUpProduct(ModelObjectType[models.CheckUpProduct]):
    id = graphene.GlobalID(required=True)
    product = graphene.Field(Product, description="Related product.")
    meta = graphene.Field(
        CheckUpProductMetaItem,
        required=True,
        description=("List of checkup meta items."),
    )
    is_available = graphene.Boolean(
        description="Whether it is in stock in current local provider."
    )

    class Meta:
        model = models.CheckUpProduct
        fields = ["id", "product", "meta", "is_available"]
        interfaces = [graphene.relay.Node]
        description = "Represents a CheckUpProduct"

    @staticmethod
    def resolve_product(root, info):
        product = ProductByIdLoader(info.context).load(root.product_id)
        return product.then(
            lambda product: ChannelContext(node=product, channel_slug=None)
        )

    @staticmethod
    def resolve_meta(root, info):
        root_meta = root.meta.get("ornament", {})

        return CheckUpProductMetaItem(
            root_meta.get("biomarkers", []),
            root_meta.get("medical_exams", []),
            root_meta.get("rules", []),
        )

    @staticmethod
    def resolve_is_available(root: models.CheckUpProduct, info):
        is_available = getattr(root, "is_available_in_local_provider", None)
        if is_available is None:
            # annotate_available_by_rules was not called on queryset
            requestor = get_user_or_app_from_context(info.context)
            is_available = (
                type(root)
                .objects.filter(id=root.id)
                .annotate_available_by_rules(requestor)
                .values_list("is_available_in_local_provider", flat=True)
                .first()
            )
        return is_available


class CheckUpProductCountableConnection(CountableConnection):
    class Meta:
        doc_category = "Checkup"
        node = CheckUpProduct


class CheckUpTemplate(ModelObjectType[models.CheckUpTemplate]):
    id = graphene.GlobalID(required=True)
    name = graphene.String(description="Checkup template name.", required=True)
    translation = graphene.Field(
        CheckUpTemplateTranslation,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description="A language code to return the translation for.",
            required=True,
        ),
        description=(
            "Returns translated CheckUpTemplate fields for the given language code."
        ),
        resolver=resolve_translation,
    )

    class Meta:
        model = models.CheckUpTemplate
        fields = ["name", "description", "translation"]
        description = "Represents a CheckUpTemplate"


class CheckUp(ModelObjectType[models.CheckUp]):
    id = graphene.GlobalID(required=True)
    template = gql_optimizer.field(
        graphene.Field(
            CheckUpTemplate, description="CheckUpTemplate related to CheckUp."
        )
    )
    category = gql_optimizer.field(
        graphene.Field(
            CheckUpCategory, description="CheckUpCategory related to CheckUp."
        )
    )

    products = gql_optimizer.field(
        NonNullList(
            CheckUpProduct,
            description="List of checkup products in the checkup.",
        ),
        prefetch_related=prefetch_checkup_products,
    )

    is_personalized = graphene.Boolean(description="Is checkup personalized or not")

    class Meta:
        model = models.CheckUp
        fields = ["id", "template", "category", "products", "is_personalized"]
        interfaces = [graphene.relay.Node]
        description = "Represents a CheckUp"

    @staticmethod
    def resolve_products(root: models.CheckUp, info, **kwargs):
        # If the category has no children, we use the prefetched data.
        if hasattr(root, "prefetched_products"):
            return root.prefetched_products

        # Otherwise we want to include products from child categories which
        # requires performing additional logic.
        requestor = get_user_or_app_from_context(info.context)
        qs = models.CheckUpProduct.objects.annotate_available_by_rules(requestor)

        return create_connection_slice(
            qs, info, kwargs, CheckUpProductCountableConnection
        )


class CheckUpCountableConnection(CountableConnection):
    class Meta:
        doc_category = "Checkup"
        node = CheckUp


class CheckUpStateMetaItemStatus(graphene.ObjectType):
    id = graphene.Int()
    status = graphene.Boolean()


class CheckUpStateMetaItemBase(graphene.ObjectType):
    date_from = graphene.DateTime()
    date_to = graphene.DateTime()
    biomarkers = graphene.List(CheckUpStateMetaItemStatus)
    medical_exams = graphene.List(CheckUpStateMetaItemStatus)
    progress = graphene.Float()


class CheckUpStateMetaItemSKU(CheckUpStateMetaItemBase):
    id = graphene.String(required=True)


class CheckUpStateMetaItemTotal(CheckUpStateMetaItemBase):
    pass


class CheckUpStateMetaGroupsSku(graphene.ObjectType):
    id = graphene.String(required=True)
    progress = graphene.Float()


class CheckUpStateMetaGroup(graphene.ObjectType):
    name = graphene.String(required=True)
    progress = graphene.Float()
    skus = graphene.List(CheckUpStateMetaGroupsSku)


class CheckUpStateMetaItem(graphene.ObjectType):
    sku = graphene.List(CheckUpStateMetaItemSKU)
    total = graphene.Field(CheckUpStateMetaItemTotal)
    groups = graphene.List(CheckUpStateMetaGroup)


class CheckUpState(ModelObjectType[models.CheckUpState]):
    id = graphene.GlobalID(required=True)
    checkup_id = graphene.Field(
        graphene.ID, description="CheckUp id related to CheckUpState."
    )
    meta = graphene.Field(
        CheckUpStateMetaItem,
        required=True,
        description="List of publicly stored metadata namespaces.",
    )
    approvement = enums.CheckUpStateApprovement(
        description="CheckUp state approvement value."
    )
    status = graphene.String(description="CheckUp state status.")
    date_from = graphene.DateTime(description="CheckUp state date from.")
    date_to = graphene.DateTime(description="CheckUp state date to.")

    class Meta:
        model = models.CheckUpState
        fields = [
            "id",
            "checkup_id",
            "date_from",
            "date_to",
            "status",
            "approvement",
            "meta",
        ]
        interfaces = [graphene.relay.Node]
        description = "Represents a CheckUpState"

    def resolve_status(self, _):
        return self.status.upper() if self.status else None

    @staticmethod
    def actualize_checkup_state(root: models.CheckUpState):
        """
        deserialize_raw_data data example:
        {(87, None): (datetime.datetime(2021, 2, 2, 6, 15, 35, tzinfo=<UTC>), 9),
         (None, 820): None,
         (None, 849): (datetime.datetime(2021, 1, 20, 6, 15, 35, tzinfo=<UTC>), 3),
         (1205, None): None}
        """

        if getattr(root, "is_actualized", False):
            return

        date = timezone.now()
        delta_checkup_days = datetime.timedelta(days=settings.CHECKUP_DURATION_DAYS)

        data = root.deserialize_raw_data(root.meta.get("data") or {})
        dates = (root.date_from, root.date_to)

        if (
            root.status == CheckUpStateStatus.PARTIAL
            and date - delta_checkup_days > root.date_from
            and date - delta_checkup_days < root.date_to
        ):
            for key, value in data.items():
                if value and value[0] < date - delta_checkup_days:
                    data[key] = None

            dates = [i[0] for i in data.values() if i]
            dates = (min(dates), max(dates))

        root.is_actualized = True
        root.actualized_state = {
            "date_from": dates[0],
            "date_to": dates[1],
            "meta_data": data,
        }

    @classmethod
    def prepare_scoped_scheme_for_meta(cls, data, scheme_source, schematic_data):
        biomarkers = {
            i: schematic_data["biomarkers"].get(i)
            for i in scheme_source.get("biomarkers", {})
        }
        medical_exams = {
            i: schematic_data["medical_exams"].get(i)
            for i in scheme_source.get("medical_exams", {})
        }
        values = list(biomarkers.values()) + list(medical_exams.values())
        dates = list(filter(bool, values))
        progress = list(map(bool, values))

        data["date_from"] = min(dates) if dates else None
        data["date_to"] = max(dates) if dates else None
        data["biomarkers"] = {k: bool(v) for k, v in biomarkers.items()}
        data["medical_exams"] = {k: bool(v) for k, v in medical_exams.items()}
        data["progress"] = round((progress.count(True) / len(progress)) * 100.0, 1)

    @classmethod
    def generate_sku_groups_data_for_meta(
        cls, state: dict, groups: Optional[dict] = None
    ) -> dict:
        # note: there is similar but not the same code in
        #       checkupcenter.tasks.calculate_state_progress_by_groups
        if state["version"] < 2:
            return {}

        groups = groups or settings.CHECKUP_SKU_GROUPS
        data = {
            "groups": {
                i["name"]: {
                    "progress": 0.0,
                    "skus": {},
                }
                for i in groups
            },
        }

        # generate progress for each sku in groups
        for k, v in state["scheme"]["products"].items():
            group = next(
                i["name"] for i in groups if i["skus"] is None or v["sku"] in i["skus"]
            )
            values = [int(bool(state["data"][(None, i)])) for i in v["biomarkers"]] + [
                int(bool(state["data"][(i, None)])) for i in v["medical_exams"]
            ]
            product_global_id = graphene.Node.to_global_id("Product", k)
            progress = round((sum(values) / len(values)) * 100.0, 1)
            data["groups"][group]["skus"][product_global_id] = progress

        # generate progress for each group without considering "part" value
        for group in data["groups"].values():
            if not group["skus"]:
                continue
            group["progress"] = round(
                (sum(s for s in group["skus"].values()) / len(group["skus"])), 1
            )

        return data

    @staticmethod
    def form_check_up_state_meta_item(meta: dict) -> CheckUpStateMetaItem:
        meta_sku = meta.get("sku", {})
        meta_total = meta.get("total", {})
        meta_groups = meta.get("groups", {}).get("groups", {})

        return CheckUpStateMetaItem(
            [
                CheckUpStateMetaItemSKU(
                    id=k,
                    date_from=v.get("date_from"),
                    date_to=v.get("date_to"),
                    biomarkers=[
                        CheckUpStateMetaItemStatus(k_, v_)
                        for k_, v_ in v.get("biomarkers", {}).items()
                    ],
                    medical_exams=[
                        CheckUpStateMetaItemStatus(k_, v_)
                        for k_, v_ in v.get("medical_exams", {}).items()
                    ],
                    progress=v.get("progress"),
                )
                for k, v in meta_sku.items()
            ],
            CheckUpStateMetaItemTotal(
                date_from=meta_total.get("date_from"),
                date_to=meta_total.get("date_to"),
                biomarkers=[
                    CheckUpStateMetaItemStatus(k_, v_)
                    for k_, v_ in meta_total.get("biomarkers", {}).items()
                ],
                medical_exams=[
                    CheckUpStateMetaItemStatus(k_, v_)
                    for k_, v_ in meta_total.get("medical_exams", {}).items()
                ],
                progress=meta_total.get("progress"),
            ),
            [
                CheckUpStateMetaGroup(
                    name=k,
                    progress=v.get("progress"),
                    skus=[
                        CheckUpStateMetaGroupsSku(id=k_, progress=v_)
                        for k_, v_ in v.get("skus", {}).items()
                    ],
                )
                for k, v in meta_groups.items()
            ],
        )

    @staticmethod
    def resolve_checkup_id(root: models.CheckUpState, info, **kwargs):
        return graphene.Node.to_global_id("CheckUp", root.checkup_id)

    @classmethod
    def resolve_date_from(cls, root: models.CheckUpState, info):
        cls.actualize_checkup_state(root)
        return root.actualized_state["date_from"]

    @classmethod
    def resolve_date_to(cls, root: models.CheckUpState, info):
        cls.actualize_checkup_state(root)
        return root.actualized_state["date_to"]

    @classmethod
    def resolve_meta(cls, root: models.CheckUpState, info):
        """
        result data format:
        {'sku': {'UHJvZHVjdDoxMA==': {'date_from': '2021-02-01 06:15:35+00:00',
                                      'date_to': '2021-02-02 06:15:35+00:00',
                                      'biomarkers': {820: False, 848: True},
                                      'medical_exams': {},
                                      'progress': 50},
                 ...},
         'total': {'date_from': '2021-02-01 06:15:35+00:00',
                   'date_to': '2021-02-03 06:15:35+00:00',
                   'biomarkers': {820: False, 848: True, 849: True},
                   'medical_exams': {87: True, 1205: False},
                   'progress': 60}}
        """

        version = root.meta.get("version")
        version = version if isinstance(version, int) else 1

        cls.actualize_checkup_state(root)  # see data format in method source
        data = root.actualized_state["meta_data"]
        scheme = root.meta.get("scheme") or {}

        meta = {"sku": {}, "total": {"progress": 0}}
        schematic_data = {
            "biomarkers": {k[1]: v[0] for k, v in data.items() if k[0] is None and v},
            "medical_exams": {
                k[0]: v[0] for k, v in data.items() if k[1] is None and v
            },
        }

        # prepare total
        cls.prepare_scoped_scheme_for_meta(meta["total"], scheme, schematic_data)

        # prepare each sku
        for sku_id, sku_scheme in scheme["products"].items():
            sku_global_id = graphene.Node.to_global_id("Product", sku_id)
            meta["sku"][sku_global_id] = {}

            cls.prepare_scoped_scheme_for_meta(
                meta["sku"][sku_global_id], sku_scheme, schematic_data
            )

        # recalculate smart total progress
        total_progress = map(
            lambda x: x * (1.0 / len(meta["sku"])),
            [i["progress"] for i in meta["sku"].values()],
        )
        meta["total"]["progress"] = round(sum(total_progress), 1)

        # generate sku groups data
        meta["groups"] = cls.generate_sku_groups_data_for_meta(
            {"data": data, "scheme": scheme, "version": version}
        )

        return cls.form_check_up_state_meta_item(meta)


class CheckUpStateCountableConnection(CountableConnection):
    class Meta:
        doc_category = "Checkup"
        node = CheckUpState


class FsmVariableSkuMatches(graphene.ObjectType):
    rule_id = graphene.Int(required=True)
    name = graphene.String(required=True)
    description = graphene.String(required=True)
