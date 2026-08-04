import logging
import math
import asyncio
import hashlib
import time
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/nearby", tags=["Nearby Facilities"])
logger = logging.getLogger("spectraguard.nearby")

# ---------------------------------------------------------------------------
# Overpass mirror pool — tried in order on timeout / 5xx
# ---------------------------------------------------------------------------
_OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

_DEFAULT_RADIUS_M = 5_000   # 5 km
_HTTP_TIMEOUT     = 45.0    # seconds per mirror attempt
_OVERPASS_TIMEOUT = 40      # declared inside the Overpass QL [timeout:…]
_RETRY_DELAY_S    = 1.0     # pause between mirror retries (seconds)

# ---------------------------------------------------------------------------
# In-memory request cache
# ---------------------------------------------------------------------------
# Key → (timestamp, FacilitiesResponse)
_cache: dict[str, tuple[float, "FacilitiesResponse"]] = {}
_CACHE_TTL_S   = 300   # 5 minutes
_CACHE_MAX_ENTRIES = 256

# Coordinate rounding for cache key (≈ 111 m precision at equator)
_COORD_PRECISION = 3   # decimal places


def _cache_key(lat: float, lon: float, radius: int, facility_type: Optional[str]) -> str:
    rounded = f"{round(lat, _COORD_PRECISION)},{round(lon, _COORD_PRECISION)},{radius},{facility_type or ''}"
    return hashlib.md5(rounded.encode()).hexdigest()


def _get_cached(key: str) -> Optional["FacilitiesResponse"]:
    entry = _cache.get(key)
    if entry is None:
        return None
    ts, value = entry
    if time.monotonic() - ts > _CACHE_TTL_S:
        _cache.pop(key, None)
        return None
    return value


def _set_cache(key: str, value: "FacilitiesResponse") -> None:
    # Evict oldest entries if the cache is full
    if len(_cache) >= _CACHE_MAX_ENTRIES:
        oldest_key = min(_cache, key=lambda k: _cache[k][0])
        _cache.pop(oldest_key, None)
    _cache[key] = (time.monotonic(), value)


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------
class FacilityResponse(BaseModel):
    id: int
    name: str
    type: str          # "pharmacy" | "laboratory" | "hospital" | "regulator"
    lat: float
    lon: float
    distance: float    # km
    address: Optional[str] = None
    phone: Optional[str] = None
    opening_hours: Optional[str] = None
    is_open: Optional[bool] = None
    website: Optional[str] = None


