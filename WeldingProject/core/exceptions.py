"""
Custom DRF exception handling: map ProtectedError to 409 so delete-with-FK returns a clear response.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.db.models import ProtectedError


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return response
    if isinstance(exc, ProtectedError):
        return Response(
            {"detail": "Cannot delete: this record is in use by other data."},
            status=status.HTTP_409_CONFLICT,
        )
    return None
