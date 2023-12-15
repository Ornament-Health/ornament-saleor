from typing import Optional
from itertools import groupby

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from saleor.core.utils.json_serializer import CustomJsonEncoder
from saleor.utils.models import AutoNowUpdateFieldsMixin
from saleor.product.models import Product, ProductVariant
from saleor.account.models import User

from . import CheckUpStateStatus, CheckUpStateApprovement


# QuerySets
# ---------
class CheckUpProductQueryset(models.QuerySet):
    def annotate_available_by_rules(self, requestor=None):
        # Annotate items with availability of related product in current users vendors rules.
        subquery = (
            ProductVariant.objects.filter(product=models.OuterRef("product_id"))
            .available_by_rules(requestor)
            .values("id")
        )

        return self.annotate(is_available_in_local_provider=models.Exists(subquery))


class CheckUpTemplateQueryset(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class CheckUpQueryset(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class CheckUpStateQueryset(models.QuerySet):
    def create_from_raw_state(
        self,
        checkup: "CheckUp",
        state: dict,
        status: Optional[str] = None,
        approvement: Optional[str] = None,
    ) -> "CheckUpState":
        meta = {
            "version": 2,  # added sku field in scheme.products.*
            "data": CheckUpState.serialize_raw_data(state["data"]),
            "scheme": state["scheme"],
        }

        return self.create(
            checkup=checkup,
            status=status,
            approvement=approvement,
            date_from=state["date_from"],
            date_to=state["date_to"],
            meta=meta,
        )


# Models
# ------
class CheckUpCategory(AutoNowUpdateFieldsMixin, models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    emoji = models.CharField(max_length=8, null=True, blank=True)

    ext_id = models.CharField(max_length=32, unique=True)

    created = models.DateTimeField(default=timezone.now, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    # TODO[ornament]: translations
    # translated = TranslationProxy()

    class Meta:
        db_table = "checkupcenter_checkup_category"
        verbose_name = "checkup category"
        verbose_name_plural = "checkup categories"

    def __str__(self):
        return self.name


class CheckUpCategoryTranslation(models.Model):
    language_code = models.CharField(max_length=10)
    category = models.ForeignKey(
        CheckUpCategory, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "checkupcenter_checkup_category_translation"
        unique_together = ("category", "language_code")
        verbose_name = "checkup category translation"
        verbose_name_plural = "checkup category translations"


class CheckUpProductCategory(AutoNowUpdateFieldsMixin, models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)

    ext_id = models.CharField(max_length=32, null=True, blank=True, unique=True)
    human_part_id = models.IntegerField(null=True, blank=True)

    created = models.DateTimeField(default=timezone.now, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    # TODO[ornament]: translations
    # translated = TranslationProxy()

    class Meta:
        db_table = "checkupcenter_checkup_product_category"
        verbose_name = "checkup product category"
        verbose_name_plural = "checkup product categories"

    def __str__(self):
        return (
            f"Human Part #{self.human_part_id}"
            if self.human_part_id
            else (self.name or f"CheckUpProductCategory #{self.id}")
        )


class CheckUpProductCategoryTranslation(models.Model):
    language_code = models.CharField(max_length=10)
    category = models.ForeignKey(
        CheckUpProductCategory, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "checkupcenter_checkup_product_category_translation"
        unique_together = ("category", "language_code")
        verbose_name = "checkup product category translation"
        verbose_name_plural = "checkup product category translations"


class CheckUpTemplate(AutoNowUpdateFieldsMixin, models.Model):
    category = models.ForeignKey(CheckUpCategory, on_delete=models.CASCADE)
    products = models.ManyToManyField(
        Product, blank=False, through="checkupcenter.CheckUpTemplateProduct"
    )

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    filters = JSONField(default=dict, encoder=CustomJsonEncoder)

    is_active = models.BooleanField(default=True)
    is_calculatable = models.BooleanField(default=True)
    is_base = models.BooleanField(default=False)
    is_personalized = models.BooleanField(default=False)

    created = models.DateTimeField(default=timezone.now, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    objects = CheckUpTemplateQueryset.as_manager()
    # TODO[ornament]: translations
    # translated = TranslationProxy()

    class Meta:
        db_table = "checkupcenter_checkup_template"
        verbose_name = "checkup template"
        verbose_name_plural = "checkup templates"

    def __str__(self):
        return self.name

    @classmethod
    def match_templates_by_data(cls, data: dict):
        # Only one template is allowed per category.
        # Only one base (is_base and is_calculatable) template is allowed at all.
        templates = (
            cls.objects.active().filter(is_personalized=False).order_by("category_id")
        )
        templates = [
            list(v) for k, v in groupby(templates, key=lambda x: x.category_id)
        ]
        templates = [
            next((t for t in group if t.match_template(data)), None)
            for group in templates
        ]

        # Exclude all base templates except first one.
        base_tpls = [t for t in templates if t and t.is_base and t.is_calculatable]
        exclude_values = [None, base_tpls[1:]]

        return [t for t in templates if not t in exclude_values]

    def match_template(self, data: dict):
        if not (
            self.filters
            and isinstance(self.filters, dict)
            and "rules" in self.filters
            and isinstance(self.filters["rules"], list)
            and self.filters["rules"]
        ):
            return False

        if not data or not set(data.keys()) & set(self.rules):
            return False

        for rule in self.filters["rules"]:
            if self.match_rule(rule, data):
                return True

        return False

    def check_rule(self, rule: dict):
        valid = False
        for key, value in rule.items():
            if not key in self.rules:
                continue
            if not (
                hasattr(self, f"check_rule_{key}")
                and hasattr(self, f"match_rule_{key}")
            ):
                raise NotImplementedError(
                    f'Rule "{key}" handlers does not implemented.'
                )
            if not getattr(self, f"check_rule_{key}")(value):
                return False
            valid = True
        return valid

    def match_rule(self, rule: dict, data: dict):
        if not self.check_rule(rule):
            return False

        matched = False
        for key, value in rule.items():
            if not key in self.rules or not key in data:
                continue
            if not getattr(self, f"match_rule_{key}")(value, data[key]):
                return False
            matched = True

        return matched

    # rules handlers
    rules: list = ["sex", "age"]
    rules_sex_values = ["M", "F"]

    def check_rule_sex(self, rule):
        return (
            isinstance(rule, list) and all(i in self.rules_sex_values for i in rule)
        ) or rule == "*"

    def match_rule_sex(self, rule, value):
        return rule == "*" or (value in self.rules_sex_values and value in rule)

    def check_rule_age(self, rule):
        return (
            isinstance(rule, list)
            and len(rule) == 2
            and all(isinstance(i, int) for i in rule)
        )

    def match_rule_age(self, rule, value):
        return rule[0] <= value <= rule[1]


class CheckUpTemplateTranslation(models.Model):
    language_code = models.CharField(max_length=10)
    template = models.ForeignKey(
        CheckUpTemplate, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "checkupcenter_checkup_template_translation"
        unique_together = ("template", "language_code")
        verbose_name = "checkup template translation"
        verbose_name_plural = "checkup template translations"


class CheckUpTemplateProduct(AutoNowUpdateFieldsMixin, models.Model):
    template = models.ForeignKey(CheckUpTemplate, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    created = models.DateTimeField(default=timezone.now, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        db_table = "checkupcenter_checkup_template_product"
        verbose_name = "checkup template product"
        verbose_name_plural = "checkup template products"

    def __str__(self):
        return f"<CheckUpTemplateProduct #{self.id}>"


class CheckUp(AutoNowUpdateFieldsMixin, models.Model):
    template = models.ForeignKey(
        CheckUpTemplate, on_delete=models.SET_NULL, null=True, blank=True
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="checkups_personalized",
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(CheckUpCategory, on_delete=models.CASCADE)
    products = models.ManyToManyField(
        Product, blank=False, through="checkupcenter.CheckUpProduct"
    )

    is_active = models.BooleanField(default=True)
    is_calculatable = models.BooleanField(default=True)
    is_base = models.BooleanField(default=False)
    is_personalized = models.BooleanField(default=False)

    profile_uuid = models.UUIDField()

    matched_at = models.DateTimeField(null=True, editable=False)
    personalized_at = models.DateTimeField(null=True, editable=False)
    calculated_at = models.DateTimeField(null=True, editable=False)
    created = models.DateTimeField(default=timezone.now, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    objects = CheckUpQueryset.as_manager()

    class Meta:
        db_table = "checkupcenter_checkup"
        verbose_name = "checkup"
        verbose_name_plural = "checkups"

    def __str__(self):
        return f"<CheckUp #{self.id} user:{self.user_id}>"

    def get_checkup_medical_scheme(self):
        """
        Meta data in CheckUpProduct model instances:
        "ornament": {
            "biomarkers": [1,2,],
            "medical_exams": [1,2,],
            "products": {
                1: {"sku": "sku-1", "biomarkers": [1, 2]},
                2: {"sku": "sku-2", "biomarkers": [1], "medical_exams": [1, 2]},
                3: {"sku": "sku-3", "medical_exams": [2]},
            }
        }
        """

        scheme = {"biomarkers": [], "medical_exams": [], "products": {}}
        checkup_products: list[CheckUpProduct] = self.checkup_products.select_related(
            "product"
        ).all()

        for i in checkup_products:
            data = i.meta.get("ornament", {})
            if not data or not isinstance(data, dict):
                continue

            scheme["products"][i.product_id] = {"sku": i.product.name}
            if isinstance(data.get("biomarkers"), list):
                scheme["biomarkers"].extend(data["biomarkers"])
                scheme["products"][i.product_id]["biomarkers"] = data["biomarkers"]
            if isinstance(data.get("medical_exams"), list):
                scheme["medical_exams"].extend(data["medical_exams"])
                scheme["products"][i.product_id]["medical_exams"] = data[
                    "medical_exams"
                ]

        scheme["biomarkers"] = sorted(set(scheme["biomarkers"]))
        scheme["medical_exams"] = sorted(set(scheme["medical_exams"]))

        return scheme


class CheckUpProduct(AutoNowUpdateFieldsMixin, models.Model):
    checkup = models.ForeignKey(
        CheckUp, on_delete=models.CASCADE, related_name="checkup_products"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    is_personalized = models.BooleanField(default=False)

    meta = JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)

    created = models.DateTimeField(default=timezone.now, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    objects = CheckUpProductQueryset.as_manager()

    class Meta:
        db_table = "checkupcenter_checkup_product"
        verbose_name = "checkup product"
        verbose_name_plural = "checkup products"

    def __str__(self):
        return f"<CheckUpProduct #{self.id}>"


class CheckUpState(AutoNowUpdateFieldsMixin, models.Model):
    checkup = models.ForeignKey(
        CheckUp, on_delete=models.CASCADE, related_name="checkup_states"
    )

    status = models.CharField(
        max_length=16, blank=True, null=True, choices=CheckUpStateStatus.CHOICES
    )
    approvement = models.CharField(
        max_length=16, blank=True, null=True, choices=CheckUpStateApprovement.CHOICES
    )

    meta = JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)

    date_from = models.DateTimeField(blank=True, null=True)
    date_to = models.DateTimeField(blank=True, null=True)

    created = models.DateTimeField(default=timezone.now, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    objects = CheckUpStateQueryset.as_manager()

    class Meta:
        db_table = "checkupcenter_checkup_state"
        verbose_name = "checkup state"
        verbose_name_plural = "checkup states"

    def __str__(self):
        return f"<CheckUpState #{self.id}:{self.status} for CheckUp #{self.checkup_id}>"

    @classmethod
    def serialize_raw_data(cls, data):
        """
        Converts raw pythonic format:
        {
            (None, 820): None,
            (None, 848): (datetime.datetime(2021, 2, 2, 6, 15, 35, tzinfo=<UTC>), 1),
            (None, 849): (datetime.datetime(2021, 1, 20, 6, 15, 35, tzinfo=<UTC>), 3),
            (87, None): (datetime.datetime(2021, 2, 2, 6, 15, 35, tzinfo=<UTC>), 9),
            (1205, None): None,
        }

        into json ready format (get only last one in each list of tuples):
        {
            'biomarkers': {
                820: None,
                848: (datetime.datetime(2021, 2, 2, 6, 15, 35, tzinfo=<UTC>), 1),
                849: (datetime.datetime(2021, 1, 20, 6, 15, 35, tzinfo=<UTC>), 3),
            },
            'medical_exams': {
                87: (datetime.datetime(2021, 2, 2, 6, 15, 35, tzinfo=<UTC>), 9),
                1205: None,
            }
        }

        which in turn will become the following json value:
        {
            'biomarkers': {
                '820': None,
                '848': [2021-02-02T06:15:35Z, 1],
                '849': [2021-02-02T06:15:35Z, 3],
            },
            'medical_exams': {
                '87': [2021-02-02T06:15:35Z, 9],
                '1205': None,
            }
        }
        """
        return {
            "biomarkers": {
                bid: value for (sid, bid), value in data.items() if sid is None
            },
            "medical_exams": {
                sid: value for (sid, bid), value in data.items() if bid is None
            },
        }

    @classmethod
    def deserialize_raw_data(cls, data):
        """
        Converts json ready format to pythonic, like serialize_raw_data but vice versa.
        Supports both datetime formats - strings and datetime objects.
        """

        meta = {}
        for bid, value in data["biomarkers"].items():
            value = value and (
                parse_datetime(value[0]) if isinstance(value[0], str) else value[0],
                value[1],
            )
            meta[(None, int(bid))] = value
        for sid, value in data["medical_exams"].items():
            value = value and (
                parse_datetime(value[0]) if isinstance(value[0], str) else value[0],
                value[1],
            )
            meta[(int(sid), None)] = value

        return meta

    def get_unique_string_from_state_data(self, data):
        """
        Data format:
        {
            "biomarkers": {1: None, 2: [<datatime>, 1], 3: [<datatime>, 31]},
            "medical_exams": {1: [<datatime>, 1], 3: [<datatime>, 31], 2: [<datatime>, 33]},
        }

        Result string format:
        "biomarkers||1:n|2:1|3:31|||medical_exams||1:1|2:33|3:31"
        """

        # fmt: off
        return "|||".join(sorted(
            f"{k}||" + (
                "|".join(sorted(
                    f"{k1}:{v1[1] if v1 else 'n'}" for k1, v1 in v.items()
                )) or "-"
            )
            for k, v in data.items()
        ))
        # fmt: on

    def equals_to_raw_state(self, state: dict) -> bool:
        if not (
            state["date_from"] == self.date_from and state["date_to"] == self.date_to
        ):
            return False

        rawdata = self.serialize_raw_data(state["data"])

        objsign = self.get_unique_string_from_state_data(self.meta["data"])
        rawsign = self.get_unique_string_from_state_data(rawdata)

        return objsign == rawsign
