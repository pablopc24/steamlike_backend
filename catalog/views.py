import requests
import json
from django.http import JsonResponse


def health(request):
    return JsonResponse({"status": "ok"})


# ============================
#   EJERCICIO 2 — SEARCH
# ============================
def catalog_search(request):
    q = request.GET.get("q")

    # Validación interna
    if q is None or q.strip() == "":
        return JsonResponse(
            {
                "error": "validation_error",
                "message": "El parámetro 'q' es obligatorio y no puede estar vacío"
            },
            status=400
        )

    url = "https://www.cheapshark.com/api/1.0/games"

    # Caso A — Timeout / red
    try:
        response = requests.get(url, params={"title": q}, timeout=5)
    except requests.exceptions.RequestException:
        return JsonResponse(
            {
                "error": "external_service_unavailable",
                "message": "El catálogo externo no está disponible. Inténtalo más tarde."
            },
            status=503
        )

    # Caso B — CheapShark responde con error
    if response.status_code != 200:
        return JsonResponse(
            {
                "error": "external_service_error",
                "message": "Error al consultar el catálogo externo."
            },
            status=502
        )

    # Caso B — JSON inválido
    try:
        data = response.json()
    except:
        return JsonResponse(
            {
                "error": "external_service_error",
                "message": "Error al consultar el catálogo externo."
            },
            status=502
        )

    # Transformación
    results = [
        {
            "external_game_id": item.get("gameID"),
            "title": item.get("external"),
            "thumb": item.get("thumb")
        }
        for item in data
    ]

    return JsonResponse(results, safe=False, status=200)



# ============================
#   EJERCICIO 3 — RESOLVE
# ============================
def catalog_resolve(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "validation_error", "message": "Método no permitido"},
            status=400
        )

    # Parseo JSON
    try:
        body = json.loads(request.body)
    except:
        return JsonResponse(
            {"error": "validation_error", "message": "JSON inválido"},
            status=400
        )

    external_ids = body.get("external_game_ids")

    # Validación interna
    if not isinstance(external_ids, list) or len(external_ids) == 0:
        return JsonResponse(
            {
                "error": "validation_error",
                "message": "external_game_ids debe ser una lista no vacía"
            },
            status=400
        )

    results = []

    for game_id in external_ids:
        url = "https://www.cheapshark.com/api/1.0/games"

        # Caso A — Timeout / red
        try:
            response = requests.get(url, params={"id": game_id}, timeout=5)
        except requests.exceptions.RequestException:
            return JsonResponse(
                {
                    "error": "external_service_unavailable",
                    "message": "El catálogo externo no está disponible. Inténtalo más tarde."
                },
                status=503
            )

        # Caso B — CheapShark responde con error
        if response.status_code != 200:
            return JsonResponse(
                {
                    "error": "external_service_error",
                    "message": "Error al consultar el catálogo externo."
                },
                status=502
            )

        # Caso B — JSON inválido
        try:
            data = response.json()
        except:
            return JsonResponse(
                {
                    "error": "external_service_error",
                    "message": "Error al consultar el catálogo externo."
                },
                status=502
            )

        info = data.get("info")

        # Si no existe el juego → simplemente no se añade (Ejercicio 3 NO usa Caso C)
        if not info:
            continue

        results.append({
            "external_game_id": game_id,
            "title": info.get("title"),
            "thumb": info.get("thumb")
        })

    return JsonResponse(results, safe=False, status=200)
