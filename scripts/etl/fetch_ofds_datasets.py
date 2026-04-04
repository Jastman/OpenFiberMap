#!/usr/bin/env python3
"""
fetch_ofds_datasets.py — Download OFDS-format GeoJSON from stevesong/OFDS-datasets.

The repository organises data as:
  {country}/{operator}/nodes.geojson
  {country}/{operator}/spans.geojson

We enumerate the GitHub tree, download every nodes/spans file, convert each
to the OpenFiberMap schema, and merge into a single output per continent.

License of source data varies per operator file; we tag each feature with the
closest known license (defaults to CC-BY-4.0) and flag uncertainty in notes.

Outputs:
  public/data/spans-ofds-africa.geojson
  public/data/spans-ofds-americas.geojson
  public/data/nodes-ofds-africa.geojson
  public/data/nodes-ofds-americas.geojson

Usage:
  python scripts/etl/fetch_ofds_datasets.py
  python scripts/etl/fetch_ofds_datasets.py --refresh
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
    PUBLIC_DATA, RAW_CACHE,
    get_json, get_text, save_geojson, feature_collection,
    span_feature, node_feature, slugify, make_node_id, make_span_id,
    region_from_iso, classify_capacity,
    is_cached, read_cache, write_cache,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_API      = "https://api.github.com"
REPO_OWNER      = "stevesong"
REPO_NAME       = "OFDS-datasets"
DEFAULT_BRANCH  = "main"
RAW_BASE        = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{DEFAULT_BRANCH}"

SOURCE          = "OFDS-datasets"
ATTRIBUTION     = "stevesong/OFDS-datasets (CC-BY) — https://github.com/stevesong/OFDS-datasets"
DEFAULT_LICENSE = "CC-BY-4.0"

# ISO alpha-2 → continent bucket
AFRICA_CODES = {
    "AO","BJ","BW","BI","CM","CF","TD","CG","CD","CI","DJ","EG","GQ","ER","ET",
    "GA","GM","GH","GN","GW","KE","LS","LR","LY","MG","MW","ML","MR","MU","MA",
    "MZ","NA","NE","NG","RW","ST","SN","SL","SO","ZA","SS","SD","SZ","TZ","TG",
    "TN","UG","ZM","ZW","DZ",
}
AMERICAS_CODES = {
    "AR","BB","BZ","BO","BR","CA","CL","CO","CR","CU","DO","EC","SV","GT","GY",
    "HT","HN","JM","MX","NI","PA","PY","PE","PR","TT","US","UY","VE",
}

# OFDS status → OFM status
OFDS_STATUS_MAP = {
    "deployed":           "deployed",
    "ready for service":  "ready-for-service",
    "lit":                "lit",
    "under construction": "under-construction",
    "planning":           "planned",
    "Deployed":           "deployed",
    "Ready for Service":  "ready-for-service",
    "Under Construction": "under-construction",
    "Planning":           "planned",
}

# OFDS physicalInfrastructureProvider fields / burial
BURIAL_MAP = {
    "Aerial":        "aerial",
    "Underground":   "underground",
    "Subsea":        "subsea",
    "Direct Buried": "direct-buried",
    "Conduit":       "conduit",
    "Mixed":         "mixed",
    "Unknown":       "unknown",
}


# ---------------------------------------------------------------------------
# GitHub tree enumeration
# ---------------------------------------------------------------------------

def _get_tree(refresh: bool) -> list[dict]:
    """Return flat GitHub tree for the repo."""
    cache_name = "ofds_tree.json"
    if not refresh and is_cached(cache_name, max_age_hours=24):
        return json.loads(read_cache(cache_name))

    url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/{DEFAULT_BRANCH}"
    data = get_json(url, params={"recursive": "1"})
    tree = data.get("tree", [])
    write_cache(cache_name, json.dumps(tree).encode())
    return tree


def _find_geojson_files(tree: list[dict]) -> dict[str, list[str]]:
    """
    Return dict mapping file path → type ('spans' or 'nodes') for all
    span/node GeoJSON files in the tree.

    Matches any .geojson file with 'span' or 'node' in the filename, e.g.:
      Tanzania/NICTBB/NIC_ofds-spans_16apr2024.geojson
      Rwanda/Rwanda_National_Backbone/RWA_ofds-nodes_16apr2024.geojson
      Kenya/NOFBI/spans.geojson
    """
    files: dict[str, list[str]] = {"spans": [], "nodes": []}
    for item in tree:
        path = item.get("path", "")
        if item.get("type") != "blob":
            continue
        if not path.lower().endswith(".geojson"):
            continue
        filename = path.split("/")[-1].lower()
        if "span" in filename:
            files["spans"].append(path)
        elif "node" in filename:
            files["nodes"].append(path)
    return files


# ---------------------------------------------------------------------------
# Download individual files
# ---------------------------------------------------------------------------

def _fetch_file(path: str, refresh: bool) -> Optional[dict]:
    cache_name = f"ofds_{path.replace('/', '_')}"
    if not refresh and is_cached(cache_name, max_age_hours=48):
        raw = read_cache(cache_name)
    else:
        url = f"{RAW_BASE}/{path}"
        try:
            text = get_text(url, timeout=30)
            raw = text.encode()
            write_cache(cache_name, raw)
            time.sleep(0.1)   # polite crawl delay
        except Exception as e:
            print(f"    WARN: Failed to fetch {path}: {e}")
            return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"    WARN: JSON error in {path}: {e}")
        return None


# ---------------------------------------------------------------------------
# Parse path to extract country + operator
# ---------------------------------------------------------------------------

def _parse_path(path: str) -> tuple[str, str]:
    """
    'angola/angola-telecom/spans.geojson' → ('AO', 'Angola Telecom')
    Falls back to directory names if lookup fails.
    """
    parts = path.split("/")
    country_dir = parts[0].lower() if len(parts) >= 1 else "unknown"
    operator_dir = parts[1] if len(parts) >= 3 else country_dir

    country_iso = COUNTRY_DIR_MAP.get(country_dir, country_dir.upper()[:2])
    operator_name = operator_dir.replace("-", " ").title()
    return country_iso, operator_name


# Directory name → ISO alpha-2
COUNTRY_DIR_MAP: dict[str, str] = {
    # Africa
    "angola": "AO", "botswana": "BW", "burundi": "BI", "cameroon": "CM",
    "drc": "CD", "congo": "CD", "kenya": "KE", "mozambique": "MZ", "namibia": "NA",
    "niger": "NE", "nigeria": "NG", "rwanda": "RW",
    "south-africa": "ZA", "south_africa": "ZA", "southafrica": "ZA",
    "sudan": "SD", "tanzania": "TZ", "togo": "TG", "uganda": "UG",
    "zambia": "ZM", "zimbabwe": "ZW", "ghana": "GH", "ethiopia": "ET",
    "senegal": "SN", "côte-d'ivoire": "CI", "cote-d-ivoire": "CI",
    "ivory-coast": "CI", "mali": "ML", "malawi": "MW", "madagascar": "MG",
    "somalia": "SO", "eritrea": "ER", "south-sudan": "SS", "south_sudan": "SS",
    # Americas
    "brazil": "BR", "canada": "CA", "costa-rica": "CR", "costa_rica": "CR",
    "nicaragua": "NI", "panama": "PA", "venezuela": "VE", "chile": "CL",
    "colombia": "CO", "peru": "PE", "argentina": "AR", "mexico": "MX",
    "ecuador": "EC", "bolivia": "BO", "paraguay": "PY", "uruguay": "UY",
    # Other
    "australia": "AU", "new-zealand": "NZ", "new_zealand": "NZ",
    "georgia": "GE",
}


# ---------------------------------------------------------------------------
# OFDS → OFM feature converters
# ---------------------------------------------------------------------------

def _ofds_span_to_ofm(feat: dict, country_iso: str, operator: str, path: str, seq: int) -> Optional[dict]:
    props = feat.get("properties") or {}
    geom  = feat.get("geometry") or {}

    # Require valid LineString geometry
    geom_type = geom.get("type", "")
    if geom_type not in ("LineString", "MultiLineString"):
        return None
    coords = geom.get("coordinates")
    if not coords:
        return None

    # OFDS v0.3.0 uses network.name; v1.0 may use operator directly
    network_obj = props.get("network") or {}
    network_name = network_obj.get("name") if isinstance(network_obj, dict) else None
    resolved_operator = network_name or operator

    network_id = f"{country_iso.lower()}-{slugify(resolved_operator)}"
    span_id    = make_span_id(network_id, seq)
    region     = region_from_iso(country_iso)

    # Map OFDS status (v0.3.0 may not have status; v1.0 does)
    ofds_status = props.get("status") or (props.get("deploymentDetails") or {}).get("deploymentState", "")
    status = OFDS_STATUS_MAP.get(ofds_status, "unknown")

    # Burial type
    burial_raw = ((props.get("physicalInfrastructureProvider") or {}).get("type", "")
                  or (props.get("deploymentDetails") or {}).get("fibreType", ""))
    burial = BURIAL_MAP.get(burial_raw, None)

    # Capacity
    capacity_raw = props.get("capacity") or props.get("capacityDetails") or {}
    capacity_gbps = None
    if isinstance(capacity_raw, dict):
        capacity_gbps = capacity_raw.get("capacity")
    elif isinstance(capacity_raw, (int, float)):
        capacity_gbps = float(capacity_raw)

    # Length
    length_km = props.get("lengthKm") or props.get("length") or None
    if length_km:
        try:
            length_km = float(length_km)
        except (TypeError, ValueError):
            length_km = None

    # OFDS original span id
    ofds_span_id = props.get("id") or props.get("spanId") or None

    # Name — use span name, falling back to network name
    name = props.get("name") or network_name or None

    return span_feature(
        span_id=span_id,
        network_id=network_id,
        name=name,
        operator=resolved_operator,
        coordinates=coords,
        country_iso=country_iso,
        countries=[country_iso],
        region=region,
        status=status,
        burial_type=burial,
        length_km=length_km,
        capacity_gbps=capacity_gbps,
        source=SOURCE,
        source_url=f"https://github.com/{REPO_OWNER}/{REPO_NAME}/blob/{DEFAULT_BRANCH}/{path}",
        license=DEFAULT_LICENSE,
        attribution=ATTRIBUTION,
        notes="Geometry from OFDS-datasets (testing quality, not authoritative).",
        ofds_span_id=ofds_span_id,
    )


def _ofds_node_to_ofm(feat: dict, country_iso: str, operator: str, path: str, seq: int) -> Optional[dict]:
    props = feat.get("properties") or {}
    geom  = feat.get("geometry") or {}

    if geom.get("type") != "Point":
        return None
    coords = geom.get("coordinates")
    if not coords or len(coords) < 2:
        return None

    lon, lat = float(coords[0]), float(coords[1])

    # Determine node type from OFDS "type" field
    ofds_type = (props.get("type") or "").lower()
    node_type_map = {
        "ixp": "ixp",
        "internet exchange": "ixp",
        "data centre": "data-center",
        "data center": "data-center",
        "pop": "pop",
        "point of presence": "pop",
        "landing station": "landing-station",
        "cable landing station": "landing-station",
        "amplifier": "amplifier",
        "exchange": "exchange",
    }
    node_type = node_type_map.get(ofds_type, "pop")

    name = props.get("name") or props.get("id") or f"{operator} Node {seq}"
    slug = slugify(props.get("name") or operator)
    region = region_from_iso(country_iso)
    node_id = make_node_id(node_type, country_iso, slug, seq)
    network_id = f"{country_iso.lower()}-{slugify(operator)}"

    return node_feature(
        node_id=node_id,
        network_id=network_id,
        name=name,
        operator=operator,
        node_type=node_type,
        lon=lon,
        lat=lat,
        status="operational",
        country_iso=country_iso,
        region=region,
        source=SOURCE,
        source_url=f"https://github.com/{REPO_OWNER}/{REPO_NAME}/blob/{DEFAULT_BRANCH}/{path}",
        license=DEFAULT_LICENSE,
        attribution=ATTRIBUTION,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def fetch(refresh: bool = False) -> dict[str, dict]:
    print("\n=== OFDS-datasets fetcher ===")

    tree = _get_tree(refresh)
    files = _find_geojson_files(tree)
    print(f"  Found {len(files['spans'])} span files, {len(files['nodes'])} node files")

    # Buckets: continent → feature list
    buckets: dict[str, dict[str, list]] = {
        "africa":   {"spans": [], "nodes": []},
        "americas": {"spans": [], "nodes": []},
        "other":    {"spans": [], "nodes": []},
    }

    def _bucket(country_iso: str) -> str:
        if country_iso in AFRICA_CODES:
            return "africa"
        if country_iso in AMERICAS_CODES:
            return "americas"
        return "other"

    # Process span files
    for path in files["spans"]:
        country_iso, operator = _parse_path(path)
        geojson = _fetch_file(path, refresh)
        if not geojson:
            continue
        features = geojson.get("features") or []
        seq = 1
        for feat in features:
            ofm = _ofds_span_to_ofm(feat, country_iso, operator, path, seq)
            if ofm:
                buckets[_bucket(country_iso)]["spans"].append(ofm)
                seq += 1

    # Process node files
    for path in files["nodes"]:
        country_iso, operator = _parse_path(path)
        geojson = _fetch_file(path, refresh)
        if not geojson:
            continue
        features = geojson.get("features") or []
        seq = 1
        for feat in features:
            ofm = _ofds_node_to_ofm(feat, country_iso, operator, path, seq)
            if ofm:
                buckets[_bucket(country_iso)]["nodes"].append(ofm)
                seq += 1

    # Save output files
    results: dict[str, dict] = {}
    for continent, layers in buckets.items():
        for layer_type, features in layers.items():
            if not features:
                continue
            fc = feature_collection(
                features,
                name=f"OpenFiberMap-{layer_type.title()}-OFDS-{continent.title()}",
                description=f"Fiber {layer_type} for {continent} from OFDS-datasets",
                license=DEFAULT_LICENSE,
                attribution=ATTRIBUTION,
                source=SOURCE,
            )
            out_name = f"{layer_type}-ofds-{continent}.geojson"
            out_path = PUBLIC_DATA / out_name
            save_geojson(fc, out_path)
            results[out_name] = fc

    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch OFDS-datasets spans and nodes")
    parser.add_argument("--refresh", action="store_true", help="Force re-download ignoring cache")
    args = parser.parse_args()
    fetch(refresh=args.refresh)


if __name__ == "__main__":
    main()
