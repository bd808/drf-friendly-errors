from __future__ import unicode_literals

from django.conf import settings as dj_settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.utils.encoding import force_text
from rest_framework.exceptions import ErrorDetail
from rest_framework.exceptions import ValidationError as RestValidationError
from rest_framework.settings import api_settings
from rest_framework.utils.serializer_helpers import ReturnDict

from . import settings
from .field_map import FieldMap


class FriendlyErrorMessagesMixin(FieldMap):
    """
    A serializer mixin which formats the `serializer.ValidationError` message
    according to friendly format.
    """

    FIELD_VALIDATION_ERRORS = {}
    NON_FIELD_ERRORS = {}

    def __init__(self, *args, **kwargs):
        self.registered_errors = {}
        super(FriendlyErrorMessagesMixin, self).__init__(*args, **kwargs)

    @property
    def errors(self):
        ugly_errors = super(FriendlyErrorMessagesMixin, self).errors
        pretty_errors = self.build_pretty_errors(ugly_errors)
        return ReturnDict(pretty_errors, serializer=self)

    def register_errors(self, errors):
        for error_details in errors:
            error_details["raise_validation_error"] = False
            self.register_error(**error_details)
        raise RestValidationError(self.registered_errors)

    def register_error(
        self,
        error_message,
        field_name=None,
        error_key=None,
        error_code=None,
        meta=None,
        raise_validation_error=True,
    ):
        if field_name is None:
            if error_code is None:
                raise ValueError(
                    "For non field error you must provide " "an error code"
                )
            error = {"code": error_code, "message": error_message, "field": None}
            key = "%s_%s" % (error_message, error_code)
        else:
            key = field_name
            field_instance = self.fields.get(field_name)
            if field_instance is None:
                raise ValueError("Incorrect field name")
            field_type = field_instance.__class__.__name__
            if error_key is None and error_code is None:
                raise ValueError(
                    "You have to provide either error key" " or error code"
                )
            if error_code is None:
                try:
                    error_code = settings.FRIENDLY_FIELD_ERRORS[field_type].get(
                        error_key
                    )
                except KeyError:
                    raise ValueError('Unknown field type: "%s"' % field_type)
                if error_code is None:
                    raise ValueError(
                        'Unknown error key: "%s" '
                        'for field type: "%s"' % (error_key, field_type)
                    )
            error = {"code": error_code, "field": field_name, "message": error_message}

        if meta is not None:
            error["meta"] = meta

        if field_name is not None:
            self.registered_errors[field_name] = [error]
        else:
            non_field_errors_key = api_settings.NON_FIELD_ERRORS_KEY
            if not self.registered_errors.get(non_field_errors_key):
                self.registered_errors[non_field_errors_key] = []
            self.registered_errors[non_field_errors_key].append({key: [error]})

        if raise_validation_error:
            raise RestValidationError(self.registered_errors)

    def get_field_kwargs(self, field, field_data):
        field_type = field.__class__.__name__
        kwargs = {
            "data_type": type(field_data).__name__,
            "datatype": type(field_data).__name__,
        }
        if field_type in self.field_map["boolean"]:
            kwargs.update({"input": field_data})
        elif field_type in self.field_map["string"]:
            kwargs.update(
                {
                    "max_length": getattr(field, "max_length", None),
                    "min_length": getattr(field, "min_length", None),
                    "value": field_data,
                }
            )
        elif field_type in self.field_map["numeric"]:

            kwargs.update(
                {
                    "min_value": field.min_value,
                    "max_value": field.max_value,
                    "decimal_places": getattr(field, "decimal_places", None),
                    "max_decimal_places": getattr(field, "decimal_places", None),
                    "max_digits": getattr(field, "max_digits", None),
                }
            )
            max_digits = kwargs["max_digits"]
            decimal_places = kwargs["decimal_places"]
            if max_digits is not None and decimal_places is not None:
                whole_digits = max_digits - decimal_places
                kwargs.update({"max_whole_digits": whole_digits})
        elif field_type in self.field_map["date"].keys():
            kwargs.update({"format": self.field_map["date"][field_type]})
            field_timezone = getattr(field, "timezone", self._timezone())
            kwargs.update({"timezone": field_timezone})
        elif field_type in self.field_map["choice"]:
            kwargs.update(
                {"input": field_data, "input_type": type(field_data).__name__}
            )
        elif field_type in self.field_map["file"]:
            kwargs.update(
                {
                    "max_length": field.max_length,
                    "length": len(field.parent.data.get(field.source, "")),
                }
            )
        elif field_type in self.field_map["composite"]:
            kwargs.update(
                {
                    "input_type": type(field_data).__name__,
                    "max_length": getattr(field, "max_length", None),
                    "min_length": getattr(field, "min_length", None),
                }
            )
        elif (
            field_type in self.field_map["relation"]
            or field_type in self.field_map["serializer"]
        ):
            kwargs.update(
                {
                    "pk_value": field_data,
                    "input_type": type(field_data).__name__,
                    "slug_name": getattr(field, "slug_field", None),
                    "value": field_data,
                }
            )
        else:
            kwargs.update({"max_length": getattr(field, "max_length", None)})
        return kwargs

    @staticmethod
    def _timezone():
        return timezone.get_current_timezone() if dj_settings.USE_TZ else None

    @staticmethod
    def does_not_exist_many_to_many_handler(field, message, kwargs):
        unformatted = field.error_messages["does_not_exist"]
        new_kwargs = kwargs
        for value in kwargs["value"]:
            new_kwargs["value"] = value
            if unformatted.format(**new_kwargs) == message:
                return True
        return False

    def find_key(self, field, message, field_name):
        kwargs = self.get_field_kwargs(field, self.initial_data.get(field_name))
        for key in field.error_messages:
            if (
                key == "does_not_exist"
                and isinstance(kwargs.get("value"), list)
                and self.does_not_exist_many_to_many_handler(field, message, kwargs)
            ):
                return key
            unformatted = field.error_messages[key]
            try:
                if unformatted.format(**kwargs) == message:
                    return key
            except KeyError:
                pass
        if getattr(field, "child_relation", None):
            return self.find_key(
                field=field.child_relation, message=message, field_name=field_name
            )
        return None

    def _run_validator(self, validator, field, message, parent=None):
        try:
            if parent:
                initial_data = self.initial_data[parent.field_name]
                for data in initial_data:
                    if getattr(validator, "requires_context", False):
                        validator(data[field.field_name], field)
                    else:
                        validator(data[field.field_name])
            else:
                if getattr(validator, "requires_context", False):
                    validator(self.initial_data[field.field_name], field)
                else:
                    validator(self.initial_data[field.field_name])
        except (DjangoValidationError, RestValidationError) as err:
            err_message = err.detail[0] if hasattr(err, "detail") else err.message
            return err_message == message

    def find_validator(self, field, message):
        for validator in field.validators:
            if self._run_validator(validator, field, message):
                return validator

    def get_validator_error_code(self, validator, error):
        try:
            name = validator.__name__
        except AttributeError:
            name = validator.__class__.__name__
        return (
            self.FIELD_VALIDATION_ERRORS.get(name)
            or settings.FRIENDLY_VALIDATOR_ERRORS.get(name)
            or getattr(error, "code", None)
        )

    def is_default_error(self, error):
        return (
            settings.INVALID_DATA_MESSAGE.format(
                data_type=type(self.initial_data).__name__
            )
            == error
        )

    def get_field_error_entry(self, error, field):
        if field.field_name in self.registered_errors:
            err = self.registered_errors[field.field_name][0]
            if err["message"] == error["message"]:
                return err

        if isinstance(error, dict):
            _, errors = list(error.items())[0]
            error = force_text(errors[0])

        if self.is_default_error(error):
            return {
                "code": settings.FRIENDLY_NON_FIELD_ERRORS["invalid"],
                "field": field.field_name,
                "message": error,
            }
        field_type = field.__class__.__name__
        key = self.find_key(field, error, field.field_name)
        if not key:
            # Here we know that error was raised by a custom field validator
            validator = self.find_validator(field, error)
            if validator:
                try:
                    name = validator.__name__
                    code = self.FIELD_VALIDATION_ERRORS.get(
                        name
                    ) or settings.FRIENDLY_VALIDATOR_ERRORS.get(name)
                    return {"code": code, "field": field.field_name, "message": error}
                except AttributeError:
                    name = validator.__class__.__name__
                    code = self.FIELD_VALIDATION_ERRORS.get(
                        name
                    ) or settings.FRIENDLY_VALIDATOR_ERRORS.get(name)
                    return {"code": code, "field": field.field_name, "message": error}
                # Here we know that error was raised by a custom field validator
                # but field might be using another serializer
                # with `many=True` option
                if (
                    getattr(field, "child", None)
                    and getattr(field, "parent", None) == self
                    and field.__class__.__name__ == "ListSerializer"
                ):
                    for _, child_field in field.child.fields.items():
                        validator = self.find_validator(
                            child_field, error, parent=field
                        )
                        if validator:
                            code = self.get_validator_error_code(validator, error)
                            return {
                                "code": code,
                                "field": field.field_name,
                                "message": error,
                            }
            # Here we know that error was raised by custom validate method
            # in serializer
            validator = getattr(self, "validate_%s" % field.field_name, None)
            if validator and self._run_validator(validator, field, error):
                code = self.get_validator_error_code(validator, error)
                return {"code": code, "field": field.field_name, "message": error}
            # maybe field error was raised directly from `validate` method
            elif self.FIELD_VALIDATION_ERRORS.get(field.field_name, None):
                code = self.FIELD_VALIDATION_ERRORS.get(
                    field.field_name, getattr(error, "code", None)
                )
                return {"code": code, "field": field.field_name, "message": error}
            elif settings.FRIENDLY_FIELD_ERRORS.get(field_type, None):
                code = settings.FRIENDLY_FIELD_ERRORS.get(field_type, {}).get(
                    getattr(error, "code", None), None
                )
                return {"code": code, "field": field.field_name, "message": error}
            else:
                code = getattr(error, "code", None)
                return {"code": code, "field": field.field_name, "message": error}

        code = settings.FRIENDLY_FIELD_ERRORS.get(field_type, {}).get(
            key, getattr(error, "code", None)
        )
        return {"code": code, "field": field.field_name, "message": error}

    def get_field_error_entries(self, errors, field):
        if isinstance(errors, dict):
            errors = errors.get(field.field_name, [errors])
        error_entries = []
        for error in errors:
            error_entry = self.get_field_error_entry(error, field)
            if isinstance(error, dict):
                error_entry["field"] = error.get("field", field.field_name)
                error_entry["message"] = error
            error_entries.append(error_entry)
        return error_entries

    def get_non_field_error_entry(self, error):
        original_error = error
        if isinstance(error, dict):
            error = list(error.keys())[0]
        elif isinstance(error, ErrorDetail):
            error = str(error)

        registered_errors = self.registered_errors.get(
            api_settings.NON_FIELD_ERRORS_KEY, {}
        )
        for registered_error in registered_errors:
            if error in registered_error:
                return registered_error[error][0]

        if self.is_default_error(error):
            return {
                "code": settings.FRIENDLY_NON_FIELD_ERRORS.get("invalid"),
                "field": None,
                "message": error,
            }
        code = self.NON_FIELD_ERRORS.get(
            error,
            settings.FRIENDLY_NON_FIELD_ERRORS.get(
                error, getattr(original_error, "code", None)
            ),
        )
        return {"code": code, "field": None, "message": error}

    def get_non_field_error_entries(self, errors):
        return [self.get_non_field_error_entry(error) for error in errors]

    def build_pretty_errors(self, errors):
        pretty = []
        for error_type in errors:
            if error_type == "non_field_errors":
                pretty.extend(self.get_non_field_error_entries(errors[error_type]))
            else:
                field = self.fields[error_type]
                pretty.extend(
                    self.get_field_error_entries(errors[error_type], field),
                )
        if pretty:
            return {
                "code": settings.VALIDATION_FAILED_CODE,
                "message": settings.VALIDATION_FAILED_MESSAGE,
                "errors": pretty,
            }
        return {}
