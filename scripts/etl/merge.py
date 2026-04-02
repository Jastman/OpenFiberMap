#!/usr/bin/env python3
"""
merge.py — Merge all per-source GeoJSON files in public/data/ into unified
           fiber-global.geojson and continent-level files.

Deduplication strategy:
  - Spans: deduplicate by (operator, approximate bbox hash) — prevents the
    same physical route from appearing twice if covered by two sources.
  - Nodes: deduplicate by (node_type, lat≈, lon≈) within ~200m.

Outputs:
  public/data/fiber-global.geojson    (ALL features)
  public/data/spans-global.geojson    (spans only)
  public/data/nodes-global.geojson    (nodes only)
  public/data/fiber-africa.geojson    (Africa features)
  public/data/fiber-americas.geojson  (Americas features)
  public/data/fiber-europe.geojson    (Europe features)
  public/data/metadata.json           (dataset statistics)

Usage:
  python scripts/etl/merge.py
  python scripts/etl/merge.py --no-dedup   # skip deduplication
  python scripts/etl/merge.py --stats      # print detailed stats
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.etl.utils import (
    PUBLIC_DATA,
    save_geojson, feature_collection, load_geojson,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# File patterns to include (in priority order — first source wins for dedup)
INCLUDE_PATTERNS = [
    # Highest priority: authoritative sources
    "spans-afterfibre-africa.geojson",
    "nodes-afterfibre-africa.geojson",
    "spans-brazil.geojson",
    "nodes-brazil.geojson",
    # OFDS-derived
    "spans-ofds-africa.geojson",
    "nodes-ofds-africa.geojson",
    "spans-ofds-americas.geojson",
    "nodes-ofds-americas.geojson",
    "spans-ofds-other.geojson",
    "nodes-ofds-other.geojson",
    # Node registries
    "nodes-peeringdb.geojson",
    "nodes-landing-stations.geojson",
    # OSM gap-fill (lower priority)
    "spans-osm-africa.geojson",
    "spans-osm-americas.geojson",
    "spans-osm-europe.geojson",
    "spans-osm-asia.geojson",
    "nodes-osm-global.geojson",
]

# Do NOT include the output files themselves
EXCLUDE_PREFIXES = ["fiber-", "spans-global", "nodes-global", "metadata"]

# Dedup tolerance for nodes (~200 m in degrees)
NODE_DEDUP_TOLERANCE = 0.002

# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _coord_bbox_key(coords: list, precision: int = 1) -> str:
    """Return a rough bbox string for a LineString's coordinates."""
    if not coords:
        return ""
    if isinstance(coords[0], list) and isinstance(coords[0][0], list):
        # MultiLineString
        flat = [pt for ring in coords for pt in ring]
    else:
        flat = coords
    lons = [c[0] for c in flat if len(c) >= 2]
    lats = [c[1] for c in flat if len(c) >= 2]
    if not lons:
        return ""
    return (
        f"{round(min(lons), precision)},{round(min(lats), precision)},"
        f"{round(max(lons), precision)},{round(max(lats), precision)}"
    )


def _span_dedup_key(feat: dict) -> str:
    props = feat.get("properties") or {}
    geom  = feat.get("geometry") or {}
    operator = (props.get("operator") or "").lower()[:20]
    bbox = _coord_bbox_key(geom.get("coordinates") or [])
    return f"{operator}||{bbox}"


def _node_dedup_key(feat: dict) -> str:
    props = feat.get("properties") or {}
    geom  = feat.get("geometry") or {}
    coords = geom.get("coordinates") or [0, 0]
    node_type = props.get("node_type") or ""
    # Round to ~200m grid
    lon_r = round(coords[0] / NODE_DEDUP_TOLERANCE) * NODE_DEDUP_TOLERANCE
    lat_r = round(coords[1] / NODE_DEDUP_TOLERANCE) * NODE_DEDUP_TOLERANCE
    return f"{node_type}||{lon_r:.3f},{lat_r:.3f}"


def deduplicate(features: list[dict]) -> list[dict]:
    """Remove near-duplicate features, keeping the first (highest-priority) occurrence."""
    seen_spans: set[str] = set()
    seen_nodes: set[str] = set()
    result: list[dict] = []

    for feat in features:
        props = feat.get("properties") or {}
        layer = props.get("ofm_layer", "")

        if layer == "fiber-spans":
            key = _span_dedup_key(feat)
            if key and key in seen_spans:
                continue
            seen_spans.add(key)
        elif layer == "fiber-nodes":
            key = _node_dedup_key(feat)
            if key in seen_nodes:
                continue
            seen_nodes.add(key)

        result.append(feat)

    return result


# ---------------------------------------------------------------------------
# Region classifier
# ---------------------------------------------------------------------------

REGION_NAMES = ["africa", "americas", "europe", "asia-pacific", "middle-east", "global"]


