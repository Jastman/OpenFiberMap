"""
utils.py — Shared utilities for all OpenFiberMap ETL fetchers.

Provides:
  - Capacity classification
  - Standardised feature builders (spans + nodes)
  - ID slug helpers
  - GeoJSON / file helpers
  - HTTP helpers with retry + rate-limit back-off
"""

from __future__ import annotations

import json
import math
import re
import time
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DATA = ROOT / "public" / "data"
RAW_CACHE = ROOT / "data" / "raw"

PUBLIC_DATA.mkdir(parents=True, exist_ok=True)
RAW_CACHE.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Capacity classification
# ---------------------------------------------------------------------------

CAPACITY_TIERS: list[tuple[float, str]] = [
    (1_000.0, "ultra-high"),  # ≥ 1 Tbps
    (100.0,   "high"),        # 100–999 Gbps
    (10.0,    "medium"),      # 10–99 Gbps
    (0.0,     "low"),         # < 10 Gbps
]


def classify_capacity(gbps: Optional[float]) -> str:
    """Return the capacity tier string for a given Gbps value."""
    if gbps is None:
        return "unknown"
    for threshold, label in CAPACITY_TIERS:
        if gbps >= threshold:
            return label
    return "unknown"


# ---------------------------------------------------------------------------
# ID / slug helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Convert a name to a lowercase ASCII slug, e.g. 'MainOne Ltd.' → 'mainone-ltd'."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text


def make_span_id(network_id: str, seq: int) -> str:
    return f"{network_id}--{seq:04d}"


def make_node_id(node_type: str, country_iso: str, slug: str, seq: int) -> str:
    type_prefix = {
        "ixp": "ixp",
        "data-center": "dc",
        "pop": "pop",
        "landing-station": "ls",
        "amplifier": "amp",
        "exchange": "exc",
        "telecom-hotel": "th",
        "government-node": "gov",
        "research-node": "rnd",
    }.get(node_type, "node")
    country = country_iso.lower() if country_iso else "xx"
    return f"{type_prefix}-{country}-{slug}-{seq:02d}"


# ---------------------------------------------------------------------------
# Feature builders
# ---------------------------------------------------------------------------

TODAY = date.today().isoformat()


def span_feature(
    *,
    span_id: str,
    network_id: str,
    name: Optional[str],
    operator: str,
    coordinates: list[list[float]],
    country_iso: Optional[str] = None,
    countries: Optional[list[str]] = None,
    region: Optional[str] = None,
    status: str = "unknown",
    burial_type: Optional[str] = None,
    length_km: Optional[float] = None,
    capacity_gbps: Optional[float] = None,
    fiber_pairs: Optional[int] = None,
    fiber_type: Optional[str] = None,
    phase_name: Optional[str] = None,
    construction_start: Optional[str] = None,
    ready_for_service: Optional[str] = None,
    funders: Optional[list[str]] = None,
    source: str = "",
    source_url: Optional[str] = None,
    license: Optional[str] = None,
    attribution: Optional[str] = None,
    notes: Optional[str] = None,
    ofds_span_id: Optional[str] = None,
    osm_way_id: Optional[str] = None,
    extra: Optional[dict] = None,
) -> dict:
    """Return a GeoJSON Feature for a fiber span."""
    # Auto-compute length if not provided (Haversine sum)
    if length_km is None and len(coordinates) >= 2:
        length_km = round(_haversine_path(coordinates), 1)

    # Derive geometry type
    geometry: dict[str, Any]
    if not coordinates:
        geometry = {"type": "LineString", "coordinates": []}
    elif isinstance(coordinates[0][0], list):
        # Already a list of rings / multilinestring
        geometry = {"type": "MultiLineString", "coordinates": coordinates}
    else:
        geometry = {"type": "LineString", "coordinates": coordinates}

    props: dict[str, Any] = {
        "ofm_layer": "fiber-spans",
        "span_id": span_id,
        "network_id": network_id,
        "name": name,
        "operator": operator,
        "operator_id": None,
        "country_iso": country_iso,
        "countries": countries or ([country_iso] if country_iso else []),
        "region": region,
        "status": status,
        "burial_type": burial_type,
        "length_km": length_km,
        "capacity_gbps": capacity_gbps,
        "capacity_class": classify_capacity(capacity_gbps),
        "fiber_pairs": fiber_pairs,
        "fiber_type": fiber_type,
        "phase_id": None,
        "phase_name": phase_name,
        "construction_start": construction_start,
        "ready_for_service": ready_for_service,
        "funders": funders or [],
        "contracts": [],
        "source": source,
        "source_url": source_url,
        "license": license,
        "attribution": attribution,
        "last_updated": TODAY,
        "notes": notes,
        "ofds_span_id": ofds_span_id,
        "osm_way_id": osm_way_id,
    }
    if extra:
        props.update(extra)

    return {"type": "Feature", "geometry": geometry, "properties": props}


