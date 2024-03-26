import datetime
import logging
from typing import Optional

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
import requests

from saleor.ornament.checkupcenter import tasks
from saleor.ornament.checkupcenter.models import CheckUp


logger = logging.getLogger(__name__)


def get_user_info(sso_id: str) -> Optional[dict]:
    try:
        response = requests.post(
            f"{settings.ORNAMENT_API_INTERNAL_HOST}/internal/data-api/v1.0/user/login",
            json={"ssoId": sso_id},
            timeout=(5, 15),
        )
        data = response.json()
        return data
    except (requests.RequestException, Exception) as error:
        logger.critical(f"DATAAPI error: {error}")
        return None


def calculate_age(birthday: int):
    birthday_date = datetime.datetime.fromtimestamp(birthday)
    today = datetime.date.today()
    return today.year - birthday_date.year


class Command(BaseCommand):
    help = "Recalculate personilized checkups"

    def add_arguments(self, parser):
        parser.add_argument("--user_id_start", help="")
        parser.add_argument("--user_id_end", help="")

    def handle(self, *args, **options):
        user_start = options.get("user_id_start")
        user_end = options.get("user_id_end")

        checkups = CheckUp.objects.filter(
            user_id__in=[user_start, user_end], is_personalized=True
        ).active()

        known_profiles_data = {}

        for checkup in checkups:
            user_id = checkup.user_id
            pid = str(checkup.profile_uuid)

            profile_data = known_profiles_data.get(pid)

            if not profile_data:
                user_info = get_user_info(str(checkup.user.sso_id))

                if user_info:
                    for profile in user_info.get("profiles", []):
                        if all(
                            [
                                profile.get("pid"),
                                profile.get("sex"),
                                profile.get("birthday"),
                            ]
                        ):
                            known_profiles_data[profile["pid"]] = {
                                "sex": profile["sex"],
                                "age": calculate_age(profile["birthday"]),
                            }

            profile_data = known_profiles_data.get(pid)

            if not profile_data:
                raise CommandError(f"Can't find profile data: {pid}")

            logger.info(
                f"Deleting checkup {checkup.id} for user {user_id} and pid {pid}..."
            )

            checkup.products.clear()
            checkup.delete()

            logger.info(
                f"Recreating personilizing checkup for user {user_id} and pid {pid}..."
            )

            tasks.handle_checkup_matching_event_task.delay(
                user_id, pid, profile_data["sex"], profile_data["age"]
            )

        return
