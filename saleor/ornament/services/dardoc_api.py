import asyncio
from datetime import datetime
import logging
from dataclasses import dataclass, fields
from typing import Optional

import aiohttp
from asgiref.sync import async_to_sync
from django.conf import settings
import requests

logger = logging.getLogger(__name__)


def filter_dict_for_dataclass(class_instance, input_dict):
    field_names = {f.name for f in fields(class_instance)}
    return {k: v for k, v in input_dict.items() if k in field_names}


@dataclass
class DarDocApiResponseBase:
    success: int
    message: Optional[str] = None


@dataclass
class DarDocApiUser:
    userUUID: str
    email: str
    phoneNumber: str
    userName: str


@dataclass
class DarDocApiPatient:
    _id: str
    userUUID: str


@dataclass
class DarDocApiAddress:
    _id: str
    userUUID: str
    lattitude: str
    longitude: str
    area: str


@dataclass
class DarDocApiUserByPhone(DarDocApiResponseBase):
    userUUID: Optional[str] = None
    email: Optional[str] = None
    user: Optional[DarDocApiUser] = None


@dataclass
class DarDocApiAddressByUserId(DarDocApiResponseBase):
    addresses: Optional[list[DarDocApiAddress]] = None


@dataclass
class DarDocApiAddressSaveResponse(DarDocApiResponseBase):
    addressID: Optional[str] = None


@dataclass
class DarDocApiUserById(DarDocApiResponseBase):
    user: Optional[DarDocApiUser] = None


@dataclass
class DarDocApiPatientsByUserId(DarDocApiResponseBase):
    patients: Optional[list[DarDocApiPatient]] = None


@dataclass
class DarDocApiUserCreateResponse(DarDocApiResponseBase):
    userUUID: Optional[str] = None


@dataclass
class DarDocApiAreaIsServiceableResponse:
    success: int
    isServiceable: int
    area: Optional[str] = None
    city: Optional[str] = None


@dataclass
class DarDocApiDateTimeslots:
    date: datetime
    timeslots: list[str]


