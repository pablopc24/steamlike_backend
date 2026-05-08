from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
from django.contrib.auth import authenticate, login


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

    details = {}

    username = data.get("username")
    password = data.get("password")

    # Validar username
    if "username" not in data:
        details["username"] = "campo obligatorio"
    elif not isinstance(username, str):
        details["username"] = "debe ser string"
    elif User.objects.filter(username=username).exists():
        details["username"] = "ya está en uso"

    # Validar password
    if "password" not in data:
        details["password"] = "campo obligatorio"
    elif not isinstance(password, str):
        details["password"] = "debe ser string"
    elif len(password) < 8:
        details["password"] = "debe tener al menos 8 caracteres"

    if details:
        return validation_error(details)

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
