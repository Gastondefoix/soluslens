"""
Geocoding utilities.
Nominatim with 1.1s rate limit + Haversine fallback.
Cache results in data/geocache.json.
"""

import json
import time
import requests
from pathlib import Path

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_HEADERS = {"User-Agent": "soluslens/1.0"}
ROME_CENTER = (41.9028, 12.4964)
GEOCACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "geocache.json"


def load_cache() -> dict:
    if GEOCACHE_PATH.exists():
        with open(GEOCACHE_PATH) as f:
            return json.load(f)
    return {}


def save_cache(cache: dict) -> None:
    GEOCACHE_PATH.parent.mkdir(exist_ok=True)
    with open(GEOCACHE_PATH, "w") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def geocode(address: str, city: str = "Roma", cache: dict | None = None) -> tuple[float, float]:
    """
    Returns (lat, lon) for address.
    Checks cache first. Falls back to ROME_CENTER if Nominatim fails.
    Updates cache in-place if provided.
    """
    key = f"{address}, {city}, Italia"
    if cache is not None and key in cache:
        return tuple(cache[key])

    try:
        r = requests.get(
            NOMINATIM_URL,
            params={"q": key, "format": "json", "limit": 1},
            headers=NOMINATIM_HEADERS,
            timeout=10,
        )
        results = r.json()
        if results:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            if cache is not None:
                cache[key] = [lat, lon]
            time.sleep(1.1)
            return lat, lon
    except Exception as e:
        print(f"  [GEOCODE FAIL] {key}: {e}")

    time.sleep(1.1)
    if cache is not None:
        cache[key] = list(ROME_CENTER)
    return ROME_CENTER
