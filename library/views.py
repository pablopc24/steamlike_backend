import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Entry

CHEAPSHARK_SEARCH_URL = "https://www.cheapshark.com/api/1.0/games"


@api_view(["POST"])
def register(request):
    from django.contrib.auth.models import User

    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "invalid"}, status=400)

    user = User.objects.create_user(username=username, password=password)

    return Response({"id": user.id}, status=201)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def entries_list(request):
    user = request.user

    if request.method == "GET":
        entries = Entry.objects.filter(user=user)
        data = [
            {
                "id": entry.id,
                "external_game_id": entry.external_game_id,
                "hours_played": entry.hours_played,
                "notes": entry.notes,
            }
            for entry in entries
        ]
        return Response(data, status=200)

    if request.method == "POST":
        try:
            body = json.loads(request.body)
        except:
            return Response(
                {"error": "validation_error", "message": "JSON inválido"},
                status=400
            )

        external_game_id = body.get("external_game_id")
        hours_played = body.get("hours_played")
        notes = body.get("notes")

        if not external_game_id:
            return Response(
                {"error": "validation_error", "message": "external_game_id es obligatorio"},
                status=400
            )

        # ============================
        #   EJERCICIO 4 — CASO C
        # ============================
        try:
            response = requests.get(
                "https://www.cheapshark.com/api/1.0/games",
                params={"id": external_game_id},
                timeout=5
            )
        except requests.exceptions.RequestException:
            return Response(
                {
                    "error": "external_service_unavailable",
                    "message": "El catálogo externo no está disponible. Inténtalo más tarde."
                },
                status=503
            )

        if response.status_code != 200:
            return Response(
                {
                    "error": "external_service_error",
                    "message": "Error al consultar el catálogo externo."
                },
                status=502
            )

        data = response.json()
        info = data.get("info")

        if not info:
            return Response(
                {
                    "error": "invalid_external_game_id",
                    "message": "El juego indicado no existe en el catálogo externo.",
                    "details": { "external_game_id": "not_found" }
                },
                status=400
            )

        # Crear entrada
        entry = Entry.objects.create(
            user=user,
            external_game_id=external_game_id,
            hours_played=hours_played or 0,
            notes=notes or ""
        )

        return Response(
            {
                "id": entry.id,
                "external_game_id": entry.external_game_id,
                "hours_played": entry.hours_played,
                "notes": entry.notes,
            },
            status=201
        )
