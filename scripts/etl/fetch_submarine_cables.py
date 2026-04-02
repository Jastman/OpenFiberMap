#!/usr/bin/env python3
"""
fetch_submarine_cables.py — Download submarine cable landing stations from
the TeleGeography Submarine Cable Map API (CC-BY-SA-4.0).

We only extract landing station POINTS (fiber-nodes layer) — not the submarine
cable routes themselves (those are undersea, not terrestrial fiber).
Landing stations are the critical endpoints where submarine cables connect to
terrestrial fiber backhaul.

API: https://www.submarinecablemap.com/api/v3/
  GET /cable/all.json      → list of cables with landing points
  GET /landing-point/all.json → all landing points

License: CC-BY-SA-4.0
Attribution: TeleGeography, www.submarinecablemap.com (CC-BY-SA)

Outputs:
  public/data/nodes-landing-stations.geojson

Usage:
  python scripts/etl/fetch_submarine_cables.py
  python scripts/etl/fetch_submarine_cables.py --refresh
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.etl.utils import (
    PUBLIC_DATA,
    get_json, save_geojson, feature_collection, node_feature,
    slugify, make_node_id, region_from_iso,
    is_cached, read_cache, write_cache,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

API_BASE    = "https://www.submarinecablemap.com/api/v3"
SOURCE      = "Submarine Cable Map"
LICENSE     = "CC-BY-SA-4.0"
ATTRIBUTION = "TeleGeography Submarine Cable Map (CC-BY-SA) — https://www.submarinecablemap.com"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_all_landing_points(refresh: bool) -> list[dict]:
    cache_name = "submarinecable_landing_points.json"
    if not refresh and is_cached(cache_name, max_age_hours=48):
        return json.loads(read_cache(cache_name))

    url = f"{API_BASE}/landing-point/all.json"
    print(f"  Fetching {url} ...")
    data = get_json(url)
    landing_points = data if isinstance(data, list) else data.get("landing_points", [])
    write_cache(cache_name, json.dumps(landing_points).encode())
    return landing_points


def _fetch_all_cables(refresh: bool) -> list[dict]:
    """Fetch all cable metadata (used to build cable-name lookup per landing point)."""
    cache_name = "submarinecable_cables.json"
    if not refresh and is_cached(cache_name, max_age_hours=48):
        return json.loads(read_cache(cache_name))

    url = f"{API_BASE}/cable/all.json"
    print(f"  Fetching {url} ...")
    data = get_json(url)
    cables = data if isinstance(data, list) else data.get("cables", [])
    write_cache(cache_name, json.dumps(cables).encode())
    return cables


def _build_landing_point_cable_map(cables: list[dict]) -> dict[str, list[str]]:
    """
    Return a dict mapping landing_point_id → [cable_name, ...] so we can
    annotate each landing station with which cables arrive there.
    """
    lp_cables: dict[str, list[str]] = {}
    for cable in cables:
        cable_name = cable.get("name") or cable.get("cable_name") or ""
        for lp in cable.get("landing_points") or []:
            lp_id = str(lp.get("id") or lp.get("landing_point_id") or "")
            if lp_id:
                lp_cables.setdefault(lp_id, []).append(cable_name)
    return lp_cables


def _parse_country(lp: dict) -> Optional[str]:
    """Extract ISO alpha-2 country code from a landing point record."""
    # API returns country in several possible fields
    return (
        lp.get("country_code")
        or lp.get("iso3166_1_alpha_2")
        or (lp.get("country") or {}).get("code")
        or None
    )


# ---------------------------------------------------------------------------
# Converter
# ---------------------------------------------------------------------------

def _lp_to_feature(lp: dict, cable_names: list[str], seq_map: dict) -> Optional[dict]:
    lat = lp.get("latitude") or lp.get("lat")
    lon = lp.get("longitude") or lp.get("lon") or lp.get("lng")

    if lat is None or lon is None:
        return None
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return None

    lp_id = str(lp.get("id") or lp.get("landing_point_id") or "")
    name  = lp.get("name") or lp.get("landing_point_name") or f"Landing Point {lp_id}"
    city  = lp.get("city") or lp.get("location") or None

    country_iso = _parse_country(lp)
    if not country_iso:
        # Try to extract from name field "City, CC" pattern
        if "," in name:
            parts = [p.strip() for p in name.split(",")]
            if len(parts[-1]) == 2:
                country_iso = parts[-1].upper()

    region = region_from_iso(country_iso or "")

    slug = slugify(name[:40])
    seq  = seq_map.get(slug, 1)
    seq_map[slug] = seq + 1
    node_id = make_node_id("landing-station", country_iso or "xx", slug, seq)

    notes_parts = []
    if cable_names:
        notes_parts.append(f"Cables: {', '.join(cable_names[:10])}")
        if len(cable_names) > 10:
            notes_parts.append(f"(+{len(cable_names)-10} more)")
    notes = "; ".join(notes_parts) if notes_parts else None

    return node_feature(
        node_id=node_id,
        network_id=f"global-landing-{lp_id}",
        name=name,
        name_short=city,
        operator="(Various)",
        node_type="landing-station",
        lon=lon,
        lat=lat,
        status="operational",
        city=city,
        country_iso=country_iso,
        region=region,
        source=SOURCE,
        source_url=f"https://www.submarinecablemap.com/#/landing-point/{lp_id}",
        license=LICENSE,
        attribution=ATTRIBUTION,
        notes=notes,
        extra={"cable_count": len(cable_names), "cables": cable_names[:20]},
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def fetch(refresh: bool = False) -> dict:
    print("\n=== Submarine Cable Map fetcher (landing stations) ===")

    cables = _fetch_all_cables(refresh)
    landing_points = _fetch_all_landing_points(refresh)
    print(f"  {len(cables)} cables, {len(landing_points)} landing points fetched")

    lp_cable_map = _build_landing_point_cable_map(cables)

    features: list[dict] = []
    skipped = 0
    seq_map: dict[str, int] = {}

    for lp in landing_points:
        lp_id = str(lp.get("id") or lp.get("landing_point_id") or "")
        cable_names = lp_cable_map.get(lp_id, [])
        feat = _lp_to_feature(lp, cable_names, seq_map)
        if feat:
            features.append(feat)
        else:
            skipped += 1

    print(f"  Converted: {len(features)} landing stations, {skipped} skipped (no coords)")

    fc = feature_collection(
        features,
        name="OpenFiberMap-Nodes-LandingStations",
        description="Submarine cable landing stations (terrestrial fiber endpoints) — TeleGeography",
        license=LICENSE,
        attribution=ATTRIBUTION,
        source=SOURCE,
    )

    out_path = PUBLIC_DATA / "nodes-landing-stations.geojson"
    save_geojson(fc, out_path)
    return fc


def main():
    parser = argparse.ArgumentParser(description="Fetch submarine cable landing stations")
    parser.add_argument("--refresh", action="store_true", help="Force re-download ignoring cache")
    args = parser.parse_args()
    fetch(refresh=args.refresh)


if __name__ == "__main__":
    main()
