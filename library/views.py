from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from .models import LibraryEntry

ALLOWED_STATUSES = ["wishlist", "playing", "completed", "dropped"]


def validation_error(details):
    return JsonResponse(
        {
            "error": "validation_error",
            "message": "Datos de entrada inválidos",
            "details": details,
        },
        status=400,
    )


def duplicate_error():
    return JsonResponse(
        {
            "error": "duplicate_entry",
            "message": "El juego ya existe en la biblioteca",
            "details": {"external_game_id": "duplicate"},
        },
        status=400,
    )


def not_found_error():
    return JsonResponse(
        {
            "error": "not_found",
            "message": "La entrada solicitada no existe",
        },
        status=404,
    )


def entry_to_dict(entry):
    return {
        "id": entry.id,
        "external_game_id": entry.external_game_id,
        "status": entry.status,
        "hours_played": entry.hours_played,
    }



@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@csrf_exempt
@require_POST
def create_library_entry(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return validation_error({"body": "JSON mal formado"})

    if not data:
        return validation_error({"body": "El JSON no puede estar vacío"})

    details = {}

    external_game_id = data.get("external_game_id")
    status_raw = data.get("status")
    hours_played = data.get("hours_played")

    if "external_game_id" not in data:
        details["external_game_id"] = "campo obligatorio"
    elif not isinstance(external_game_id, str):
        details["external_game_id"] = "debe ser string"

    if "status" not in data:
        details["status"] = "campo obligatorio"
    elif not isinstance(status_raw, str):
        details["status"] = "debe ser string"
    elif status_raw not in ALLOWED_STATUSES:
        details["status"] = "valor no permitido"

    if "hours_played" not in data:
        details["hours_played"] = "campo obligatorio"
    elif not isinstance(hours_played, int) or isinstance(hours_played, bool):
        details["hours_played"] = "debe ser integer"
    elif hours_played < 0:
        details["hours_played"] = "debe ser mayor o igual que 0"

    if details:
        return validation_error(details)

    if LibraryEntry.objects.filter(external_game_id=external_game_id).exists():
        return duplicate_error()

    entry = LibraryEntry.objects.create(
        external_game_id=external_game_id,
        status=status_raw,
        hours_played=hours_played,
    )

    return JsonResponse(entry_to_dict(entry), status=201)


@require_GET
def list_library_entries(request):
    entries = LibraryEntry.objects.all().order_by("id")
    data = [entry_to_dict(entry) for entry in entries]
    return JsonResponse(data, safe=False, status=200)


@require_GET
def library_entry_detail(request, entry_id):
    try:
        entry = LibraryEntry.objects.get(pk=entry_id)
    except LibraryEntry.DoesNotExist:
        return not_found_error()

    return JsonResponse(entry_to_dict(entry), status=200)

@csrf_exempt
def update_library_entry(request, entry_id):
    if request.method != "PATCH":
        return JsonResponse({"error": "method_not_allowed"}, status=405)

   
    try:
        entry = LibraryEntry.objects.get(pk=entry_id)
    except LibraryEntry.DoesNotExist:
        return not_found_error()


    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return validation_error({"body": "JSON mal formado"})

    if not data:
        return validation_error({"body": "El JSON no puede estar vacío"})


    allowed = {"status", "hours_played"}
    unknown = set(data.keys()) - allowed
    if unknown:
        return validation_error({field: "campo no permitido" for field in unknown})


    details = {}

    if "status" in data:
        status_raw = data["status"]
        if not isinstance(status_raw, str):
            details["status"] = "debe ser string"
        elif status_raw not in ALLOWED_STATUSES:
            details["status"] = "valor no permitido"

    if "hours_played" in data:
        hours = data["hours_played"]
        if not isinstance(hours, int) or isinstance(hours, bool):
            details["hours_played"] = "debe ser integer"
        elif hours < 0:
            details["hours_played"] = "debe ser mayor o igual que 0"

    if details:
        return validation_error(details)


    if "status" in data:
        entry.status = data["status"]
    if "hours_played" in data:
        entry.hours_played = data["hours_played"]

    entry.save()


    return JsonResponse(entry_to_dict(entry), status=200)
