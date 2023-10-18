import copy
import datetime
import logging
from typing import Optional

import requests
from django.conf import settings
from django.utils import timezone
from requests.exceptions import RequestException

from saleor.account.models import User
from saleor.celeryconf import app
from saleor.product.models import Product
from saleor.utils.locks import RedisBlockingCounterManager

from . import CheckUpStateApprovement, CheckUpStateStatus, models

logger = logging.getLogger(__name__)

SPECIAL_CASE_FULL_SKU_BIOMARKERS = [190, 337]


# Utils


# only for multiselect attribute types
def get_int_product_attribute_values_by_slug(product: Product, attribute_slug: str):
    return list(
        map(
            lambda x: int(x),
            product.attributevalues.filter(
                assignment__assignment__attribute__slug=attribute_slug
            ).values_list("value__name", flat=True),
        )
    )


def get_user_medical_history_from_dataapi(pid, history=None):
    """
    DataApi json history:
    {
      "items": [
        {
          "etoid": 1411,
          "bid": null,
          "sid": 190609,
          "seid": null,
          "date": 1608768000
        },
        {
          "etoid": null,
          "bid": 57,
          "sid": 190608,
          "seid": 2337367,
          "date": 1608076800
        }
      }
    }

    Result python history for further processing:
    [
        (1411, None, datetime.datetime(2020, 12, 24, 0, 0, tzinfo=<UTC>), 190609),
        (None, 57, datetime.datetime(2020, 12, 16, 0, 0, tzinfo=<UTC>), 2337367),
    ]

    DataApi keys meaning (key - DataApi model field):
        etoid   - SubmissionEntity.exam_type_object_id
        bid     - SubmissionEntryEntity.biomarker_id
        sid     - SubmissionEntity.id
        seid    - SubmissionEntryEntity.id
        date    - SubmissionEntity.date
    """
    INTERNAL_DATA_API = settings.ORNAMENT_INTERNAL_DATA_API

    if history is None:
        try:
            response = requests.post(
                f"{INTERNAL_DATA_API}/internal/data-api/v1.0/checkup/medical-history",
                json={"pid": str(pid)},
                timeout=(5, 15.02),
            )
            history = response.json() if response.status_code == 200 else []
        except (RequestException, Exception) as error:
            logger.critical(f"DataApi error: {error}")
            history = []

    if history:
        # translate json history to python history (see docstring above)
        history = [
            (
                i["etoid"],
                i["bid"],
                datetime.datetime.utcfromtimestamp(i["date"]).replace(
                    tzinfo=timezone.utc
                ),
                i["seid"] or i["sid"],
            )
            for i in history["items"]
        ]
        history = sorted(history, key=lambda x: x[2], reverse=True)

    return history


def check_state_data_is_not_changed_in_history(state, history):
    """
    Check are there any changes in history that intersect with state data.
    Usually it happens if user deletes/updates his medical data in data api.

    State deserialized raw data format:

    {(87, None): (datetime.datetime(2021, 2, 2, 6, 15, 35, tzinfo=<UTC>), 9),
     (None, 848): (datetime.datetime(2021, 2, 2, 6, 15, 35, tzinfo=<UTC>), 1),
     (1205, None): None}

    History format:

    [(190609, None, datetime.datetime(2020, 12, 24, 0, 0, tzinfo=<UTC>), 1411),
     (190610, None, datetime.datetime(2020, 12, 24, 0, 0, tzinfo=<UTC>), 1411)]
    """

    # None values considered as exist by default
    # Special-case:full-sku-biomarkers: dbid 0 values considered as exists by default
    # Special-case:full-sku-medical-exams: dbid 0 values considered as exists by default
    data = state.deserialize_raw_data(state.meta["data"])
    data = {k: {"value": v, "exists": v is None or v[1] == 0} for k, v in data.items()}

    for exam_type, mid, sdate, dbid in history:
        key, value = (exam_type, mid), (sdate, dbid)
        if key in data and data[key]["value"] == value:
            data[key]["exists"] = True

    return all(i["exists"] for i in data.values())


