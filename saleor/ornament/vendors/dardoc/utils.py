import logging
from typing import Optional

from saleor.account.models import Address, User
from saleor.ornament.services.dardoc_api import DarDocApi

logger = logging.getLogger(__name__)


def get_or_create_dardoc_user(
    user: User, shipping_address_instance: Address
) -> Optional[str]:
    error_message = "DarDoc get_or_create_dardoc_user error;"
    dardoc_api = DarDocApi()

    saved_dardoc_user_id = user.get_value_from_metadata("dardoc_user_id")
    dardoc_user_id = None

    if saved_dardoc_user_id:
        dardoc_user = dardoc_api.user_get(saved_dardoc_user_id)
        dardoc_user_id = (
            dardoc_user.user.userUUID if dardoc_user and dardoc_user.user else None
        )

    phone = (
        shipping_address_instance.phone.as_e164
        if shipping_address_instance.phone
        else None
    )

    if not dardoc_user_id and phone:
        dardoc_user = dardoc_api.user_get_by_phone(phone)
        dardoc_user_id = dardoc_user.userUUID if dardoc_user else None

    if not dardoc_user_id:
        email = user.email
        name = (
            shipping_address_instance.first_name
            + " "
            + shipping_address_instance.last_name
        )
        name = name.strip()

        if not all([email, phone, name]):
            logger.error(
                f"{error_message}; Shipping address doesn't contain all required fields; email: {email}, phone: {phone}, name: {name}"
            )
            return None

        dardoc_user = dardoc_api.user_create(email=email, phone_number=phone, name=name)

        if not dardoc_user or not dardoc_user.userUUID:
            logger.error(f"{error_message}; DarDoc user has not been created!")
            return None

        dardoc_user_id = dardoc_user.userUUID

    if dardoc_user_id != saved_dardoc_user_id:
        user.store_value_in_metadata({"dardoc_user_id": dardoc_user_id})
        user.save(update_fields=["metadata"])

    return dardoc_user_id


def get_dardoc_patient_id(user: User, dardoc_user_id: str) -> str:
    dardoc_api = DarDocApi()
    patient_id = ""

    dardoc_patient_id = user.get_value_from_metadata("dardoc_patient_id")

    if dardoc_patient_id:
        patient_id = dardoc_patient_id
    else:
        dardoc_patients = dardoc_api.patents_get(dardoc_user_id)
        if dardoc_patients and dardoc_patients.patients:
            patient_id = [p._id for p in dardoc_patients.patients][0]

    if not dardoc_patient_id or dardoc_patient_id != patient_id:
        user.store_value_in_metadata({"dardoc_patient_id": patient_id})
        user.save(update_fields=["metadata"])

    return patient_id


def get_dardoc_address_id(
    user: User, dardoc_user_id: str, shipping_address_instance: Address
) -> Optional[str]:
    error_message = "DarDoc get_dardoc_address_id error;"
    dardoc_api = DarDocApi()
    address_id = None
    update = False

    saved_address_id = user.get_value_from_metadata("dardoc_address_id")

    if saved_address_id:
        address_id = saved_address_id
        update = True
    else:
        dardoc_addresses = dardoc_api.address_get_by_user_id(dardoc_user_id)
        if dardoc_addresses and dardoc_addresses.addresses:
            address_id = [a._id for a in dardoc_addresses.addresses][0]
            update = True

    lat = shipping_address_instance.get_value_from_metadata("dardoc_address_lat")
    lng = shipping_address_instance.get_value_from_metadata("dardoc_address_lng")

    if not all([lat, lng]):
        logger.error(
            f"{error_message}; Shipping address metadata doesn't contain lat and lng! dardoc_address_lat: {lat}, dardoc_address_lng: {lng}"
        )
        return None

    if not address_id:
        address_id_res = dardoc_api.address_save(dardoc_user_id, lat, lng)

        if not address_id_res or not address_id_res.addressID:
            logger.error(
                f"{error_message}; DarDoc address has not been created! dardoc_user_id: {dardoc_user_id}"
            )
            return None

        address_id = address_id_res.addressID

    if address_id:
        if address_id != saved_address_id:
            user.store_value_in_metadata({"dardoc_address_id": address_id})
            user.save(update_fields=["metadata"])
        if update:
            dardoc_api.address_edit(dardoc_user_id, address_id, lat, lng)

    return address_id
