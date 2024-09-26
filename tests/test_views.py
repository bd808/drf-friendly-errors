from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory

from rest_framework_friendly_errors.settings import (
    FRIENDLY_FIELD_ERRORS,
    FRIENDLY_NON_FIELD_ERRORS,
    FRIENDLY_VALIDATOR_ERRORS,
)

from . import BaseTestCase
from .models import Snippet
from .views import Snippet2List, SnippetDetail, SnippetList


class ListViewTestCase(BaseTestCase):
    def setUp(self):
        super(ListViewTestCase, self).setUp()
        self.factory = APIRequestFactory()

    def test_empty_list_view(self):
        request = self.factory.get(reverse("api:snippet-list"))
        response = SnippetList.as_view()(request)
        self.assertEqual(response.data, [])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_a_valid_snippet(self):
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_boolean(self):
        self.data_set["linenos"] = "A text instead of a bool"
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["BooleanField"]["invalid"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

    def test_invalid_char_field(self):
        # Too long string
        self.data_set["title"] = "Too Long Title For Defined Serializer"
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["CharField"]["max_length"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

        # Empty string
        self.data_set["title"] = ""
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["CharField"]["blank"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

        # No data provided
        self.data_set.pop("title")
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["CharField"]["required"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

    def test_invalid_choice_field(self):
        # invalid choice
        self.data_set["language"] = "brainfuck"
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["ChoiceField"]["invalid_choice"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

        # empty string
        self.data_set["language"] = ""
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["ChoiceField"]["invalid_choice"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

        # no data provided
        self.data_set.pop("language")
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["ChoiceField"]["required"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

    def test_invalid_decimal_field(self):
        # invalid
        self.data_set["rating"] = "text instead of float"
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["DecimalField"]["invalid"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

        # decimal places
        self.data_set["rating"] = 2.99
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["DecimalField"]["max_decimal_places"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

        # decimal max digits
        self.data_set["rating"] = 222.9
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["DecimalField"]["max_digits"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

    def test_datetime_field_error_content(self):
        # invalid
        self.data_set["posted_date"] = "text instead of date"
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["DateTimeField"]["invalid"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

    def test_custom_field_validation_method(self):
        self.data_set["comment"] = "comment"
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(errors[0]["code"], "validate_comment")

    def test_custom_field_validation_using_validators(self):
        self.data_set["title"] = "A title"
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(errors[0]["code"], "incorrect_title")

    def test_field_dependency_validation(self):
        self.data_set["title"] = "A Python"
        self.data_set["language"] = "c++"
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_NON_FIELD_ERRORS["invalid"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        c = errors[0]["code"]
        self.assertEqual(int(c), code)

    def test_error_registration(self):
        self.data_set["title"] = "A Python"
        self.data_set["language"] = "c++"
        request = self.factory.post(reverse("api:snippet2-list"), data=self.data_set)
        response = Snippet2List.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["ChoiceField"]["invalid_choice"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

    def test_couple_errors(self):
        self.data_set["comment"] = "comment"
        self.data_set["rating"] = "Not a number at all"

        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(len(errors), 2)

    def test_unique_constraint(self):
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        SnippetList.as_view()(request)
        request = self.factory.post(reverse("api:snippet-list"), data=self.data_set)
        response = SnippetList.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_VALIDATOR_ERRORS["UniqueValidator"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)


class DetailViewTestCase(BaseTestCase):
    def setUp(self):
        super(DetailViewTestCase, self).setUp()
        self.factory = APIRequestFactory()
        self.snippet = Snippet.objects.create(**self.data_set)

    def test_retrieve_object(self):
        request = self.factory.get(
            reverse("api:snippet-detail", kwargs={"pk": self.snippet.pk})
        )
        response = SnippetDetail.as_view()(request, pk=self.snippet.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_snippet(self):
        self.data_set["code"] = "def foo(bar):\n\treturn bar"
        request = self.factory.put(
            reverse("api:snippet-detail", kwargs={"pk": self.snippet.pk}),
            data=self.data_set,
        )
        response = SnippetDetail.as_view()(request, pk=self.snippet.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], "def foo(bar):\n\treturn bar")

    def update_invalid_boolean(self):
        self.data_set["linenos"] = "A text instead of a bool"
        request = self.factory.put(
            reverse("api:snippet-detail", kwargs={"pk": self.snippet.pk}),
            data=self.data_set,
        )
        response = SnippetDetail.as_view()(request, pk=self.snippet.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["BooleanField"]["invalid"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

    def test_upload_invalid_char_field(self):
        # Too long string
        self.data_set["title"] = "Too Long Title For Defined Serializer"
        request = self.factory.put(
            reverse("api:snippet-detail", kwargs={"pk": self.snippet.pk}),
            data=self.data_set,
        )
        response = SnippetDetail.as_view()(request, pk=self.snippet.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["CharField"]["max_length"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

        # Empty string
        self.data_set["title"] = ""
        request = self.factory.put(
            reverse("api:snippet-detail", kwargs={"pk": self.snippet.pk}),
            data=self.data_set,
        )
        response = SnippetDetail.as_view()(request, pk=self.snippet.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["CharField"]["blank"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

        # No data provided
        self.data_set.pop("title")
        request = self.factory.put(
            reverse("api:snippet-detail", kwargs={"pk": self.snippet.pk}),
            data=self.data_set,
        )
        response = SnippetDetail.as_view()(request, pk=self.snippet.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["CharField"]["required"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

    def test_upload_invalid_choice_field(self):
        # invalid choice
        self.data_set["language"] = "brainfuck"
        request = self.factory.put(
            reverse("api:snippet-detail", kwargs={"pk": self.snippet.pk}),
            data=self.data_set,
        )
        response = SnippetDetail.as_view()(request, pk=self.snippet.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["ChoiceField"]["invalid_choice"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

        # empty string
        self.data_set["language"] = ""
        request = self.factory.put(
            reverse("api:snippet-detail", kwargs={"pk": self.snippet.pk}),
            data=self.data_set,
        )
        response = SnippetDetail.as_view()(request, pk=self.snippet.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["ChoiceField"]["invalid_choice"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

        # no data provided
        self.data_set.pop("language")
        request = self.factory.put(
            reverse("api:snippet-detail", kwargs={"pk": self.snippet.pk}),
            data=self.data_set,
        )
        response = SnippetDetail.as_view()(request, pk=self.snippet.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["ChoiceField"]["required"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

    def test_upload_invalid_decimal_field(self):
        # invalid
        self.data_set["rating"] = "text instead of float"
        request = self.factory.put(
            reverse("api:snippet-detail", kwargs={"pk": self.snippet.pk}),
            data=self.data_set,
        )
        response = SnippetDetail.as_view()(request, pk=self.snippet.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["DecimalField"]["invalid"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

        # decimal places
        self.data_set["rating"] = 2.99
        request = self.factory.put(
            reverse("api:snippet-detail", kwargs={"pk": self.snippet.pk}),
            data=self.data_set,
        )
        response = SnippetDetail.as_view()(request, pk=self.snippet.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["DecimalField"]["max_decimal_places"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

        # decimal max digits
        self.data_set["rating"] = 222.9
        request = self.factory.put(
            reverse("api:snippet-detail", kwargs={"pk": self.snippet.pk}),
            data=self.data_set,
        )
        response = SnippetDetail.as_view()(request, pk=self.snippet.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["DecimalField"]["max_digits"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

    def test_datetime_field_error_content(self):
        # invalid
        self.data_set["posted_date"] = "text instead of date"
        request = self.factory.put(
            reverse("api:snippet-detail", kwargs={"pk": self.snippet.pk}),
            data=self.data_set,
        )
        response = SnippetDetail.as_view()(request, pk=self.snippet.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_FIELD_ERRORS["DateTimeField"]["invalid"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)

    def test_cannot_update_to_not_unique_watermark(self):
        self.data_set["watermark"] = "TEST2"
        Snippet.objects.create(**self.data_set)

        request = self.factory.put(
            reverse("api:snippet-detail", kwargs={"pk": self.snippet.pk}),
            data=self.data_set,
        )
        response = SnippetDetail.as_view()(request, pk=self.snippet.pk)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code = FRIENDLY_VALIDATOR_ERRORS["UniqueValidator"]
        errors = response.data.get("errors")
        self.assertIsNotNone(errors)
        self.assertEqual(type(errors), list)
        self.assertEqual(int(errors[0]["code"]), code)