def calculate_state_progress_by_groups(
    state: dict, groups: Optional[dict] = None
) -> dict:
    # note: there is similar but not the same code in
    #       graphql.checkupcenter.types.CheckUpState.generate_sku_groups_data_for_meta

    groups = groups or settings.CHECKUP_SKU_GROUPS
    data = {
        "total": {"progress": 0},
        "groups": {
            i["name"]: {
                "progress": 0.0,
                "skus": {},
                "part": i["part"],
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
        progress = round((sum(values) / len(values)) * 100.0, 1)
        data["groups"][group]["skus"][k] = {"progress": progress}

    # generate progress for each group considering "part" value
    for group in data["groups"].values():
        if not group["skus"]:
            continue
        group["progress"] = round(
            (sum(s["progress"] for s in group["skus"].values()) / len(group["skus"]))
            * (group["part"] / 100.0),
            1,
        )

    # generate total progress considering "part" values in each group
    data["total"]["progress"] = sum(g["progress"] for g in data["groups"].values())

    return data


def calculate_checkup_states_from_history(scheme: dict, history: dict):
    """
    Scheme format:
    {
        'biomarkers': [820, 848, 849],
        'medical_exams': [87, 1205],
        'products': {
            10: {'sku': 'sku-10', 'biomarkers': [820, 848]},
            11: {'sku': 'sku-11', 'biomarkers': [848, 849], 'medical_exams': [87, 1205]},
            14: {'sku': 'sku-14', 'biomarkers': [848], 'medical_exams': [87, 1205]}
        }
    }

    History format:
    [
        (None, 1, datetime.datetime(2021, 2, 2,  6, 15, 35), 1,),
        (1, None, datetime.datetime(2021, 2, 2,  6, 15, 35), 7,),
        (2, None, datetime.datetime(2021, 2, 2,  6, 15, 35), 9,),
        (None, 1, datetime.datetime(2021, 1, 25, 6, 15, 35), 2,),
        (None, 2, datetime.datetime(2021, 1, 20, 6, 15, 35), 3,),
        (2, None, datetime.datetime(2021, 1, 20, 6, 15, 35), 10,),
        (None, 2, datetime.datetime(2021, 1, 15, 6, 15, 35), 4,),
        (None, 4, datetime.datetime(2021, 1, 1,  6, 15, 35), 6,),
        (None, 3, datetime.datetime(2021, 1, 1,  6, 15, 35), 5,),
        (1, None, datetime.datetime(2020, 1, 15, 6, 15, 35), 8,),
    ]

    State raw format:
    {
        'data': {
            (None, 1): (datetime.datetime(2021, 2, 2, 6, 15, 35), 1),
            (2, None): (datetime.datetime(2021, 2, 2, 6, 15, 35), 9),
            (None, 2): (datetime.datetime(2021, 1, 20, 6, 15, 35), 3),
            (None, 3): None,
        },
        'date_from': datetime.datetime(2021, 1, 20, 6, 15, 35),
        'date_to': datetime.datetime(2021, 2, 2, 6, 15, 35),
        'scheme': {...},
    }

    Special-case:full-sku-biomarkers ids format:
    {
        (None, 190): [1, 2, 3, 190],
        (None, 337): [2, 3, 5, 7, 337],
    }

    Special-case:full-sku-medical-exams ids format:
    {
        (19, None): [1, 2, 3, 19],
        (33, None): [2, 3, 5, 7, 33],
    }
    """

    keys = [
        *[(None, i) for i in scheme.get("biomarkers", [])],
        *[(i, None) for i in scheme.get("medical_exams", [])],
    ]

    # Special-case:full-sku-biomarkers: generate full sku biomarkers map
    sc_full_sku_biomarkers = {(None, i): [] for i in SPECIAL_CASE_FULL_SKU_BIOMARKERS}
    for value in scheme.get("products", {}).values():
        biomarkers = value.get("biomarkers", [])
        for biomarker in SPECIAL_CASE_FULL_SKU_BIOMARKERS:
            if biomarker in biomarkers:
                sc_full_sku_biomarkers[(None, biomarker)].extend(biomarkers)
    for k, v in sc_full_sku_biomarkers.items():
        sc_full_sku_biomarkers[k] = list(set(v))

    # Special-case:full-sku-medical-exams: generate full sku medical_exams map
    sc_full_sku_medical_exams = {}
    for value in scheme.get("products", {}).values():
        medical_exams = value.get("medical_exams", [])
        if medical_exams and len(medical_exams) > 1:
            for exam_type in medical_exams:
                key = (exam_type, None)
                if not key in sc_full_sku_medical_exams:
                    sc_full_sku_medical_exams[key] = []
                sc_full_sku_medical_exams[key].extend(medical_exams)
    for k, v in sc_full_sku_medical_exams.items():
        sc_full_sku_medical_exams[k] = list(set(v))

    data = history
    delta_checkup_days = datetime.timedelta(days=settings.CHECKUP_DURATION_DAYS)
    date_most_filled_state_expiration = timezone.now() - datetime.timedelta(
        days=settings.CHECKUP_MOST_FILLED_STATE_EXPIRATION_DAYS
    )
    state = {
        "scheme": scheme,
        "data": {i: [] for i in keys},
        "date_from": None,
        "date_to": None,
        "is_empty": True,
    }
    states = {"partial": None, "full": None, "most_filled": None}

    # main cycle
    most_filled_biggest_progress = 0
    for exam_type, mid, date, dbid in data:
        key = (exam_type, mid)
        if not key in state["data"]:
            continue

        out_of_range = state["date_to"] and date + delta_checkup_days < state["date_to"]

        """
        1. Save partial state if new item goes out of range (only once),
           partial can not be created after full is collected.
        2. Add item to state.
           Special-case:full-sku-biomarkers: additionaly add all related
           biomarkers if item is biomarker and in full-sku-biomarkers (hack history).
           Special-case:full-sku-medical-exams: additionaly add all related
           exam types if item is exam and in full-sku-medical-exams (hack history).
        3. Check all items are in 30d range and remove that ones which are not.
           This case can not be reached if full is collected.
        4. Reset from and to dates by new min and max dates.
        5. Check state is full, save it and stop process if it is.
        6. Save new most-filled state if progress of new current state is bigger
           than progress of previous most-filled state.
           Most-filled state have to be older than partial state and must contains
           only medical data added later than one year ago.
        7. Clear additional information in each state.
        """

        # 1.
        if out_of_range and not states["partial"]:
            states["partial"] = copy.deepcopy(state)
            most_filled_biggest_progress = calculate_state_progress_by_groups(state)

        # 2.
        state["data"][key].insert(0, (date, dbid))
        state["is_empty"] = False

        # Special-case:full-sku-biomarkers: add related biomarkers if item is matched
        if key in sc_full_sku_biomarkers:
            for bid in sc_full_sku_biomarkers[key]:
                state["data"][(None, bid)].insert(0, (date, 0))

        # Special-case:full-sku-medical-exams: add related exam types if item is matched
        if key in sc_full_sku_medical_exams:
            for meid in sc_full_sku_medical_exams[key]:
                state["data"][(meid, None)].insert(0, (date, 0))

        # 3.
        if out_of_range:  # can not be reached if full is collected
            for k, v in state["data"].items():
                for idx, (meddate, _) in list(enumerate(v))[::-1]:
                    if date + delta_checkup_days < meddate:
                        v.pop(idx)

        # 4.
        meddates = [i[-1][0] for i in state["data"].values() if i]
        state["date_from"] = min(meddates)
        state["date_to"] = max(meddates)

        # 5.
        if all(state["data"].values()):
            states["full"] = state
            break

        # 6.
        if states["partial"] and state["date_from"] > date_most_filled_state_expiration:
            progress = calculate_state_progress_by_groups(state)
            if (
                progress["total"]["progress"]
                > most_filled_biggest_progress["total"]["progress"]
            ):
                most_filled_biggest_progress = progress
                states["most_filled"] = copy.deepcopy(state)

    if not (states["full"] or states["partial"] or state["is_empty"]):
        states["partial"] = state

    # 7.
    for state in states.values():
        if not state:
            continue
        state.pop("is_empty")
        for key, value in state["data"].items():
            state["data"][key] = value[-1] if value else None

    return states


# Tasks
@app.task
def handle_checkup_matching_event_task(user_id, profile_uuid, sex, age):
    """
    Handle checkup matching event.
    1. Get user by id.
    2. Get all active non-personalized checkups by user and profile uuid.
    3. Match by one template from each category.
    4. Deactivate inactive non-personalized previous checkups.
    5. Create non-personalized checkups according new mathed templates.
    6. Create personalized checkup in case of base checkup existance.
        6.0. Get base checkup (only one per user is allowed).
        6.1. Get all active personalized checkups.
        6.2. Deactivate inactive personalized checkups.
        6.3. Get personalized template (only one per system is allowed).
        6.4. Create new personalized checkup (only one per user is allowed).
        6.5. Emit personalized checkup SKU rematching in FSMAPI event.
    7. Emit checkup calculation event.
    """

    # 1. Get user
    user = User.objects.filter(id=user_id).first()
    if not user:
        return

    # 2. Get all active non-personalized checkups
    checkups = models.CheckUp.objects.filter(
        user=user, profile_uuid=profile_uuid, is_personalized=False
    ).active()

    # 3. Match templates
    templates = models.CheckUpTemplate.match_templates_by_data({"sex": sex, "age": age})

    # get inactive checkup and new templates
    checkups = list(checkups)
    inactive, new = list(checkups), []
    for t in templates:
        exists = False
        for c in checkups:
            if c.template_id == t.id:
                inactive.remove(c)
                exists = True
        if not exists:
            new.append(t)

    # 4. Deactivate inactive non-personalized checkups
    models.CheckUp.objects.filter(id__in=[i.id for i in inactive]).update(
        is_active=False
    )

    # 5. Create new non-personalized checkups
    for template in new:
        checkup = models.CheckUp.objects.create(
            user=user,
            profile_uuid=profile_uuid,
            template=template,
            category=template.category,
            is_active=template.is_active,
            is_calculatable=template.is_calculatable,
            is_base=template.is_base,
            is_personalized=False,
            matched_at=timezone.now(),
        )
        for product in template.products.all():
            biomarkers = get_int_product_attribute_values_by_slug(product, "biomarkers")
            medical_exams = get_int_product_attribute_values_by_slug(
                product, "medical_exams"
            )
            checkup.products.add(
                product,
                through_defaults={
                    "meta": {
                        "ornament": {
                            "biomarkers": biomarkers,
                            "medical_exams": medical_exams,
                        }
                    }
                },
            )

    # 6. Create personalized checkup, only one per user:profile

    # 6.0. Get base checkup (only one per user is allowed)
    base = (
        models.CheckUp.objects.filter(
            user=user,
            profile_uuid=profile_uuid,
            is_personalized=False,
            is_base=True,
            is_calculatable=True,
        )
        .active()
        .first()
    )

    # 6.1. Get all active personalized checkups
    checkups = models.CheckUp.objects.filter(
        user=user, profile_uuid=profile_uuid, is_personalized=True
    ).active()
    checkups = [(base and c.parent_id == base.id, c) for c in checkups]
    inactive = [c for condition, c in checkups if not condition]
    personalized = next((c for condition, c in checkups if condition), None)

    # 6.2. Deactivate inactive personalized checkups
    models.CheckUp.objects.filter(id__in=[i.id for i in inactive]).update(
        is_active=False
    )

    if not personalized and base:
        # 6.3. Get personalized template (only one per system is allowed)
        personalized_template = (
            models.CheckUpTemplate.objects.filter(is_personalized=True).active().first()
        )

        # 6.4. Create new personalized checkup (only one per user is allowed)
        checkup = models.CheckUp.objects.create(
            user=user,
            profile_uuid=profile_uuid,
            template=personalized_template or base.template,
            parent=base,
            category=(personalized_template or base.template).category,
            is_active=base.template.is_active,
            is_calculatable=base.template.is_calculatable,
            is_base=base.template.is_base,
            is_personalized=True,
            matched_at=timezone.now(),
        )
        for product in base.template.products.all():
            biomarkers = get_int_product_attribute_values_by_slug(product, "biomarkers")
            medical_exams = get_int_product_attribute_values_by_slug(
                product, "medical_exams"
            )
            checkup.products.add(
                product,
                through_defaults={
                    "meta": {
                        "ornament": {
                            "biomarkers": biomarkers,
                            "medical_exams": medical_exams,
                        }
                    }
                },
            )

        # 6.5. Emit personalized checkup SKU rematching in FSMAPI event
        try:
            response = requests.post(
                f"{settings.ORNAMENT_API_INTERNAL_HOST}/internal/fsm-api/v1.0/fsm/variable-sku-match/run-processor",
                json={"ssoId": str(user.sso_id), "pid": str(profile_uuid)},
                timeout=(5, 15),
            )
        except (RequestException, Exception) as error:
            logger.critical(f"FSMAPI error: {error}")

    # 7. Emit checkup calculation event
    if new:
        handle_checkup_calculation_event_task.delay(user.id, profile_uuid)


@app.task
def handle_checkup_calculation_event_task(user_id, profile_uuid, history=None):
    """
    Handle checkup calculation event.
    1. Get user by id.
    2. Get all active checkups by user and profile uuid.
    3. Load full user medical history from data api by profile id.
    4. For each checkup do the following steps:
        4.0. Lock checkup or increment call required count and exit (continue for)
        4.1. Get most recent full, partial and most_filled states for each checkup.
        4.2. Check full, partial and most_filled is changed by medical history editing.
        4.3. Calculate new full, partial and most_filled states using history from data api.
        4.4. Create new checkup states according calcalation results.
        4.5. Update calculated_at datetime field in checkup.
        4.6. Set recall_required if call counter > 0.
    """
    # 1.
    user = User.objects.filter(id=user_id).first()
    if not user:
        return

    # 2.
    checkups = models.CheckUp.objects.filter(
        user=user, profile_uuid=profile_uuid, is_calculatable=True
    ).active()

    if not checkups:
        return

    # 3.
    if history is None:
        # history is not None in case of mass recalculation
        history = get_user_medical_history_from_dataapi(pid=profile_uuid)

    # 4.
    recall_required = False

    for checkup in checkups:
        lock_name = f"lock:checkup_calculation_event_task:{checkup.id}"
        with RedisBlockingCounterManager(name=lock_name) as manager:
            # 4.0.
            if not manager.lock:  # check checkup is locked
                continue

            locked = models.CheckUp.objects.filter(id=checkup.id).active().first()
            if not locked:
                continue

            # 4.1.
            qs_full = checkup.checkup_states.filter(status=CheckUpStateStatus.FULL)
            qs_partial = checkup.checkup_states.filter(
                status=CheckUpStateStatus.PARTIAL
            )
            qs_most_filled = checkup.checkup_states.filter(
                status=CheckUpStateStatus.MOST_FILLED
            )
            full = qs_full.order_by("-date_from").first()
            partial = qs_partial.order_by("-date_from").first()
            most_filled = qs_most_filled.order_by("-date_from").first()

            # 4.2.
            if full and not check_state_data_is_not_changed_in_history(full, history):
                qs_full.delete()
                full = None
            if partial and not check_state_data_is_not_changed_in_history(
                partial, history
            ):
                qs_partial.delete()
                partial = None
            if most_filled and not check_state_data_is_not_changed_in_history(
                most_filled, history
            ):
                qs_most_filled.delete()
                most_filled = None

            if not history:
                continue

            # 4.3.
            states = calculate_checkup_states_from_history(
                checkup.get_checkup_medical_scheme(), history
            )

            # 4.4.
            full_has_changes = states["full"] and (
                not full or not full.equals_to_raw_state(states["full"])
            )
            partial_has_changes = states["partial"] and (
                not partial or not partial.equals_to_raw_state(states["partial"])
            )
            most_filled_has_changes = states["most_filled"] and (
                not most_filled
                or not most_filled.equals_to_raw_state(states["most_filled"])
            )

            # Erase all previous fulls if no one full is calculated or we have changes
            if full_has_changes or not states["full"]:
                qs_full.delete()
            if full_has_changes:
                models.CheckUpState.objects.create_from_raw_state(
                    checkup=checkup,
                    status=CheckUpStateStatus.FULL,
                    state=states["full"],
                )

            # Erase all previous partials if no one partial is calculated or we have changes
            if partial_has_changes or not states["partial"]:
                qs_partial.delete()
            if partial_has_changes:
                if partial and partial.approvement == CheckUpStateApprovement.APPROVED:
                    approvement = CheckUpStateApprovement.APPROVED
                else:
                    approvement = CheckUpStateApprovement.NEED_TO_ASK
                models.CheckUpState.objects.create_from_raw_state(
                    checkup=checkup,
                    status=CheckUpStateStatus.PARTIAL,
                    approvement=approvement,
                    state=states["partial"],
                )

            # Erase all previous most_filleds if no one most_filled is calculated or we have changes
            if most_filled_has_changes or not states["most_filled"]:
                qs_most_filled.delete()
            if most_filled_has_changes:
                models.CheckUpState.objects.create_from_raw_state(
                    checkup=checkup,
                    status=CheckUpStateStatus.MOST_FILLED,
                    state=states["most_filled"],
                )

            # 4.5
            checkup.calculated_at = timezone.now()
            checkup.save()

            # 4.6
            if manager.get() > 0:
                recall_required = True

    if recall_required:
        handle_checkup_calculation_event_task.delay(user_id, profile_uuid)


@app.task
def handle_checkup_personalization_event_task(user_id, profile_uuid, matches):
    """
    Handle checkup personalization event.
    1. Get user by id.
    2. Get personalized checkup.
    3. Get base non-personalized checkup.
    4. Create personalized checkup if it does not exist.
    5. Sync personalized checkup with matches data from FSMAPI.
    6. Emit checkup calculation event.
    """
    is_changed = False

    # 1.
    user = User.objects.filter(id=user_id).first()
    if not user:
        return

    # 2.
    checkup = (
        models.CheckUp.objects.filter(
            user=user,
            profile_uuid=profile_uuid,
            parent__isnull=False,
            is_personalized=True,
            is_base=True,
            is_calculatable=True,
        )
        .active()
        .first()
    )

    # 3.
    base = (
        models.CheckUp.objects.filter(
            user=user,
            profile_uuid=profile_uuid,
            is_personalized=False,
            is_base=True,
            is_calculatable=True,
        )
        .active()
        .first()
    )

    # 4.
    if not checkup and not base:
        return
    elif not checkup:
        is_changed = True
        personalized_template = (
            models.CheckUpTemplate.objects.filter(is_personalized=True).active().first()
        )

        checkup = models.CheckUp.objects.create(
            user=user,
            profile_uuid=profile_uuid,
            template=personalized_template or base.template,
            parent=base,
            category=(personalized_template or base.template).category,
            is_active=base.template.is_active,
            is_calculatable=base.template.is_calculatable,
            is_base=base.template.is_base,
            is_personalized=True,
            matched_at=timezone.now(),
        )
        for product in base.template.products.all():
            biomarkers = get_int_product_attribute_values_by_slug(product, "biomarkers")
            medical_exams = get_int_product_attribute_values_by_slug(
                product, "medical_exams"
            )
            checkup.products.add(
                product,
                through_defaults={
                    "meta": {
                        "ornament": {
                            "biomarkers": biomarkers,
                            "medical_exams": medical_exams,
                        }
                    }
                },
            )

    # 5.
    ADD_RULE, REMOVE_RULE = "add", "remove"
    matches = {i["sku"]: i for i in matches}
    inactive = []

    # Get base checkup and personalized checkup products
    cu_base_products = checkup.parent.checkup_products.select_related("product").all()
    cu_base_products = {i.product.name: i for i in cu_base_products}
    checkup_products = checkup.checkup_products.select_related("product").all()
    checkup_products = {i.product.name: i for i in checkup_products}

    # Process REMOVE_RULE for non-personalized SKUs.
    for sku, bproduct in cu_base_products.items():
        actions = matches.get(sku, {}).get("actions", [])
        if sku in checkup_products and REMOVE_RULE in actions:
            # Remove non-personalized SKU by REMOVE_RULE.
            inactive.append(checkup_products[sku].id)
        elif not sku in checkup_products and not REMOVE_RULE in actions:
            biomarkers = get_int_product_attribute_values_by_slug(
                bproduct.product, "biomarkers"
            )
            medical_exams = get_int_product_attribute_values_by_slug(
                bproduct.product, "medical_exams"
            )
            # Revert non-personalized SKU in case of no more REMOVE_RULE exists.
            checkup.products.add(
                bproduct.product,
                through_defaults={
                    "meta": {
                        "ornament": {
                            "biomarkers": biomarkers,
                            "medical_exams": medical_exams,
                        }
                    },
                },
            )
            is_changed = True

    # Process ADD_RULE for personalized SKUs: add new and update existing ones.
    for sku, match in matches.items():
        if sku in cu_base_products or not ADD_RULE in match["actions"]:
            continue
        cproduct, rules = checkup_products.get(sku), match["rules"]
        if not cproduct:
            channel_slug = (
                user.city.channel.slug if user.city else settings.DEFAULT_CHANNEL_SLUG
            )
            product = (
                Product.objects.published(channel_slug=channel_slug)  # FIXME
                .filter(name=sku)
                .first()
            )
            if not product:
                continue
            biomarkers = get_int_product_attribute_values_by_slug(product, "biomarkers")
            medical_exams = get_int_product_attribute_values_by_slug(
                product, "medical_exams"
            )
            # Add new personalized SKU by ADD_RULE.
            checkup.products.add(
                product,
                through_defaults={
                    "is_personalized": True,
                    "meta": {
                        "ornament": {
                            "rules": rules,
                            "biomarkers": biomarkers,
                            "medical_exams": medical_exams,
                        },
                    },
                },
            )
            is_changed = True
        elif (
            not cproduct.is_personalized
            or not cproduct.meta["ornament"].get("rules", []) == rules
        ):
            # Update existing personalized SKU by ADD_RULE (personalize SKU).
            cproduct.is_personalized = True
            cproduct.meta["ornament"]["rules"] = rules
            cproduct.save()
            is_changed = True

    # Process remain checkup products.
    for sku, cproduct in checkup_products.items():
        actions = matches.get(sku, {}).get("actions", [])
        if not sku in cu_base_products and not ADD_RULE in actions:
            # Remove abandoned personalized SKU.
            inactive.append(cproduct.id)
        elif sku in cu_base_products and cproduct.is_personalized:
            # Depersonalize personalized SKU in case of new base product existance.
            cproduct.is_personalized = False
            cproduct.meta["ornament"].pop("rules", None)
            cproduct.save()
            is_changed = True

    # Delete inactive (removed) SKUs.
    if inactive:
        checkup.checkup_products.filter(id__in=inactive).delete()
        is_changed = True

    # Update personalized_at datetime field in checkup.
    checkup.personalized_at = timezone.now()
    checkup.save()

    # 6.
    if is_changed:
        handle_checkup_calculation_event_task.delay(user.id, profile_uuid)
