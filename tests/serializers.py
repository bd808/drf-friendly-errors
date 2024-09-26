from django.template.defaultfilters import title
from rest_framework import serializers, validators
from rest_framework.exceptions import ValidationError

from rest_framework_friendly_errors.mixins import FriendlyErrorMessagesMixin
from rest_framework_friendly_errors.settings import FRIENDLY_NON_FIELD_ERRORS

from .models import LANGUAGE_CHOICES, Field, FieldOption, Snippet


def is_proper_title(value):
    if value and value != title(value):
        raise ValidationError("Incorrect title")


class SnippetSerializer(FriendlyErrorMessagesMixin, serializers.Serializer):
    pk = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=10, validators=[is_proper_title])
    comment = serializers.CharField(max_length=255)
    code = serializers.CharField(style={"base_template": "textarea.html"})
    linenos = serializers.BooleanField(required=False)
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES)
    rating = serializers.DecimalField(max_digits=3, decimal_places=1)
    posted_date = serializers.DateTimeField()

    def validate_comment(self, value):
        if value[0] != value[0].upper():
            raise ValidationError("First letter must be an uppercase")
        return value

    def validate(self, attrs):
        # if phrase python is in title, language must be python as well
        language = attrs.get("language")
        title = attrs.get("title")
        if "python" in title.lower() and language != "python":
            raise ValidationError("Must be a python language")
        return attrs

    FIELD_VALIDATION_ERRORS = {"validate_comment": 5000, "is_proper_title": 5001}

    NON_FIELD_ERRORS = {"Must be a python language": 8000}


class RegisterSingleFieldErrorSerializer(SnippetSerializer):
    """
    Serializer to test registration of single field error
    """

    def validate(self, attrs):
        # if phrase python is in title, language must be python as well
        language = attrs.get("language")
        title = attrs.get("title")
        if "python" in title.lower() and language != "python":
            self.register_error(
                error_message="Python, fool!",
                error_key="invalid_choice",
                field_name="language",
            )
        return attrs


class RegisterMultipleFieldsErrorSerializer(SnippetSerializer):
    """
    Serializer to test registration of multiple fields error
    """

    def validate(self, attrs):
        errors = [
            {
                "error_message": "Python, fool!",
                "error_key": "invalid_choice",
                "field_name": "language",
            },
            {
                "error_message": "Not a boolean",
                "error_key": "invalid",
                "field_name": "linenos",
            },
        ]
        self.register_errors(errors)
        return attrs


class RegisterMixErrorSerializer(SnippetSerializer):
    """
    Serializer to test registration of mix field error and non field error.
    Registers one field error and one non field error
    """

    def validate(self, attrs):
        errors = [
            {
                "error_message": "Python, fool!",
                "error_code": "custom_code",
            },
            {
                "error_message": "Not a boolean",
                "error_key": "invalid",
                "field_name": "linenos",
            },
        ]
        self.register_errors(errors)
        return attrs


class NonFieldErrorAsStringSerializer(SnippetSerializer):
    """
    Serializer which raises non field error as string
    """

    def validate(self, attrs):
        raise ValidationError("Test")

    NON_FIELD_ERRORS = {"Test": FRIENDLY_NON_FIELD_ERRORS["invalid"]}


class NonFieldErrorAsStringWithCodeSerializer(SnippetSerializer):
    """
    Serializer which raises non field error as string with custom error code
    """

    def validate(self, attrs):
        raise ValidationError("Test", code="custom_code")


class FieldsErrorAsDictInValidateSerializer(SnippetSerializer):
    """
    Serializer which raises field errors as dict in `validate`
    """

    def validate(self, attrs):
        errors = {"title": "not good", "linenos": "not good", "language": "not good"}
        raise ValidationError(errors)

    FIELD_VALIDATION_ERRORS = {
        "title": "custom_code",
    }


class SnippetModelSerializer(FriendlyErrorMessagesMixin, serializers.ModelSerializer):
    class Meta:
        model = Snippet
        fields = "__all__"

    def validate_comment(self, value):
        if value[0] != value[0].upper():
            raise ValidationError("First letter must be an uppercase")
        return value

    def validate(self, attrs):
        # if phrase python is in title, language must be python as well
        language = attrs.get("language")
        title = attrs.get("title")
        if "python" in title.lower() and language != "python":
            raise ValidationError("Must be a python language")
        return attrs

    FIELD_VALIDATION_ERRORS = {
        "validate_comment": "validate_comment",
        "is_proper_title": "incorrect_title",
    }

    NON_FIELD_ERRORS = {
        "Must be a python language": FRIENDLY_NON_FIELD_ERRORS["invalid"]
    }


class AnotherSnippetModelSerializer(
    FriendlyErrorMessagesMixin, serializers.ModelSerializer
):
    class Meta:
        model = Snippet
        fields = "__all__"

    def validate_comment(self, value):
        if value[0] != value[0].upper():
            raise ValidationError("First letter must be an uppercase")
        return value

    def validate(self, attrs):
        # if phrase python is in title, language must be python as well
        language = attrs.get("language")
        title = attrs.get("title")
        if "python" in title.lower() and language != "python":
            self.register_error(
                error_message="Python, fool!",
                error_key="invalid_choice",
                field_name="language",
            )
        return attrs

    FIELD_VALIDATION_ERRORS = {
        "validate_comment": 5000,
        "is_proper_title": "incorrect_title",
    }

    NON_FIELD_ERRORS = {"Must be a python language": 8000}


class ThirdSnippetModelSerializer(
    FriendlyErrorMessagesMixin, serializers.ModelSerializer
):
    class Meta:
        model = Snippet
        fields = "__all__"

    def validate_comment(self, value):
        if value[0] != value[0].upper():
            self.register_error(
                "First letter must be an uppercase",
                field_name="comment",
                error_key="blank",
            )
        return value


class SnippetValidator(FriendlyErrorMessagesMixin, serializers.Serializer):
    title = serializers.SlugRelatedField(
        queryset=Snippet.objects.all(), slug_field="title"
    )


class FieldOptionModelSerializer(
    FriendlyErrorMessagesMixin, serializers.ModelSerializer
):
    value = serializers.IntegerField(
        validators=[validators.UniqueValidator(queryset=FieldOption.objects.all())]
    )

    class Meta:
        model = FieldOption
        fields = ["value"]

    def create(self, validated_data):
        validated_data["field"] = self.context["field"]
        return FieldOption.objects.create(**validated_data)


class FieldModelSerializer(FriendlyErrorMessagesMixin, serializers.ModelSerializer):
    label = serializers.CharField(max_length=10)
    options = FieldOptionModelSerializer(many=True, required=False)

    class Meta:
        model = Field
        fields = ["label", "options"]
