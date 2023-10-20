from typing import List

import graphene

from saleor.graphql.attribute.types import SelectedAttribute
from saleor.graphql.core.fields import JSONString
from saleor.graphql.core.types import ModelObjectType
from saleor.graphql.product.dataloaders.attributes import (
    SelectedAttributesByProductIdLoader,
)
from saleor.product import models as product_models
from saleor.graphql.core.connection import CountableConnection


class SearchProduct(ModelObjectType[product_models.Product]):
    id = graphene.GlobalID(required=True)
    channels = graphene.List(
        graphene.NonNull(graphene.String),
        description="List of channels where this product is listed.",
        required=True,
    )
    name = graphene.String(required=True, description="Product name.")
    description = JSONString(description="Description of the product.")
    biomarkers = graphene.Field(
        graphene.List(graphene.Int),
        description=("List of biomarkers attributes."),
    )
    medical_exams = graphene.Field(
        graphene.List(graphene.Int),
        description=("List of medical exams attributes."),
    )

    class Meta:
        model = product_models.Product
        interfaces = [graphene.relay.Node]
        description = "Represents a search product."

    @staticmethod
    def _get_attributes(
        attributes: List[SelectedAttribute], attribute_slug: str
    ) -> List[int]:
        attribute_values = [
            [int(a.name) for a in atr["values"]]
            for atr in attributes
            if atr["attribute"].slug == attribute_slug
        ]
        return attribute_values[0] if attribute_values else []

    @classmethod
    def resolve_biomarkers(cls, root: product_models.Product, info):
        return (
            SelectedAttributesByProductIdLoader(info.context)
            .load(root.id)
            .then(lambda attributes: cls._get_attributes(attributes, "biomarkers"))
        )

    @classmethod
    def resolve_medical_exams(cls, root: product_models.Product, info):
        return (
            SelectedAttributesByProductIdLoader(info.context)
            .load(root.id)
            .then(lambda attributes: cls._get_attributes(attributes, "medical_exams"))
        )


class SearchProductCountableConnection(CountableConnection):
    class Meta:
        doc_category = "Search products"
        node = SearchProduct
