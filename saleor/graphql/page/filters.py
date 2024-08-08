import datetime
import math
from collections import defaultdict

import graphene
import django_filters
from django.db.models import Q
from django.db.models import Exists, FloatField, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Cast

from saleor.attribute import AttributeInputType
from saleor.attribute.models import Attribute, AttributeValue
from saleor.attribute.models.page import AssignedPageAttributeValue
from saleor.graphql.product.filters import KeyValueDict

from ...page import models
from ..core.doc_category import DOC_CATEGORY_PAGES
from ..core.filters import (
    GlobalIDMultipleChoiceFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
    filter_slug_list,
)
from ..core.types import FilterInputObjectType
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import filter_by_id
from .types import Page, PageType

T_PAGE_FILTER_QUERIES = dict[int, list[int]]


def filter_page_search(qs, _, value):
    if not value:
        return qs
    return qs.filter(
        Q(title__trigram_similar=value)
        | Q(slug__trigram_similar=value)
        | Q(content__icontains=value)
    )


def filter_page_page_types(qs, _, value):
    if not value:
        return qs
    _, page_types_pks = resolve_global_ids_to_primary_keys(value, PageType)
    return qs.filter(page_type_id__in=page_types_pks)


def filter_page_type_search(qs, _, value):
    if not value:
        return qs
    return qs.filter(Q(name__trigram_similar=value) | Q(slug__trigram_similar=value))


def _clean_page_attributes_filter_input(
    filter_value, queries, database_connection_name
):
    attribute_slugs = []
    value_slugs = []
    for attr_slug, val_slugs in filter_value:
        attribute_slugs.append(attr_slug)
        value_slugs.extend(val_slugs)
    attributes_slug_pk_map: dict[str, int] = {}
    attributes_pk_slug_map: dict[int, str] = {}
    values_map: dict[str, dict[str, int]] = defaultdict(dict)
    for attr_slug, attr_pk in (
        Attribute.objects.using(database_connection_name)
        .filter(slug__in=attribute_slugs)
        .values_list("slug", "id")
    ):
        attributes_slug_pk_map[attr_slug] = attr_pk
        attributes_pk_slug_map[attr_pk] = attr_slug

    for (
        attr_pk,
        value_pk,
        value_slug,
    ) in (
        AttributeValue.objects.using(database_connection_name)
        .filter(slug__in=value_slugs, attribute_id__in=attributes_pk_slug_map.keys())
        .values_list("attribute_id", "pk", "slug")
    ):
        attr_slug = attributes_pk_slug_map[attr_pk]
        values_map[attr_slug][value_slug] = value_pk

    # Convert attribute:value pairs into a dictionary where
    # attributes are keys and values are grouped in lists
    for attr_name, val_slugs in filter_value:
        if attr_name not in attributes_slug_pk_map:
            raise ValueError(f"Unknown attribute name: {attr_name}")
        attr_pk = attributes_slug_pk_map[attr_name]
        attr_val_pk = [
            values_map[attr_name][val_slug]
            for val_slug in val_slugs
            if val_slug in values_map[attr_name]
        ]
        queries[attr_pk] += attr_val_pk


