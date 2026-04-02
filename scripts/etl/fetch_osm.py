#!/usr/bin/env python3
"""
fetch_osm.py — Fetch fiber optic infrastructure from OpenStreetMap via Overpass API.

OpenStreetMap data is licensed under ODbL 1.0.
© OpenStreetMap contributors.

This fetcher queries the Overpass API for:
  - Ways tagged telecom=cable (fiber optic ducts / routes)
  - Ways tagged man_made=pipeline + content=fiber
  - Nodes/ways tagged telecom=exchange or telecom=data_center

OSM fiber tagging is sparse and highly variable by region — best in urban
corridors and some African/Asian routes. Used as a gap-filler.

Queries are split by region bounding box to avoid Overpass timeouts.
Results are cached locally for 72 hours.

Outputs:
  public/data/spans-osm-africa.geojson
  public/data/spans-osm-americas.geojson
  public/data/spans-osm-europe.geojson
  public/data/nodes-osm-global.geojson

Usage:
  python scripts/etl/fetch_osm.py
  python scripts/etl/fetch_osm.py --regions africa europe
  python scripts/etl/fetch_osm.py --refresh
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.etl.utils import (
    PUBLIC_DATA,
    get_text, save_geojson, feature_collection,
    span_feature, node_feature, slugify, make_node_id, make_span_id,
    region_from_iso, is_cached, read_cache, write_cache,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
]

SOURCE      = "OpenStreetMap"
LICENSE     = "ODbL-1.0"
ATTRIBUTION = "© OpenStreetMap contributors (ODbL) — https://www.openstreetmap.org/copyright"

# Bounding boxes [south, west, north, east]
REGION_BBOXES: dict[str, tuple[float, float, float, float]] = {
    "africa":   (-35.0, -18.0,  38.0,  52.0),
    "americas": (-56.0, -82.0,  72.0, -34.0),
    "europe":   ( 34.0, -10.0,  72.0,  40.0),
    "asia":     (-10.0,  25.0,  55.0, 145.0),
}

# Overpass query template — parametrised by bbox
SPAN_QUERY_TEMPLATE = """
[out:json][timeout:120][bbox:{south},{west},{north},{east}];
(
  way["telecom"="cable"];
  way["telecom:medium"="fibre"];
  way["telecom:medium"="fiber"];
  way["cable:type"="fibre"];
  way["cable:type"="fiber"];
  way["man_made"="pipeline"]["content"="fibre"];
  way["man_made"="pipeline"]["content"="fiber"];
  relation["telecom"="cable"]["type"="route"];
);
out geom qt;
"""

NODE_QUERY_TEMPLATE = """
[out:json][timeout:60][bbox:{south},{west},{north},{east}];
(
  node["telecom"="exchange"];
  node["telecom"="data_center"];
  node["telecom"~"^(ixp|internet_exchange)$"];
  way["telecom"="exchange"]["building"];
  way["telecom"="data_center"]["building"];
);
out center qt;
"""


# ---------------------------------------------------------------------------
# Overpass query runner
# ---------------------------------------------------------------------------

def _run_overpass(query: str, cache_name: str, refresh: bool) -> Optional[dict]:
    if not refresh and is_cached(cache_name, max_age_hours=72):
        return json.loads(read_cache(cache_name))

    last_err = None
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            print(f"    Querying {endpoint} ...")
            resp_text = get_text(endpoint, params={"data": query}, timeout=150)
            data = json.loads(resp_text)
            write_cache(cache_name, resp_text.encode())
            return data
        except Exception as e:
            last_err = e
            print(f"    WARN: {endpoint} failed: {e}")
            time.sleep(2)

    print(f"    ERROR: All Overpass endpoints failed. Last: {last_err}")
    return None


# ---------------------------------------------------------------------------
# OSM element → OFM converters
# ---------------------------------------------------------------------------

def _osm_way_to_span(elem: dict, region: str, seq: int) -> Optional[dict]:
    """Convert an OSM way element (with geom) to an OFM fiber span."""
    geom = elem.get("geometry") or []
    if not geom:
        return None

    coords = [[pt["lon"], pt["lat"]] for pt in geom if "lon" in pt and "lat" in pt]
    if len(coords) < 2:
        return None

    tags = elem.get("tags") or {}
    osm_id = str(elem.get("id", ""))

    operator = (
        tags.get("operator")
        or tags.get("network")
        or tags.get("owner")
        or "Unknown"
    )
    name = tags.get("name") or tags.get("description") or None

    # Infer country from first coordinate if we had reverse-geocoding.
    # For now, use region as proxy.
    country_iso = None

    # Burial type
    location = (tags.get("location") or tags.get("tunnel") or "").lower()
    if location in ("underground", "buried"):
        burial = "underground"
    elif location in ("aerial", "overhead"):
        burial = "aerial"
    else:
        burial = "underground"  # default for telecom cables

    network_id = f"osm-{region}-{slugify(operator)}"

    return span_feature(
        span_id=make_span_id(network_id, seq),
        network_id=network_id,
        name=name,
        operator=operator,
        coordinates=coords,
        country_iso=country_iso,
        region=region,
        status="deployed",
        burial_type=burial,
        source=SOURCE,
        source_url=f"https://www.openstreetmap.org/way/{osm_id}",
        license=LICENSE,
        attribution=ATTRIBUTION,
        notes="OSM fiber tag; data quality highly variable.",
        osm_way_id=osm_id,
    )


def _osm_node_to_ofm(elem: dict, seq_map: dict) -> Optional[dict]:
    """Convert an OSM node/way-with-centre to an OFM fiber node."""
    # Ways come back with a 'center' field
    if elem.get("type") == "way":
        centre = elem.get("center") or {}
        lat = centre.get("lat")
        lon = centre.get("lon")
    else:
        lat = elem.get("lat")
        lon = elem.get("lon")

    if lat is None or lon is None:
        return None

    tags = elem.get("tags") or {}
    osm_id = str(elem.get("id", ""))

    telecom_tag = tags.get("telecom", "").lower()
    node_type_map = {
        "exchange": "exchange",
        "data_center": "data-center",
        "ixp": "ixp",
        "internet_exchange": "ixp",
    }
    node_type = node_type_map.get(telecom_tag, "exchange")

    name = tags.get("name") or tags.get("description") or f"OSM Telecom Node {osm_id}"
    operator = tags.get("operator") or tags.get("network") or "Unknown"
    country_iso = (tags.get("addr:country") or "").upper() or None
    region = "global"

    slug = slugify(name[:40])
    seq  = seq_map.get(slug, 1)
    seq_map[slug] = seq + 1
    node_id = make_node_id(node_type, country_iso or "xx", slug, seq)
    network_id = f"osm-{slugify(operator)}"

    return node_feature(
        node_id=node_id,
        network_id=network_id,
        name=name,
        operator=operator,
        node_type=node_type,
        lon=float(lon),
        lat=float(lat),
        country_iso=country_iso,
        region=region,
        source=SOURCE,
        source_url=f"https://www.openstreetmap.org/node/{osm_id}",
        license=LICENSE,
        attribution=ATTRIBUTION,
        osm_node_id=osm_id,
    )


# ---------------------------------------------------------------------------
# Per-region fetch
# ---------------------------------------------------------------------------

def _fetch_region_spans(region: str, bbox: tuple, refresh: bool) -> list[dict]:
    south, west, north, east = bbox
    query = SPAN_QUERY_TEMPLATE.format(south=south, west=west, north=north, east=east)
    cache_name = f"osm_spans_{region}.json"

    print(f"  Fetching OSM spans for {region} [{south},{west},{north},{east}] ...")
    data = _run_overpass(query, cache_name, refresh)
    if not data:
        return []

    elements = data.get("elements") or []
    ways = [e for e in elements if e.get("type") == "way"]
    print(f"    {len(ways)} OSM ways returned")

    features = []
    for i, elem in enumerate(ways, 1):
        feat = _osm_way_to_span(elem, region, i)
        if feat:
            features.append(feat)

    print(f"    Converted: {len(features)} span features")
    return features


def _fetch_region_nodes(region: str, bbox: tuple, refresh: bool, seq_map: dict) -> list[dict]:
    south, west, north, east = bbox
    query = NODE_QUERY_TEMPLATE.format(south=south, west=west, north=north, east=east)
    cache_name = f"osm_nodes_{region}.json"

    print(f"  Fetching OSM nodes for {region} ...")
    data = _run_overpass(query, cache_name, refresh)
    if not data:
        return []

    elements = data.get("elements") or []
    features = []
    for elem in elements:
        feat = _osm_node_to_ofm(elem, seq_map)
        if feat:
            features.append(feat)

    print(f"    Converted: {len(features)} node features")
    return features


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def fetch(regions: Optional[list[str]] = None, refresh: bool = False) -> dict[str, dict]:
    print("\n=== OSM Overpass fetcher ===")

    if regions is None:
        regions = list(REGION_BBOXES.keys())

    all_nodes: list[dict] = []
    node_seq_map: dict[str, int] = {}
    results: dict[str, dict] = {}

    for region in regions:
        if region not in REGION_BBOXES:
            print(f"  WARN: Unknown region '{region}', skipping")
            continue

        bbox = REGION_BBOXES[region]

        span_features = _fetch_region_spans(region, bbox, refresh)
        if span_features:
            fc = feature_collection(
                span_features,
                name=f"OpenFiberMap-Spans-OSM-{region.title()}",
                description=f"Fiber optic ways from OpenStreetMap — {region}",
                license=LICENSE, attribution=ATTRIBUTION, source=SOURCE,
            )
            out_path = PUBLIC_DATA / f"spans-osm-{region}.geojson"
            save_geojson(fc, out_path)
            results[f"spans-osm-{region}.geojson"] = fc
        else:
            print(f"  INFO: No OSM span data for {region} (API may be slow; try --refresh)")

        node_features = _fetch_region_nodes(region, bbox, refresh, node_seq_map)
        all_nodes.extend(node_features)

        time.sleep(1)   # be polite to Overpass

    if all_nodes:
        nodes_fc = feature_collection(
            all_nodes,
            name="OpenFiberMap-Nodes-OSM-Global",
            description="Telecom exchange and data center nodes from OpenStreetMap",
            license=LICENSE, attribution=ATTRIBUTION, source=SOURCE,
        )
        out_path = PUBLIC_DATA / "nodes-osm-global.geojson"
        save_geojson(nodes_fc, out_path)
        results["nodes-osm-global.geojson"] = nodes_fc

    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch OSM fiber infrastructure via Overpass")
    parser.add_argument(
        "--regions", nargs="+",
        choices=list(REGION_BBOXES.keys()),
        default=list(REGION_BBOXES.keys()),
        help="Regions to query (default: all)"
    )
    parser.add_argument("--refresh", action="store_true", help="Force re-download ignoring cache")
    args = parser.parse_args()
    fetch(regions=args.regions, refresh=args.refresh)


if __name__ == "__main__":
    main()