class DarDocApi:
    date_format = "%d/%m/%Y"

    def __init__(self):
        self.base_url = f"{settings.DARDOC_API_HOST}/api/v1"
        self.base_headers = {"Authorization": f"Bearer {settings.DARDOC_API_TOKEN}"}
        self.serviceUUID = settings.DARDOC_SERVICE_UUID

    def user_get(self, dardoc_user_id: str) -> Optional[DarDocApiUserById]:
        try:
            response = requests.get(
                f"{self.base_url}/users/get-by-user-id-ornament/{dardoc_user_id}",
                headers=self.base_headers,
                timeout=(5, 15),
            )
            data = response.json()
            user = data.get("user")

            return (
                DarDocApiUserById(
                    success=data.get("success"),
                    user=DarDocApiUser(
                        **filter_dict_for_dataclass(DarDocApiUser, user)
                    ),
                )
                if user
                else None
            )
        except Exception as error:
            logger.critical(f"DarDocApi user_get error: {error}")
            return None

    def user_get_by_phone(self, phone_number: str) -> Optional[DarDocApiUserByPhone]:
        error_base_message = "DarDocApi user_get_by_phone error;"

        try:
            response = requests.get(
                f"{self.base_url}/users/get-user-by-phone-number-ornament/{phone_number}",
                headers=self.base_headers,
                timeout=(5, 15),
            )
            data = response.json()
            success = data.get("success")
            message = data.get("message")

            if not success:
                logger.critical(f"{error_base_message} {message}")
                return None

            user = data.get("user")

            return (
                DarDocApiUserByPhone(
                    success=success,
                    message=message,
                    userUUID=data.get("userUUID"),
                    email=data.get("email"),
                    user=DarDocApiUser(
                        **filter_dict_for_dataclass(DarDocApiUser, user)
                    ),
                )
                if user
                else None
            )
        except Exception as error:
            logger.critical(f"{error_base_message} {error}")
            return None

    def user_create(
        self, email: str, phone_number: str, name: str
    ) -> Optional[DarDocApiUserCreateResponse]:
        error_base_message = "DarDocApi user_create error;"

        try:
            response = requests.post(
                f"{self.base_url}/users/create-user-for-ornament",
                json={"email": email, "number": phone_number, "name": name},
                headers=self.base_headers,
                timeout=(5, 15),
            )
            data = response.json()
            data = DarDocApiUserCreateResponse(**data)

            if not data.success:
                logger.critical(f"{error_base_message} {data.message}")
                return None

            return data
        except Exception as error:
            logger.critical(f"{error_base_message} {error}")
            return None

    def patents_get(self, dardoc_user_id: str) -> Optional[DarDocApiPatientsByUserId]:
        error_base_message = "DarDocApi patents_get error;"

        try:
            response = requests.get(
                f"{self.base_url}/patients/fetch-patients-for-ornament/{dardoc_user_id}",
                headers=self.base_headers,
                timeout=(5, 15),
            )
            data = response.json()
            success = data.get("success")
            message = data.get("message")

            if not success:
                logger.critical(f"{error_base_message} {message}")
                return None

            patients = data.get("patients", [])

            return DarDocApiPatientsByUserId(
                success=success,
                message=message,
                patients=[
                    DarDocApiPatient(**filter_dict_for_dataclass(DarDocApiPatient, p))
                    for p in patients
                ],
            )
        except Exception as error:
            logger.critical(f"{error_base_message} {error}")
            return None

    def address_get_by_user_id(
        self, user_id: str
    ) -> Optional[DarDocApiAddressByUserId]:
        error_base_message = "DarDocApi address_get_by_user_id error;"

        try:
            response = requests.get(
                f"{self.base_url}/addresses/get-addresses-for-ornament/{user_id}",
                headers=self.base_headers,
                timeout=(5, 15),
            )
            data = response.json()
            success = data.get("success")
            message = data.get("message")

            if not success:
                logger.critical(f"{error_base_message} {message}")
                return None

            addresses = data.get("addresses")

            return (
                DarDocApiAddressByUserId(
                    success=success,
                    message=message,
                    addresses=[
                        DarDocApiAddress(
                            **filter_dict_for_dataclass(DarDocApiAddress, address)
                        )
                        for address in addresses
                    ],
                )
                if addresses
                else None
            )
        except Exception as error:
            logger.critical(f"{error_base_message} {error}")
            return None

    def address_save(
        self,
        user_id: str,
        lat: str,
        lng: str,
        flat_or_villa: str = "",
        building_name: str = "",
        floor_number: str = "",
    ) -> Optional[DarDocApiAddressSaveResponse]:
        error_base_message = "DarDocApi address_save error;"

        try:
            response = requests.post(
                f"{self.base_url}/addresses/save-address-ornament",
                json={
                    "userUUID": user_id,
                    "lattitude": lat,
                    "longitude": lng,
                    "flatOrVillaNumber": flat_or_villa,
                    "buildingName": building_name,
                    "floorNumber": floor_number,
                },
                headers=self.base_headers,
                timeout=(5, 15),
            )
            data = response.json()
            data = DarDocApiAddressSaveResponse(**data)

            if not data.success:
                logger.critical(f"{error_base_message} {data.message}")
                return None

            return data
        except Exception as error:
            logger.critical(f"{error_base_message} {error}")
            return None

    def address_edit(
        self,
        user_id: str,
        address_id: str,
        lat: str,
        lng: str,
        flat_or_villa: str = "",
        building_name: str = "",
        floor_number: str = "",
    ) -> bool:
        error_base_message = "DarDocApi address_edit error;"

        try:
            response = requests.post(
                f"{self.base_url}/addresses/edit-address-ornament",
                json={
                    "userUUID": user_id,
                    "addressUUID": address_id,
                    "lattitude": lat,
                    "longitude": lng,
                    "flatOrVillaNumber": flat_or_villa,
                    "buildingName": building_name,
                    "floorNumber": floor_number,
                },
                headers=self.base_headers,
                timeout=(5, 15),
            )
            data = response.json()
            data = DarDocApiAddressSaveResponse(**data)

            if not data.success:
                logger.critical(f"{error_base_message} {data.message}")
                return False

            return True
        except Exception as error:
            logger.critical(f"{error_base_message} {error}")
            return False

    def is_area_serviceable(
        self,
        lat: str,
        lng: str,
    ) -> Optional[DarDocApiAreaIsServiceableResponse]:
        error_base_message = "DarDocApi is_area_serviceable error;"

        try:
            response = requests.post(
                f"{self.base_url}/users/check-the-area-is-serviceable-for-ornament",
                json={
                    "lat": lat,
                    "lng": lng,
                },
                headers=self.base_headers,
                timeout=(5, 15),
            )
            data = response.json()
            data = DarDocApiAreaIsServiceableResponse(**data)

            if not data.success:
                logger.critical(error_base_message)
                return None

            return data
        except Exception as error:
            logger.critical(f"{error_base_message} {error}")
            return None

    def disabled_dates(
        self,
        emirate: str,
    ) -> list[datetime]:
        error_base_message = "DarDocApi disabled_dates error;"

        try:
            response = requests.post(
                f"{self.base_url}/nursetimeslots/disableddatesallnurse-ornament",
                json={
                    "serviceUUID": self.serviceUUID,
                    "emirate": emirate,
                },
                headers=self.base_headers,
                timeout=(5, 15),
            )
            data = response.json()
            dates = data.get("disabledDates", [])

            if not data.get("success"):
                logger.critical(error_base_message)
                return []

            return [datetime.strptime(d, self.date_format) for d in dates]

        except Exception as error:
            logger.critical(f"{error_base_message} {error}")
            return []

    @async_to_sync
    async def timeslots_by_dates(
        self,
        dates: list[datetime],
        emirate: str,
    ) -> list[DarDocApiDateTimeslots]:
        error_base_message = "DarDocApi timeslots_by_dates error;"

        try:
            async with aiohttp.ClientSession() as session:
                requests = [
                    session.post(
                        f"{self.base_url}/nursetimeslots/normaltimeslots-ornament",
                        json={
                            "dateToCheck": d.strftime(self.date_format),
                            "serviceUUID": self.serviceUUID,
                            "emirate": emirate,
                        },
                        headers=self.base_headers,
                    )
                    for d in dates
                ]
                result = await asyncio.gather(*requests)

                results = [await r.json() for r in result]

                return [
                    DarDocApiDateTimeslots(
                        date=d,
                        timeslots=(
                            [
                                t.get("timeSlot")
                                for t in results[num].get("timeSlotsAvailable", [])
                            ]
                            if results[num].get("success")
                            else []
                        ),
                    )
                    for num, d in enumerate(dates)
                ]

        except Exception as error:
            logger.critical(f"{error_base_message} {error}")
            return []
