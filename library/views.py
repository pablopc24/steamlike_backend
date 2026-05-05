import json
import requests

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
        entries = Entry.objects.filter(owner=user)
        data = [
            {
                "id": entry.id,
                "external_id": entry.external_id,
                "hours_played": entry.hours_played,
                "notes": entry.notes,
            }
            for entry in entries
        ]
        return Response(data, status=200)

    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8"))
        except:
            return Response(
                {"error": "validation_error", "message": "JSON inválido"},
                status=400
            )

        external_id = body.get("external_id")
        hours_played = body.get("hours_played")
        notes = body.get("notes")

        if not external_id:
            return Response(
                {"error": "validation_error", "message": "external_id es obligatorio"},
                status=400
            )

        # ============================
        #   EJERCICIO 4 — CASO C
        # ============================
        try:
            response = requests.get(
                "https://www.cheapshark.com/api/1.0/games",
                params={"id": external_id},
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

        try:
            data = response.json()
        except ValueError:
            return Response(
                {
                    "error": "external_service_error",
                    "message": "Error al consultar el catálogo externo."
                },
                status=502
            )

        if isinstance(data, list):
            info = data[0] if len(data) else None
        else:
            info = data.get("info")

        if not info:
            return Response(
                {
                    "error": "invalid_external_game_id",
                    "message": "El juego indicado no existe en el catálogo externo.",
                    "details": {"external_id": "not_found"}
                },
                status=400
            )

        title = info.get("title", "")
        content = info.get("shortDescription", "")

        # Crear entrada
        entry = Entry.objects.create(
            owner=user,
            external_id=external_id,
            title=title,
            content=content,
            hours_played=hours_played or 0,
            notes=notes or ""
        )

        return Response(
            {
                "id": entry.id,
                "external_id": entry.external_id,
                "hours_played": entry.hours_played,
                "notes": entry.notes,
            },
            status=201
        )

@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def entry_detail(request, entry_id):
    user = request.user

    try:
        entry = Entry.objects.get(id=entry_id, owner=user)
    except Entry.DoesNotExist:
        return Response({"error": "not_found"}, status=404)

    if request.method == "GET":
        return Response(
            {
                "id": entry.id,
                "external_id": entry.external_id,
                "hours_played": entry.hours_played,
                "notes": entry.notes,
            }
        )

    if request.method == "PUT":
        data = request.data
        entry.hours_played = data.get("hours_played", entry.hours_played)
        entry.notes = data.get("notes", entry.notes)
        entry.save()
        return Response({"status": "updated"})

    if request.method == "DELETE":
        entry.delete()
        return Response(status=204)