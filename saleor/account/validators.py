from django.core.exceptions import ValidationError
from phonenumber_field.phonenumber import to_python
from phonenumbers.phonenumberutil import is_possible_number

from .error_codes import AccountErrorCode
from django.conf import settings


def validate_possible_number(phone, country=None):
    if not settings.ENABLE_PHONE_VALIDATION:
        # Without phone_number.is_valid
        phone_number = to_python(phone, country)
        if (
            phone_number
            and not is_possible_number(phone_number)
        ):
            raise ValidationError(
                "The phone number entered is not valid.",
                code=AccountErrorCode.INVALID.value,
            )
        return phone_number

    phone_number = to_python(phone, country)
    if (
        phone_number
        and not is_possible_number(phone_number)
        or not phone_number.is_valid()
    ):
        raise ValidationError(
            "The phone number entered is not valid.",
            code=AccountErrorCode.INVALID.value,
        )
    return phone_number
