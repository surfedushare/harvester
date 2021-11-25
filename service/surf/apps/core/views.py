from django.conf import settings
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, schema, permission_classes
from rest_framework.permissions import AllowAny


@api_view()
@permission_classes([AllowAny])
@schema(None)
def health_check(request):
    data = {"healthy": True, "ip": settings.IP}
    data.update(settings.PACKAGE_INFO)
    return Response(data, status.HTTP_200_OK)


def robots_txt(request):
    return render(request, "robots.txt")
