from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
from django.contrib.auth import authenticate, login
from catalog.services.email_service import (
    EmailService,
    ExternalServiceUnavailable,
    ExternalServiceError
)
import logging

def validation_error(details):
    return JsonResponse(
        {
            "error": "validation_error",
            "message": "Datos de entrada inválidos",
            "details": details,
        },
        status=400,
    )

@csrf_exempt
@require_POST
def register(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return validation_error({"body": "JSON mal formado"})

    if not data:
        return validation_error({"body": "El JSON no puede estar vacío"})

    username = data.get("username")
    password = data.get("password")
    
    details = {}

    # Validar username
    if "username" not in data:
        details["username"] = ["campo obligatorio"]
    elif not isinstance(username, str):
        details["username"] = ["debe ser string"]
    elif User.objects.filter(username=username).exists():
        details["username"] = ["ya está en uso"]

    # Validar password
    if "password" not in data:
        details["password"] = ["campo obligatorio"]
    elif not isinstance(password, str):
        details["password"] = ["debe ser string"]
    elif len(password) < 8:
        details["password"] = ["debe tener al menos 8 caracteres"]

    if details:
        return JsonResponse({"error": "validation_error", "details": details}, status=400)

    # Crear usuario
    user = User.objects.create_user(username=username, password=password)

    return JsonResponse(
        {"id": user.id, "username": user.username},
        status=201
    )


@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "method_not_allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "validation_error"}, status=400)

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JsonResponse({"error": "validation_error"}, status=400)

    user = authenticate(username=username, password=password)

    if user is None:
        return JsonResponse(
            {"error": "unauthorized", "message": "Credenciales incorrectas"},
            status=401,
        )

    login(request, user)

    return JsonResponse({"id": user.id, "username": user.username}, status=200)


def me(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "unauthorized", "message": "No autenticado"},
            status=401,
        )

    return JsonResponse({"id": request.user.id, "username": request.user.username})


# -------------------------
# CAMBIO DE CONTRASEÑA
# -------------------------

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    current_password = request.data.get("current_password")
    new_password = request.data.get("new_password")

    if not user.check_password(current_password):
        return Response({"error": "Contraseña actual incorrecta"}, status=400)

    user.set_password(new_password)
    user.save()
    return Response({"message": "Contraseña cambiada correctamente"})
