from rest_framework.generics import GenericAPIView
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)

from .models import Snippet
from .serializers import AnotherSnippetModelSerializer, SnippetModelSerializer


class SnippetList(ListModelMixin, CreateModelMixin, GenericAPIView):
    queryset = Snippet.objects.all()
    serializer_class = SnippetModelSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class Snippet2List(ListModelMixin, CreateModelMixin, GenericAPIView):
    queryset = Snippet.objects.all()
    serializer_class = AnotherSnippetModelSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class SnippetDetail(RetrieveModelMixin, UpdateModelMixin, GenericAPIView):
    queryset = Snippet.objects.all()
    serializer_class = SnippetModelSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