def _feature_region(feat: dict) -> str:
    props = feat.get("properties") or {}
    return props.get("region") or "global"


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def _compute_stats(features: list[dict]) -> dict:
    spans = [f for f in features if (f.get("properties") or {}).get("ofm_layer") == "fiber-spans"]
    nodes = [f for f in features if (f.get("properties") or {}).get("ofm_layer") == "fiber-nodes"]

    # Span stats
    status_counts: dict[str, int] = defaultdict(int)
    capacity_counts: dict[str, int] = defaultdict(int)
    source_counts: dict[str, int] = defaultdict(int)
    region_counts: dict[str, int] = defaultdict(int)
    total_km = 0.0

    for f in spans:
        p = f.get("properties") or {}
        status_counts[p.get("status", "unknown")] += 1
        capacity_counts[p.get("capacity_class", "unknown")] += 1
        source_counts[p.get("source", "unknown")] += 1
        region_counts[p.get("region", "global")] += 1
        km = p.get("length_km") or 0
        total_km += km if km else 0

    # Node stats
    node_type_counts: dict[str, int] = defaultdict(int)
    node_region_counts: dict[str, int] = defaultdict(int)
    node_source_counts: dict[str, int] = defaultdict(int)

    for f in nodes:
        p = f.get("properties") or {}
        node_type_counts[p.get("node_type", "unknown")] += 1
        node_region_counts[p.get("region", "global")] += 1
        node_source_counts[p.get("source", "unknown")] += 1

    return {
        "generated": date.today().isoformat(),
        "total_features": len(features),
        "spans": {
            "count": len(spans),
            "total_km_approx": round(total_km, 1),
            "by_status": dict(status_counts),
            "by_capacity_class": dict(capacity_counts),
            "by_source": dict(source_counts),
            "by_region": dict(region_counts),
        },
        "nodes": {
            "count": len(nodes),
            "by_type": dict(node_type_counts),
            "by_region": dict(node_region_counts),
            "by_source": dict(node_source_counts),
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def merge(no_dedup: bool = False, stats: bool = False) -> dict:
    print("\n=== Merge ===")

    # Collect all input files
    all_features: list[dict] = []
    loaded_files: list[str] = []

    for pattern in INCLUDE_PATTERNS:
        path = PUBLIC_DATA / pattern
        if not path.exists():
            continue
        if any(path.name.startswith(excl) for excl in EXCLUDE_PREFIXES):
            continue
        try:
            fc = load_geojson(path)
            feats = fc.get("features") or []
            all_features.extend(feats)
            loaded_files.append(f"{pattern} ({len(feats)} features)")
        except Exception as e:
            print(f"  WARN: Could not load {pattern}: {e}")

    # Also pick up any extra files matching spans-* or nodes-* not in the priority list
    for path in sorted(PUBLIC_DATA.glob("*.geojson")):
        if path.name in INCLUDE_PATTERNS:
            continue
        if any(path.name.startswith(excl) for excl in EXCLUDE_PREFIXES):
            continue
        if path.name.startswith(("spans-", "nodes-")):
            try:
                fc = load_geojson(path)
                feats = fc.get("features") or []
                all_features.extend(feats)
                loaded_files.append(f"{path.name} ({len(feats)} features)")
            except Exception as e:
                print(f"  WARN: Could not load {path.name}: {e}")

    print(f"  Loaded {len(all_features)} features from {len(loaded_files)} files:")
    for f in loaded_files:
        print(f"    {f}")

    if not no_dedup:
        before = len(all_features)
        all_features = deduplicate(all_features)
        print(f"  Dedup: {before} → {len(all_features)} features ({before - len(all_features)} removed)")

    # --- Global outputs ---
    global_fc = feature_collection(
        all_features,
        name="OpenFiberMap-Global",
        description="Global fiber optic network — all sources merged",
        version="0.1.0",
    )
    save_geojson(global_fc, PUBLIC_DATA / "fiber-global.geojson")

    spans_only = [f for f in all_features if (f.get("properties") or {}).get("ofm_layer") == "fiber-spans"]
    nodes_only = [f for f in all_features if (f.get("properties") or {}).get("ofm_layer") == "fiber-nodes"]

    save_geojson(
        feature_collection(spans_only, name="OpenFiberMap-Spans-Global"),
        PUBLIC_DATA / "spans-global.geojson",
    )
    save_geojson(
        feature_collection(nodes_only, name="OpenFiberMap-Nodes-Global"),
        PUBLIC_DATA / "nodes-global.geojson",
    )

    # --- Per-continent outputs ---
    continent_buckets: dict[str, list[dict]] = defaultdict(list)
    for feat in all_features:
        region = _feature_region(feat)
        bucket = region if region in ("africa", "americas", "europe") else "global"
        continent_buckets[bucket].append(feat)

    for continent, feats in continent_buckets.items():
        save_geojson(
            feature_collection(feats, name=f"OpenFiberMap-{continent.title()}"),
            PUBLIC_DATA / f"fiber-{continent}.geojson",
        )

    # --- Metadata ---
    stat_data = _compute_stats(all_features)
    meta_path = PUBLIC_DATA / "metadata.json"
    with open(meta_path, "w") as f:
        json.dump(stat_data, f, indent=2)
    print(f"\n  metadata.json written")

    if stats:
        print("\n=== Dataset Statistics ===")
        print(json.dumps(stat_data, indent=2))

    return global_fc


def main():
    parser = argparse.ArgumentParser(description="Merge all OpenFiberMap GeoJSON sources")
    parser.add_argument("--no-dedup", action="store_true", help="Skip deduplication")
    parser.add_argument("--stats", action="store_true", help="Print detailed statistics")
    args = parser.parse_args()
    merge(no_dedup=args.no_dedup, stats=args.stats)


if __name__ == "__main__":
    main()
