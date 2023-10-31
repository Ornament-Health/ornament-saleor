from typing import List, Optional

import graphene

from saleor.graphql.attribute.types import SelectedAttribute
from saleor.graphql.core.fields import JSONString
from saleor.graphql.core.types import ModelObjectType
from saleor.graphql.product.dataloaders.attributes import (
    SelectedAttributesByProductIdLoader,
)
from saleor.product import models as product_models
from saleor.graphql.core.connection import CountableConnection


class SearchProductChannelPrice(graphene.ObjectType):
    channel = graphene.String(description="Price channel")
    amount = graphene.String(description="Price amount")
    currency = graphene.String(description="Price currency")
    variant_id = graphene.String(description="Variant ID")


class SearchProductType(graphene.ObjectType):
    id = graphene.GlobalID(required=True, description="The ID of the product type.")
    name = graphene.String(required=True, description="Name of the product type.")
    slug = graphene.String(required=True, description="Slug of the product type.")


class SearchProduct(ModelObjectType[product_models.Product]):
    product_id = graphene.String(required=True)
    variant_id = graphene.String(required=True)
    channels = graphene.List(
        graphene.NonNull(graphene.String),
        description="List of channels where this product is listed.",
        required=True,
    )
    name = graphene.String(required=True, description="Product name.")
    description = JSONString(description="Description of the product.")
    biomarkers = graphene.List(
        graphene.Int,
        description=("List of biomarkers attributes."),
    )
    medical_exams = graphene.List(
        graphene.Int,
        description=("List of medical exams attributes."),
    )
    prices = graphene.List(
        SearchProductChannelPrice,
        description=("Product prices per channel."),
    )
    product_type = graphene.Field(SearchProductType, description="Product type info")

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
    def resolve_product_id(cls, root: product_models.Product, info):
        return graphene.Node.to_global_id("Product", root.pk)

    @classmethod
    def resolve_variant_id(cls, root: product_models.Product, info):
        return graphene.Node.to_global_id("ProductVariant", root.variant_id)

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

    @classmethod
    def resolve_prices(cls, root: product_models.Product, info):
        return [
            SearchProductChannelPrice(
                channel=p["channel__slug"],
                amount=float(p["price_amount"]),
                currency=p["currency"],
            )
            for p in root.current_variant_prices
        ]

    @classmethod
    def resolve_product_type(cls, root: product_models.Product, info):
        return SearchProductType(
            id=root.product_type.pk,
            name=root.product_type.name,
            slug=root.product_type.slug,
        )


class SearchProductCountableConnection(CountableConnection):
    class Meta:
        doc_category = "Search products"
        node = SearchProduct
