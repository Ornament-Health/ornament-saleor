import django_filters

from saleor.graphql.core.filters import GlobalIDFilter
from saleor.graphql.core.types import FilterInputObjectType
from saleor.ornament.checkupcenter import models


class CheckUpFilter(django_filters.FilterSet):
    category = GlobalIDFilter()
    profile_uuid = django_filters.UUIDFilter()

    class Meta:
        model = models.CheckUp
        fields = ["category", "profile_uuid"]


class CheckUpFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = "Checkup"
        filterset_class = CheckUpFilter