def _clean_page_attributes_range_filter_input(
    filter_value, queries, database_connection_name
):
    attributes = Attribute.objects.using(database_connection_name).filter(
        input_type=AttributeInputType.NUMERIC
    )
    values = (
        AttributeValue.objects.using(database_connection_name)
        .filter(Exists(attributes.filter(pk=OuterRef("attribute_id"))))
        .annotate(numeric_value=Cast("name", FloatField()))
        .select_related("attribute")
    )

    attributes_map: dict[str, int] = {}
    values_map: defaultdict[str, defaultdict[str, list[int]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for value_data in values.values_list(
        "attribute_id", "attribute__slug", "pk", "numeric_value"
    ):
        attr_pk, attr_slug, pk, numeric_value = value_data
        attributes_map[attr_slug] = attr_pk
        values_map[attr_slug][numeric_value].append(pk)

    for attr_name, val_range in filter_value:
        if attr_name not in attributes_map:
            raise ValueError(f"Unknown numeric attribute name: {attr_name}")
        gte, lte = val_range.get("gte", 0), val_range.get("lte", math.inf)
        attr_pk = attributes_map[attr_name]
        attr_values = values_map[attr_name]
        matching_values = [
            value for value in attr_values.keys() if gte <= value and lte >= value
        ]
        queries[attr_pk] = []
        for value in matching_values:
            queries[attr_pk] += attr_values[value]


def _clean_page_attributes_date_time_range_filter_input(
    filter_value, database_connection_name
):
    attribute_slugs = [slug for slug, _ in filter_value]
    matching_attributes = AttributeValue.objects.using(database_connection_name).filter(
        attribute__slug__in=attribute_slugs
    )
    filters = {}
    for _, val_range in filter_value:
        if lte := val_range.get("lte"):
            if not isinstance(lte, datetime.datetime):
                lte = datetime.datetime.combine(lte, datetime.datetime.max.time())
            filters["date_time__lte"] = lte
        if gte := val_range.get("gte"):
            if not isinstance(gte, datetime.datetime):
                gte = datetime.datetime.combine(gte, datetime.datetime.min.time())
            filters["date_time__gte"] = gte
    return matching_attributes.filter(**filters)


def filter_pages_by_attributes_values_qs(qs, values_qs):
    assigned_page_attribute_values = AssignedPageAttributeValue.objects.using(
        qs.db
    ).filter(value__in=values_qs)
    page_attribute_filter = Q(
        Exists(assigned_page_attribute_values.filter(page_id=OuterRef("pk")))
    )
    return qs.filter(page_attribute_filter)


def _clean_page_attributes_boolean_filter_input(
    filter_value, queries, database_connection_name
):
    attribute_slugs = [slug for slug, _ in filter_value]
    attributes = (
        Attribute.objects.using(database_connection_name)
        .filter(input_type=AttributeInputType.BOOLEAN, slug__in=attribute_slugs)
        .prefetch_related("values")
    )
    values_map: dict[str, KeyValueDict] = {
        attr.slug: {
            "pk": attr.pk,
            "values": {val.boolean: val.pk for val in attr.values.all()},
        }
        for attr in attributes
    }

    for attr_slug, value in filter_value:
        if attr_slug not in values_map:
            raise ValueError(f"Unknown attribute name: {attr_slug}")
        attr_pk = values_map[attr_slug].get("pk")
        value_pk = values_map[attr_slug]["values"].get(value)
        if not value_pk:
            raise ValueError(f"Requested value for attribute {attr_slug} doesn't exist")
        if attr_pk and value_pk:
            queries[attr_pk] += [value_pk]


def filter_pages_by_attributes_values(qs, queries: T_PAGE_FILTER_QUERIES):
    filters = []
    for values in queries.values():
        assigned_page_attribute_values = AssignedPageAttributeValue.objects.using(
            qs.db
        ).filter(value_id__in=values)
        page_attribute_filter = Q(
            Exists(assigned_page_attribute_values.filter(page_id=OuterRef("pk")))
        )
        filters.append(page_attribute_filter)

    return qs.filter(*filters)


def filter_pages_by_attributes(
    qs,
    filter_values,
    filter_range_values,
    filter_boolean_values,
    date_range_list,
    date_time_range_list,
):
    queries: dict[int, list[int]] = defaultdict(list)
    try:
        if filter_values:
            _clean_page_attributes_filter_input(filter_values, queries, qs.db)
        if filter_range_values:
            _clean_page_attributes_range_filter_input(
                filter_range_values, queries, qs.db
            )
        if date_range_list:
            values_qs = _clean_page_attributes_date_time_range_filter_input(
                date_range_list, qs.db
            )
            return filter_pages_by_attributes_values_qs(qs, values_qs)
        if date_time_range_list:
            values_qs = _clean_page_attributes_date_time_range_filter_input(
                date_time_range_list, qs.db
            )
            return filter_pages_by_attributes_values_qs(qs, values_qs)
        if filter_boolean_values:
            _clean_page_attributes_boolean_filter_input(
                filter_boolean_values, queries, qs.db
            )
    except ValueError:
        return models.Page.objects.none()
    return filter_pages_by_attributes_values(qs, queries)


def _filter_attributes(qs, _, value):
    if value:
        value_list = []
        boolean_list = []
        value_range_list = []
        date_range_list = []
        date_time_range_list = []

        for v in value:
            slug = v["slug"]
            if "values" in v:
                value_list.append((slug, v["values"]))
            elif "values_range" in v:
                value_range_list.append((slug, v["values_range"]))
            elif "date" in v:
                date_range_list.append((slug, v["date"]))
            elif "date_time" in v:
                date_time_range_list.append((slug, v["date_time"]))
            elif "boolean" in v:
                boolean_list.append((slug, v["boolean"]))

        qs = filter_pages_by_attributes(
            qs,
            value_list,
            value_range_list,
            boolean_list,
            date_range_list,
            date_time_range_list,
        )
    return qs


class PageFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method=filter_page_search)
    page_types = GlobalIDMultipleChoiceFilter(method=filter_page_page_types)
    ids = GlobalIDMultipleChoiceFilter(method=filter_by_id(Page))
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)
    attributes = ListObjectTypeFilter(
        input_class="saleor.graphql.attribute.types.AttributeInput",
        method="filter_attributes",
    )

    class Meta:
        model = models.Page
        fields = [
            "search",
            "attributes",
        ]

    def filter_attributes(self, queryset, name, value):
        return _filter_attributes(queryset, name, value)


class PageFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        filterset_class = PageFilter


class PageTypeFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_page_type_search)
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)


class PageTypeFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        filterset_class = PageTypeFilter
