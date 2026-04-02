#!/usr/bin/env python3
"""
fetch_peeringdb.py — Download IXP and data-center nodes from PeeringDB.

PeeringDB API is CC0 (public domain). No authentication required for read-only
access, though an API key raises rate limits from 100 to 1000 req/min.

Outputs:
  data/raw/peeringdb_ix.json      — Internet exchanges
  data/raw/peeringdb_fac.json     — Facilities (data centers / carrier hotels)
  public/data/nodes-peeringdb.geojson

Usage:
  python scripts/etl/fetch_peeringdb.py
  python scripts/etl/fetch_peeringdb.py --api-key YOUR_KEY --refresh
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

# Allow running the script directly from any directory
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.etl.utils import (
    RAW_CACHE, PUBLIC_DATA,
    get_json, save_geojson, feature_collection, node_feature,
    slugify, make_node_id, region_from_iso,
    cache_path, is_cached, read_cache, write_cache,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PEERINGDB_BASE = "https://www.peeringdb.com/api"
SOURCE = "PeeringDB"
LICENSE = "CC0-1.0"
ATTRIBUTION = "PeeringDB (CC0) — https://www.peeringdb.com"
SOURCE_URL_IX  = "https://www.peeringdb.com/ix/{id}"
SOURCE_URL_FAC = "https://www.peeringdb.com/fac/{id}"

# IXP status mapping from PeeringDB → OFM
IX_STATUS_MAP = {
    "ok": "operational",
    "pending": "planned",
    "deleted": "decommissioned",
    "inactive": "decommissioned",
}

FAC_STATUS_MAP = {
    "ok": "operational",
    "pending": "planned",
    "deleted": "decommissioned",
    "inactive": "decommissioned",
}


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

def _fetch_paged(endpoint: str, api_key: Optional[str], cache_name: str, refresh: bool) -> list[dict]:
    """Fetch all pages of a PeeringDB endpoint, with local cache."""
    if not refresh and is_cached(cache_name, max_age_hours=48):
        print(f"  Using cache: {cache_name}")
        return json.loads(read_cache(cache_name))

    headers = {}
    if api_key:
        headers["Authorization"] = f"Api-Key {api_key}"

    url = f"{PEERINGDB_BASE}/{endpoint}"
    print(f"  Fetching {url} ...")

    # PeeringDB paginates with ?limit=&skip=
    all_data: list[dict] = []
    limit = 500
    skip = 0

    while True:
        params = {"limit": limit, "skip": skip, "depth": 0}
        resp = get_json(url, params=params)
        items = resp.get("data", [])
        all_data.extend(items)
        if len(items) < limit:
            break
        skip += limit
        time.sleep(0.2)   # gentle rate limiting

    print(f"  Fetched {len(all_data)} records from /{endpoint}")
    write_cache(cache_name, json.dumps(all_data).encode())
    return all_data


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------

def _ix_to_feature(ix: dict, seq_map: dict) -> Optional[dict]:
    """Convert a PeeringDB IX record to an OFM fiber-nodes Feature."""
    lat = ix.get("lat") or ix.get("latitude")
    lon = ix.get("lon") or ix.get("longitude")

    # PeeringDB IX records don't always have lat/lon at the top level;
    # they may be on the ixlan or fac sub-records. Skip if missing.
    if not lat or not lon:
        return None

    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return None

    ix_id = ix.get("id")
    country = (ix.get("country") or "").upper() or None
    city = ix.get("city") or None
    name = ix.get("name") or f"IXP {ix_id}"
    name_short = ix.get("name_long") or name

    slug = slugify(ix.get("name") or str(ix_id))
    seq = seq_map.get(slug, 1)
    seq_map[slug] = seq + 1
    node_id = make_node_id("ixp", country or "xx", slug, seq)

    region = region_from_iso(country or "")

    return node_feature(
        node_id=node_id,
        network_id=f"peeringdb-ix-{ix_id}",
        name=name,
        name_short=name_short if name_short != name else None,
        operator=ix.get("org", {}).get("name", "") if isinstance(ix.get("org"), dict) else name,
        node_type="ixp",
        lon=lon,
        lat=lat,
        status=IX_STATUS_MAP.get(ix.get("status", "ok"), "operational"),
        city=city,
        country_iso=country,
        region=region,
        address=None,
        peeringdb_ix_id=ix_id,
        website=ix.get("website") or None,
        source=SOURCE,
        source_url=SOURCE_URL_IX.format(id=ix_id),
        license=LICENSE,
        attribution=ATTRIBUTION,
        notes=ix.get("notes") or None,
    )


def _fac_to_feature(fac: dict, seq_map: dict) -> Optional[dict]:
    """Convert a PeeringDB facility record to an OFM fiber-nodes Feature."""
    lat = fac.get("latitude")
    lon = fac.get("longitude")

    if not lat or not lon:
        return None

    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return None

    fac_id = fac.get("id")
    country = (fac.get("country") or "").upper() or None
    city = fac.get("city") or None
    name = fac.get("name") or f"Facility {fac_id}"

    slug = slugify(fac.get("name") or str(fac_id))
    seq = seq_map.get(slug, 1)
    seq_map[slug] = seq + 1
    node_id = make_node_id("data-center", country or "xx", slug, seq)

    region = region_from_iso(country or "")

    # Classify facility type
    colo_type = (fac.get("colo") or "").lower()
    node_type = "telecom-hotel" if "hotel" in colo_type else "data-center"

    return node_feature(
        node_id=node_id,
        network_id=f"peeringdb-fac-{fac_id}",
        name=name,
        name_short=None,
        operator=fac.get("org", {}).get("name", "") if isinstance(fac.get("org"), dict) else name,
        node_type=node_type,
        lon=lon,
        lat=lat,
        status=FAC_STATUS_MAP.get(fac.get("status", "ok"), "operational"),
        city=city,
        country_iso=country,
        region=region,
        address=fac.get("address1") or None,
        floor_space_sqm=None,  # not in public API
        power_mw=None,
        peeringdb_id=fac_id,
        website=fac.get("website") or None,
        source=SOURCE,
        source_url=SOURCE_URL_FAC.format(id=fac_id),
        license=LICENSE,
        attribution=ATTRIBUTION,
        notes=fac.get("notes") or None,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def fetch(api_key: Optional[str] = None, refresh: bool = False) -> dict:
    print("\n=== PeeringDB fetcher ===")

    # Fetch IXPs
    ix_data = _fetch_paged("ix", api_key, "peeringdb_ix.json", refresh)

    # Fetch facilities
    fac_data = _fetch_paged("fac", api_key, "peeringdb_fac.json", refresh)

    features: list[dict] = []
    seq_map: dict[str, int] = {}

    # Convert IXPs
    ok_ix = skipped_ix = 0
    for ix in ix_data:
        if ix.get("status") == "deleted":
            skipped_ix += 1
            continue
        feat = _ix_to_feature(ix, seq_map)
        if feat:
            features.append(feat)
            ok_ix += 1
        else:
            skipped_ix += 1

    print(f"  IXPs: {ok_ix} converted, {skipped_ix} skipped (no coords or deleted)")

    # Convert facilities
    ok_fac = skipped_fac = 0
    for fac in fac_data:
        if fac.get("status") == "deleted":
            skipped_fac += 1
            continue
        feat = _fac_to_feature(fac, seq_map)
        if feat:
            features.append(feat)
            ok_fac += 1
        else:
            skipped_fac += 1

    print(f"  Facilities: {ok_fac} converted, {skipped_fac} skipped (no coords or deleted)")

    fc = feature_collection(
        features,
        name="OpenFiberMap-Nodes-PeeringDB",
        description="IXPs and data-center facilities from PeeringDB (CC0)",
        license=LICENSE,
        attribution=ATTRIBUTION,
        source="PeeringDB",
    )

    out_path = PUBLIC_DATA / "nodes-peeringdb.geojson"
    save_geojson(fc, out_path)
    return fc


def main():
    parser = argparse.ArgumentParser(description="Fetch PeeringDB nodes for OpenFiberMap")
    parser.add_argument("--api-key", help="PeeringDB API key (optional; raises rate limit)")
    parser.add_argument("--refresh", action="store_true", help="Force re-download ignoring cache")
    args = parser.parse_args()
    fetch(api_key=args.api_key, refresh=args.refresh)


if __name__ == "__main__":
    main()