def node_feature(
    *,
    node_id: str,
    network_id: str,
    name: str,
    name_short: Optional[str] = None,
    operator: str,
    node_type: str,
    lon: float,
    lat: float,
    status: str = "operational",
    city: Optional[str] = None,
    country_iso: Optional[str] = None,
    region: Optional[str] = None,
    address: Optional[str] = None,
    floor_space_sqm: Optional[float] = None,
    power_mw: Optional[float] = None,
    connected_networks: Optional[list[str]] = None,
    peeringdb_id: Optional[int] = None,
    peeringdb_ix_id: Optional[int] = None,
    website: Optional[str] = None,
    source: str = "",
    source_url: Optional[str] = None,
    license: Optional[str] = None,
    attribution: Optional[str] = None,
    notes: Optional[str] = None,
    osm_node_id: Optional[str] = None,
    extra: Optional[dict] = None,
) -> dict:
    """Return a GeoJSON Feature for a fiber node."""
    props: dict[str, Any] = {
        "ofm_layer": "fiber-nodes",
        "node_id": node_id,
        "network_id": network_id,
        "name": name,
        "name_short": name_short,
        "operator": operator,
        "node_type": node_type,
        "status": status,
        "city": city,
        "country_iso": country_iso,
        "region": region,
        "address": address,
        "floor_space_sqm": floor_space_sqm,
        "power_mw": power_mw,
        "connected_networks": connected_networks or [],
        "peeringdb_id": peeringdb_id,
        "peeringdb_ix_id": peeringdb_ix_id,
        "website": website,
        "source": source,
        "source_url": source_url,
        "license": license,
        "attribution": attribution,
        "last_updated": TODAY,
        "notes": notes,
        "osm_node_id": osm_node_id,
    }
    if extra:
        props.update(extra)

    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": props,
    }


# ---------------------------------------------------------------------------
# GeoJSON I/O
# ---------------------------------------------------------------------------

def feature_collection(features: list[dict], **meta) -> dict:
    fc: dict[str, Any] = {
        "type": "FeatureCollection",
        "last_updated": TODAY,
    }
    fc.update(meta)
    fc["features"] = features
    return fc


def save_geojson(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    kb = path.stat().st_size / 1024
    print(f"  Saved {len(data.get('features', []))} features → {path} ({kb:.0f} KB)")


def load_geojson(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _build_session(retries: int = 4, backoff: float = 1.0) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": "OpenFiberMap-ETL/0.1 (https://github.com/jastman/OpenFiberMap; open-source public good)"
    })
    return session


_SESSION = _build_session()


def get_json(url: str, params: Optional[dict] = None, timeout: int = 60) -> Any:
    """Fetch JSON from a URL with retries."""
    resp = _SESSION.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def get_raw(url: str, params: Optional[dict] = None, timeout: int = 120) -> bytes:
    """Fetch raw bytes from a URL with retries."""
    resp = _SESSION.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.content


def get_text(url: str, params: Optional[dict] = None, timeout: int = 120) -> str:
    resp = _SESSION.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.text


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Return great-circle distance in km between two WGS84 points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _haversine_path(coords: list[list[float]]) -> float:
    """Sum haversine distances along a list of [lon, lat] coordinates."""
    total = 0.0
    for i in range(len(coords) - 1):
        total += _haversine(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1])
    return total


def region_from_iso(country_iso: str) -> str:
    """Map ISO-3166-1 alpha-2 country code to OpenFiberMap region string."""
    AFRICA = {
        "DZ","AO","BJ","BW","BF","BI","CM","CV","CF","TD","KM","CG","CD","CI","DJ",
        "EG","GQ","ER","ET","GA","GM","GH","GN","GW","KE","LS","LR","LY","MG","MW",
        "ML","MR","MU","MA","MZ","NA","NE","NG","RW","ST","SN","SL","SO","ZA","SS",
        "SD","SZ","TZ","TG","TN","UG","ZM","ZW",
    }
    AMERICAS = {
        "AI","AG","AR","AW","BS","BB","BZ","BM","BO","BR","VG","CA","KY","CL","CO",
        "CR","CU","CW","DM","DO","EC","SV","FK","GF","GD","GP","GT","GY","HT","HN",
        "JM","MQ","MX","MS","NI","PA","PY","PE","PR","KN","LC","VC","SX","SR","TT",
        "TC","US","UY","VE","VI",
    }
    EUROPE = {
        "AL","AD","AT","BY","BE","BA","BG","HR","CY","CZ","DK","EE","FI","FR","DE",
        "GI","GR","HU","IS","IE","IT","XK","LV","LI","LT","LU","MT","MD","MC","ME",
        "NL","MK","NO","PL","PT","RO","RU","SM","RS","SK","SI","ES","SE","CH","UA",
        "GB","VA","TR",
    }
    ASIA_PACIFIC = {
        "AF","AM","AZ","BH","BD","BT","BN","KH","CN","GE","HK","IN","ID","IR","IQ",
        "IL","JP","JO","KZ","KW","KG","LA","LB","MO","MY","MV","MN","MM","NP","KP",
        "OM","PK","PS","PH","QA","SA","SG","KR","LK","SY","TW","TJ","TH","TL","TM",
        "UZ","VN","YE","AU","FJ","GU","KI","MH","FM","NR","NZ","PW","PG","WS","SB",
        "TO","TV","VU",
    }
    MIDDLE_EAST = {"AE", "BH", "IQ", "IL", "JO", "KW", "LB", "OM", "PS", "QA", "SA", "SY", "YE"}

    code = (country_iso or "").upper()
    if code in AFRICA:
        return "africa"
    if code in AMERICAS:
        return "americas"
    if code in EUROPE:
        return "europe"
    if code in MIDDLE_EAST:
        return "middle-east"
    if code in ASIA_PACIFIC:
        return "asia-pacific"
    return "global"


# ---------------------------------------------------------------------------
# Cache helpers (avoid re-downloading on repeated runs)
# ---------------------------------------------------------------------------

def cache_path(name: str) -> Path:
    return RAW_CACHE / name


def is_cached(name: str, max_age_hours: int = 24) -> bool:
    p = cache_path(name)
    if not p.exists():
        return False
    age_hours = (time.time() - p.stat().st_mtime) / 3600
    return age_hours < max_age_hours


def read_cache(name: str) -> bytes:
    return cache_path(name).read_bytes()


def write_cache(name: str, data: bytes) -> None:
    p = cache_path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
