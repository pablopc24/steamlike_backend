import hashlib
import logging
import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

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
    logger.debug(f"Searching catalog for query: {query!r}, cache_key: {cache_key}")
    
    cached_results = cache.get(cache_key)
    if cached_results is not None:
        logger.info(f"Cache hit for query: {query!r}. Returned {len(cached_results)} results from Redis.")
        return cached_results
    
    logger.debug(f"Cache miss for query: {query!r}. Fetching from CheapShark...")

    try:
        data = _fetch_catalog_data({"title": query})
    except (CatalogServiceUnavailable, CatalogServiceExternalError) as exc:
        logger.debug(f"Provider request failed: {type(exc).__name__}. Checking for fallback cache...")
        cached_results = cache.get(cache_key)
        if cached_results is not None:
            logger.info(f"Provider failed for query: {query!r}, but falling back to stale cache with {len(cached_results)} results.")
            return cached_results
        logger.error(f"Provider failed for query: {query!r} and no cache available. Raising error.")
        raise

    results = [
        {
            "external_game_id": item.get("gameID"),
            "title": item.get("external"),
            "thumb": item.get("thumb"),
        }
        for item in data
    ]

    logger.info(f"Provider returned {len(results)} results for query: {query!r}. Caching with TTL={CACHE_TTL_SECONDS}s.")
    cache.set(cache_key, results, timeout=CACHE_TTL_SECONDS)
    return results


def resolve_catalog(external_ids: list[str]) -> list[dict]:
    logger.debug(f"Resolving catalog for {len(external_ids)} game IDs.")
    results = []
    for game_id in external_ids:
        logger.debug(f"Fetching details for game_id: {game_id}")
        try:
            data = _fetch_catalog_data({"id": game_id})
        except (CatalogServiceUnavailable, CatalogServiceExternalError) as exc:
            logger.error(f"Provider failed for game_id: {game_id}. Exception: {type(exc).__name__}")
            raise
        
        if isinstance(data, list):
            if not data:
                logger.warning(f"No info found for game_id: {game_id}. Skipping.")
                continue
            info = data[0]
        elif isinstance(data, dict):
            info = data.get("info") or data
        else:
            logger.warning(f"Unexpected response format for game_id: {game_id}. Skipping.")
            continue

        if not info:
            logger.warning(f"No info found for game_id: {game_id}. Skipping.")
            continue

        result = {
            "external_game_id": game_id,
            "title": info.get("title"),
            "thumb": info.get("thumb"),
        }
        results.append(result)
        logger.debug(f"Resolved game_id: {game_id} -> title: {info.get('title')!r}")

    logger.info(f"Resolved {len(results)}/{len(external_ids)} game IDs successfully.")
    return results
