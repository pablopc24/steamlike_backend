import json
from django.http import JsonResponse

from library.catalog_service import (
    CatalogServiceExternalError,
    CatalogServiceUnavailable,
    resolve_catalog,
    search_catalog,
)


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

    try:
        results = search_catalog(q)
    except CatalogServiceUnavailable:
        return JsonResponse(
            {
                "error": "external_service_unavailable",
                "message": "El catálogo externo no está disponible. Inténtalo más tarde."
            },
            status=503
        )
    except CatalogServiceExternalError:
        return JsonResponse(
            {
                "error": "external_service_error",
                "message": "Error al consultar el catálogo externo."
            },
            status=502
        )

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

    try:
        results = resolve_catalog(external_ids)
    except CatalogServiceUnavailable:
        return JsonResponse(
            {
                "error": "external_service_unavailable",
                "message": "El catálogo externo no está disponible. Inténtalo más tarde."
            },
            status=503
        )
    except CatalogServiceExternalError:
        return JsonResponse(
            {
                "error": "external_service_error",
                "message": "Error al consultar el catálogo externo."
            },
            status=502
        )

    return JsonResponse(results, safe=False, status=200)
