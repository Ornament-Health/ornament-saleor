import logging

import requests
from http import HTTPStatus
from django.conf import settings


logger = logging.getLogger(__name__)


class FSMApi:
    base_public_url_1_0 = f"{settings.ORNAMENT_API_PUBLIC_HOST}/public/fsm-api/v1.0"
    base_internal_url_1_0 = (
        f"{settings.ORNAMENT_API_INTERNAL_HOST}/internal/fsm-api/v1.0"
    )

    @staticmethod
    def get_rules_transitions(language: str) -> list[dict]:
        try:
            response = requests.get(
                f"{FSMApi.base_public_url_1_0}/fsm/variable-sku-match/rules-transitions",
                headers={"Accept-Language": language},
                timeout=(5, 15),
            )
        except (requests.RequestException, Exception) as error:
            logger.critical(f"FSMAPI error: {error}")
            return []

        if response.status_code != HTTPStatus.OK:
            logger.critical(
                f"FSMAPI error: response status_code {response.status_code} "
            )
            return []

        data = response.json()

        return data.get("variableSkuMatches", [])

    @staticmethod
    def run_processor(sso_id: str, pid: str) -> None:
        try:
            response = requests.post(
                f"{FSMApi.base_internal_url_1_0}/fsm/variable-sku-match/run-processor",
                json={"ssoId": sso_id, "pid": pid},
                timeout=(5, 15),
            )
        except (requests.RequestException, Exception) as error:
            logger.critical(f"FSMAPI error: {error}")
            return None

        if response.status_code != HTTPStatus.OK:
            logger.critical(
                f"FSMAPI error: response status_code {response.status_code} "
            )
            return None

        return None