class FacilitiesResponse(BaseModel):
    facilities: list[FacilityResponse]
    total: int
    cached: bool = False


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.get("", response_model=FacilitiesResponse)
async def get_nearby_facilities(
    lat: float = Query(..., ge=-90, le=90, description="User latitude"),
    lon: float = Query(..., ge=-180, le=180, description="User longitude"),
    radius: int = Query(
        default=_DEFAULT_RADIUS_M,
        ge=500,
        le=50_000,
        description="Search radius in metres (default 5 000)",
    ),
    facility_type: Optional[str] = Query(
        default=None,
        alias="type",
        description="Filter: pharmacy | laboratory | hospital | regulator",
    ),
):
    """
    Proxy for OpenStreetMap / Overpass API.

    - Queries only the requested facility type (or all four if omitted).
    - Retries across multiple Overpass mirrors on 5xx / timeout.
    - Caches successful responses for 5 minutes (keyed on rounded location).
    - Returns structured facility objects with user-friendly error messages.
    """
    # Normalise the type filter value
    ftype = (facility_type or "").lower().strip() or None

    # ── Cache lookup ────────────────────────────────────────────────────────
    key = _cache_key(lat, lon, radius, ftype)
    cached = _get_cached(key)
    if cached is not None:
        logger.info(
            "Cache hit for lat=%.4f lon=%.4f radius=%d type=%s",
            lat, lon, radius, ftype,
        )
        # Return a copy with cached=True so clients can tell
        return FacilitiesResponse(
            facilities=cached.facilities,
            total=cached.total,
            cached=True,
        )

    # ── Query Overpass (with mirror retry) ──────────────────────────────────
    query = _build_query(lat, lon, radius, ftype)

    last_error: Exception = RuntimeError("No mirrors available")
    for attempt, mirror_url in enumerate(_OVERPASS_MIRRORS):
        if attempt > 0:
            # Brief pause before trying the next mirror
            await asyncio.sleep(_RETRY_DELAY_S)

        try:
            logger.info(
                "Querying Overpass mirror %d/%d: %s (radius=%dm, type=%s)",
                attempt + 1, len(_OVERPASS_MIRRORS), mirror_url, radius, ftype,
            )
            data = await _post_overpass(mirror_url, query)
            elements: list = data.get("elements", [])
            facilities = _parse_elements(elements, lat, lon)
            facilities.sort(key=lambda f: f.distance)

            result = FacilitiesResponse(facilities=facilities, total=len(facilities))
            _set_cache(key, result)

            logger.info(
                "Got %d facilities from %s (cached)",
                len(facilities), mirror_url,
            )
            return result

        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.warning(
                "Mirror %s timed out or unreachable: %s", mirror_url, exc
            )
            last_error = exc
            continue

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500:
                logger.warning(
                    "Mirror %s returned %d — trying next mirror",
                    mirror_url, exc.response.status_code,
                )
                last_error = exc
                continue
            # 4xx from Overpass usually means a bad query — no point retrying
            logger.error(
                "Mirror %s returned %d: %s",
                mirror_url, exc.response.status_code, exc,
            )
            raise HTTPException(
                status_code=502,
                detail="Could not fetch facility data: upstream service error. Please try again.",
            )

        except Exception as exc:
            logger.error(
                "Unexpected error from mirror %s: %s", mirror_url, exc, exc_info=True,
            )
            last_error = exc
            continue

    # ── All mirrors exhausted ───────────────────────────────────────────────
    logger.error("All Overpass mirrors failed. Last error: %s", last_error)
    raise HTTPException(
        status_code=503,
        detail=(
            "The facility data service is temporarily unavailable. "
            "Please try again in a moment."
        ),
    )


