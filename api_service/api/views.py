from django.contrib.auth.models import User
from django.http import HttpResponse

from rest_framework.generics import RetrieveUpdateAPIView

from api.serializers import UserSerializer


def do_nothing(request):
    """default do-nothing view"""
    return HttpResponse("<h1>Snap back to reality!</h1>")


class UserRetrieveUpdateView(RetrieveUpdateAPIView):
    """Serving api/me/ endpoint simple retrieve/update view"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
