from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler

from . import settings
from .utils import is_pretty


def friendly_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if not response and settings.CATCH_ALL_EXCEPTIONS:
        exc = APIException(exc)
        response = exception_handler(exc, context)

    if response is not None:
        if is_pretty(response):
            return response
        error_message = response.data.get("detail", str(exc.__class__.__name__))
        error_code = settings.FRIENDLY_EXCEPTION_DICT.get(exc.__class__.__name__)
        data = response.data
        errors = []
        for field, value in data.items():
            message = value[0] if type(value) is list else value
            errors.append({"field": field, "message": message})

        response.data = {
            "code": error_code,
            "message": error_message,
            "status_code": response.status_code,
            "errors": errors,
        }

    return response
