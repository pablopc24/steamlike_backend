import hashlib
import requests
from django.core.cache import cache

CHEAPSHARK_URL = "https://www.cheapshark.com/api/1.0/games"
CACHE_TTL_SECONDS = 300


class CatalogServiceError(Exception):
    pass


class CatalogServiceUnavailable(CatalogServiceError):
    pass


class CatalogServiceExternalError(CatalogServiceError):
    pass


def _catalog_search_cache_key(query: str) -> str:
    normalized = query.strip()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"catalog_search:{digest}"


def _fetch_catalog_data(params: dict) -> list[dict] | dict:
    try:
        response = requests.get(CHEAPSHARK_URL, params=params, timeout=5)
    except requests.exceptions.RequestException as exc:
        raise CatalogServiceUnavailable from exc

    if response.status_code != 200:
        raise CatalogServiceExternalError

    try:
        return response.json()
    except ValueError as exc:
        raise CatalogServiceExternalError from exc


def search_catalog(query: str) -> list[dict]:
    cache_key = _catalog_search_cache_key(query)
    cached_results = cache.get(cache_key)
    if cached_results is not None:
        return cached_results

    try:
        data = _fetch_catalog_data({"title": query})
    except (CatalogServiceUnavailable, CatalogServiceExternalError):
        if cached_results is not None:
            return cached_results
        raise

    results = [
        {
            "external_game_id": item.get("gameID"),
            "title": item.get("external"),
            "thumb": item.get("thumb"),
        }
        for item in data
    ]

    cache.set(cache_key, results, timeout=CACHE_TTL_SECONDS)
    return results


def resolve_catalog(external_ids: list[str]) -> list[dict]:
    results = []
    for game_id in external_ids:
        data = _fetch_catalog_data({"id": game_id})
        info = data.get("info")
        if not info:
            continue

        results.append({
            "external_game_id": game_id,
            "title": info.get("title"),
            "thumb": info.get("thumb"),
        })

    return results