# ---------------------------------------------------------------------------
# Overpass HTTP helper
# ---------------------------------------------------------------------------
async def _post_overpass(url: str, query: str) -> dict:
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
        resp = await client.post(
            url,
            data={"data": query},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Query builder
# ---------------------------------------------------------------------------
def _build_query(lat: float, lon: float, radius: int, facility_type: Optional[str]) -> str:
    r = radius
    t = (facility_type or "").lower().strip()

    pharmacy_block = f'''
  node["amenity"="pharmacy"](around:{r},{lat},{lon});
  way["amenity"="pharmacy"](around:{r},{lat},{lon});''' if t in ("", "pharmacy") else ""

    hospital_block = f'''
  node["amenity"="hospital"](around:{r},{lat},{lon});
  way["amenity"="hospital"](around:{r},{lat},{lon});
  node["amenity"="clinic"](around:{r},{lat},{lon});
  way["amenity"="clinic"](around:{r},{lat},{lon});''' if t in ("", "hospital") else ""

    lab_block = f'''
  node["amenity"="laboratory"](around:{r},{lat},{lon});
  way["amenity"="laboratory"](around:{r},{lat},{lon});
  node["healthcare"="laboratory"](around:{r},{lat},{lon});
  way["healthcare"="laboratory"](around:{r},{lat},{lon});
  node["office"="pharmaceutical"](around:{r},{lat},{lon});
  way["office"="pharmaceutical"](around:{r},{lat},{lon});''' if t in ("", "laboratory") else ""

    regulator_block = f'''
  node["office"="government"]["name"~"drug|pharma|medicine|health|regulation|regulatory|authority|control",i](around:{r},{lat},{lon});
  way["office"="government"]["name"~"drug|pharma|medicine|health|regulation|regulatory|authority|control",i](around:{r},{lat},{lon});''' if t in ("", "regulator") else ""

    union_body = pharmacy_block + hospital_block + lab_block + regulator_block

    return f"""[out:json][timeout:{_OVERPASS_TIMEOUT}];
(
{union_body}
);
out body center;
"""


# ---------------------------------------------------------------------------
# Element parser
# ---------------------------------------------------------------------------
def _parse_elements(elements: list, user_lat: float, user_lon: float) -> list[FacilityResponse]:
    results: list[FacilityResponse] = []
    for el in elements:
        facility = _parse_element(el, user_lat, user_lon)
        if facility is not None:
            results.append(facility)
    return results


def _parse_element(el: dict, user_lat: float, user_lon: float) -> Optional[FacilityResponse]:
    try:
        tags: dict = el.get("tags", {})
        name: str = tags.get("name", "").strip()
        if not name:
            return None

        # Coordinates: node has lat/lon directly; way has a "center" object
        if el.get("type") == "node":
            e_lat = el.get("lat")
            e_lon = el.get("lon")
        else:
            center = el.get("center", {})
            e_lat = center.get("lat")
            e_lon = center.get("lon")

        if e_lat is None or e_lon is None:
            return None

        ftype = _detect_type(tags)
        if ftype is None:
            return None

        distance = _haversine_km(user_lat, user_lon, float(e_lat), float(e_lon))
        address = _build_address(tags)
        phone = _extract_phone(tags)
        opening_hours = tags.get("opening_hours", "").strip() or None
        is_open = _parse_open_status(tags)
        website = tags.get("website") or tags.get("contact:website") or None

        return FacilityResponse(
            id=int(el.get("id", 0)),
            name=name,
            type=ftype,
            lat=float(e_lat),
            lon=float(e_lon),
            distance=round(distance, 3),
            address=address or None,
            phone=phone,
            opening_hours=opening_hours,
            is_open=is_open,
            website=website,
        )
    except Exception:
        return None


def _detect_type(tags: dict) -> Optional[str]:
    amenity    = tags.get("amenity", "")
    healthcare = tags.get("healthcare", "")
    office     = tags.get("office", "")
    name       = tags.get("name", "").lower()

    if amenity == "pharmacy":
        return "pharmacy"
    if amenity in ("hospital", "clinic"):
        return "hospital"
    if amenity == "laboratory" or healthcare == "laboratory":
        return "laboratory"
    if office == "pharmaceutical":
        return "laboratory"
    if office == "government":
        keywords = ["drug", "pharma", "medicine", "health", "regulation",
                    "regulatory", "authority", "control"]
        if any(k in name for k in keywords):
            return "regulator"
    return None


def _build_address(tags: dict) -> str:
    house  = tags.get("addr:housenumber", "")
    street = tags.get("addr:street", "")
    suburb = tags.get("addr:suburb", "")
    city   = tags.get("addr:city", "")

    parts: list[str] = []
    if street and house:
        parts.append(f"{house} {street}")
    elif street:
        parts.append(street)
    if suburb:
        parts.append(suburb)
    if city:
        parts.append(city)
    return ", ".join(parts)


def _extract_phone(tags: dict) -> Optional[str]:
    for key in ("contact:phone", "phone", "contact:mobile", "mobile"):
        v = tags.get(key, "").strip()
        if v:
            return v
    return None


def _parse_open_status(tags: dict) -> Optional[bool]:
    import re
    from datetime import datetime

    raw = tags.get("opening_hours", "").lower().strip()
    if not raw:
        return None
    if raw == "24/7":
        return True

    now = datetime.now()
    day_abbrs = {1: "mo", 2: "tu", 3: "we", 4: "th", 5: "fr", 6: "sa", 7: "su"}
    day_abbr = day_abbrs[now.isoweekday()]

    if "mo-su" in raw or "24/7" in raw:
        return True
    if day_abbr not in raw:
        return False

    m = re.search(r"(\d{2}):(\d{2})-(\d{2}):(\d{2})", raw)
    if not m:
        return None
    open_h, open_min, close_h, close_min = (int(x) for x in m.groups())
    current = now.hour * 60 + now.minute
    return open_h * 60 + open_min <= current < close_h * 60 + close_min


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(d_lon / 2) ** 2)
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
