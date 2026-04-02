#!/usr/bin/env python3
"""
generate_czml.py — Convert OpenFiberMap GeoJSON to Cesium CZML.

CZML is the native format for CesiumJS. It allows us to express per-feature
styling, labels, and properties natively understood by the Cesium engine.

This generator creates two CZML files:
  public/data/fiber-spans.czml    — Polylines for fiber routes
  public/data/fiber-nodes.czml    — Billboards for network nodes

Styling rules encoded here:
  Spans:
    color   → capacity_class (ultra-high=cyan, high=green, medium=yellow, low=orange, unknown=grey)
    alpha   → status (deployed=1.0, planned=0.5, under-construction=0.75, unknown=0.3)
    width   → capacity_class (ultra-high=4, high=3, medium=2, low=1.5, unknown=1)
    glowPower → 0.1 for deployed, 0.05 for others (used in custom shader)

  Nodes:
    billboard image → node_type (ixp, data-center, pop, landing-station, etc.)
    scale → 0.6–1.0 depending on importance
    label → name_short or name (shown on zoom in)

Usage:
  python scripts/etl/generate_czml.py
  python scripts/etl/generate_czml.py --input public/data/fiber-global.geojson
  python scripts/etl/generate_czml.py --split   # one CZML per continent
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.etl.utils import PUBLIC_DATA, load_geojson

# ---------------------------------------------------------------------------
# Color + style definitions
# ---------------------------------------------------------------------------

# RGBA 0–255
CAPACITY_COLORS = {
    "ultra-high": [0,   230, 255, 255],   # bright cyan
    "high":       [50,  200, 80,  255],   # green
    "medium":     [255, 200, 0,   255],   # yellow
    "low":        [255, 120, 0,   255],   # orange
    "unknown":    [140, 140, 140, 200],   # grey
}

STATUS_ALPHAS = {
    "deployed":           1.0,
    "lit":                1.0,
    "ready-for-service":  0.9,
    "under-construction": 0.75,
    "planned":            0.45,
    "decommissioned":     0.25,
    "unknown":            0.3,
}

CAPACITY_WIDTHS = {
    "ultra-high": 4.0,
    "high":       3.0,
    "medium":     2.0,
    "low":        1.5,
    "unknown":    1.0,
}

# Node billboard images — relative to /public/icons/ in the web app.
# These SVG icon names are defined in Phase 3.
NODE_ICONS = {
    "ixp":             "/icons/ixp.png",
    "data-center":     "/icons/datacenter.png",
    "pop":             "/icons/pop.png",
    "landing-station": "/icons/landing.png",
    "amplifier":       "/icons/amplifier.png",
    "exchange":        "/icons/exchange.png",
    "telecom-hotel":   "/icons/datacenter.png",
    "government-node": "/icons/pop.png",
    "research-node":   "/icons/pop.png",
    "unknown":         "/icons/pop.png",
}

NODE_SCALES = {
    "ixp":             0.9,
    "data-center":     1.0,
    "pop":             0.7,
    "landing-station": 1.0,
    "amplifier":       0.5,
    "exchange":        0.6,
    "telecom-hotel":   0.8,
    "government-node": 0.65,
    "research-node":   0.65,
    "unknown":         0.5,
}


# ---------------------------------------------------------------------------
# CZML packet builders
# ---------------------------------------------------------------------------

def _rgba_with_alpha(base_rgba: list[int], alpha: float) -> list[int]:
    return [base_rgba[0], base_rgba[1], base_rgba[2], int(base_rgba[3] * alpha)]


def _span_packet(feat: dict, czml_id: str) -> Optional[dict]:
    """Build a CZML polyline packet from a fiber-spans feature."""
    props = feat.get("properties") or {}
    geom  = feat.get("geometry") or {}
    geom_type = geom.get("type", "")
    raw_coords = geom.get("coordinates") or []

    if not raw_coords:
        return None

    # Flatten MultiLineString to list of LineStrings for separate packets
    # For simplicity we take the first LineString only; caller will handle multi.
    if geom_type == "MultiLineString":
        if not raw_coords[0]:
            return None
        coords = raw_coords[0]
    elif geom_type == "LineString":
        coords = raw_coords
    else:
        return None

    if len(coords) < 2:
        return None

    # Build flat [lon, lat, alt, lon, lat, alt, ...] Cartographic Degrees array
    positions: list[float] = []
    for pt in coords:
        if len(pt) >= 2:
            positions.extend([pt[0], pt[1], 0.0])

    capacity_class = props.get("capacity_class") or "unknown"
    status = props.get("status") or "unknown"
    alpha = STATUS_ALPHAS.get(status, 0.5)
    base_color = CAPACITY_COLORS.get(capacity_class, CAPACITY_COLORS["unknown"])
    rgba = _rgba_with_alpha(base_color, alpha)
    width = CAPACITY_WIDTHS.get(capacity_class, 1.0)

    # Description HTML popup
    description = _span_description_html(props)

    packet: dict[str, Any] = {
        "id": czml_id,
        "name": props.get("name") or props.get("operator") or czml_id,
        "description": {"string": description},
        "properties": {
            "span_id":        props.get("span_id"),
            "operator":       props.get("operator"),
            "status":         props.get("status"),
            "capacity_gbps":  props.get("capacity_gbps"),
            "capacity_class": capacity_class,
            "length_km":      props.get("length_km"),
            "burial_type":    props.get("burial_type"),
            "region":         props.get("region"),
            "country_iso":    props.get("country_iso"),
            "source":         props.get("source"),
            "source_url":     props.get("source_url"),
            "license":        props.get("license"),
        },
        "polyline": {
            "positions": {
                "cartographicDegrees": positions,
            },
            "material": {
                "polylineOutline": {
                    "color": {
                        "rgba": rgba,
                    },
                    "outlineColor": {
                        "rgba": [0, 0, 0, int(alpha * 80)],
                    },
                    "outlineWidth": 0.5,
                }
            },
            "width": width,
            "clampToGround": True,
            "shadows": "DISABLED",
            "show": True,
        }
    }

    # Dashed line for planned routes
    if status in ("planned", "under-construction"):
        packet["polyline"]["material"] = {
            "polylineDash": {
                "color": {"rgba": rgba},
                "gapColor": {"rgba": [0, 0, 0, 0]},
                "dashLength": 16.0,
                "dashPattern": status == "planned" and 255 or 65278,
            }
        }

    return packet


def _node_packet(feat: dict, czml_id: str) -> Optional[dict]:
    """Build a CZML billboard packet from a fiber-nodes feature."""
    props = feat.get("properties") or {}
    geom  = feat.get("geometry") or {}
    coords = geom.get("coordinates") or []

    if len(coords) < 2:
        return None

    lon, lat = float(coords[0]), float(coords[1])
    node_type = props.get("node_type") or "unknown"
    icon = NODE_ICONS.get(node_type, NODE_ICONS["unknown"])
    scale = NODE_SCALES.get(node_type, 0.6)
    name = props.get("name") or czml_id
    short = props.get("name_short") or name[:20]

    description = _node_description_html(props)

    packet: dict[str, Any] = {
        "id": czml_id,
        "name": name,
        "description": {"string": description},
        "properties": {
            "node_id":        props.get("node_id"),
            "node_type":      node_type,
            "operator":       props.get("operator"),
            "status":         props.get("status"),
            "city":           props.get("city"),
            "country_iso":    props.get("country_iso"),
            "region":         props.get("region"),
            "peeringdb_id":   props.get("peeringdb_id"),
            "peeringdb_ix_id":props.get("peeringdb_ix_id"),
            "source":         props.get("source"),
            "source_url":     props.get("source_url"),
        },
        "position": {
            "cartographicDegrees": [lon, lat, 0.0],
        },
        "billboard": {
            "image": icon,
            "scale": scale,
            "verticalOrigin": "BOTTOM",
            "heightReference": "CLAMP_TO_GROUND",
            "disableDepthTestDistance": 1_500_000,  # always visible up to 1500 km
            "show": True,
        },
        "label": {
            "text": short,
            "font": "11pt sans-serif",
            "fillColor": {"rgba": [255, 255, 255, 230]},
            "outlineColor": {"rgba": [0, 0, 0, 180]},
            "outlineWidth": 2,
            "style": "FILL_AND_OUTLINE",
            "verticalOrigin": "TOP",
            "pixelOffset": {"cartesian2": [0, 8]},
            "heightReference": "CLAMP_TO_GROUND",
            "disableDepthTestDistance": 800_000,
            "translucencyByDistance": {
                "nearFarScalar": [500_000, 1.0, 3_000_000, 0.0],
            },
            "show": True,
        }
    }

    return packet


# ---------------------------------------------------------------------------
# HTML description builders (shown in Cesium info box)
# ---------------------------------------------------------------------------

def _row(label: str, value: Any) -> str:
    if value is None or value == "":
        return ""
    return f"<tr><td><b>{label}</b></td><td>{value}</td></tr>"


def _span_description_html(props: dict) -> str:
    source_url = props.get("source_url") or ""
    source_link = f'<a href="{source_url}" target="_blank">{props.get("source", "")}</a>' if source_url else props.get("source", "")
    rows = "".join([
        _row("Operator",        props.get("operator")),
        _row("Status",          props.get("status")),
        _row("Capacity",        f"{props.get('capacity_gbps')} Gbps" if props.get('capacity_gbps') else None),
        _row("Length",          f"{props.get('length_km')} km" if props.get('length_km') else None),
        _row("Burial type",     props.get("burial_type")),
        _row("Countries",       ", ".join(props.get("countries") or []) or props.get("country_iso")),
        _row("Phase",           props.get("phase_name")),
        _row("Funders",         ", ".join(props.get("funders") or []) or None),
        _row("Source",          source_link),
        _row("License",         props.get("license")),
        _row("Last updated",    props.get("last_updated")),
        _row("Notes",           props.get("notes")),
    ])
    return f"<table>{rows}</table>"


def _node_description_html(props: dict) -> str:
    source_url = props.get("source_url") or ""
    source_link = f'<a href="{source_url}" target="_blank">{props.get("source", "")}</a>' if source_url else props.get("source", "")
    website = props.get("website")
    website_link = f'<a href="{website}" target="_blank">{website}</a>' if website else None
    pdb_id = props.get("peeringdb_id") or props.get("peeringdb_ix_id")
    pdb_link = f'<a href="https://www.peeringdb.com/fac/{pdb_id}" target="_blank">PeeringDB #{pdb_id}</a>' if pdb_id else None
    rows = "".join([
        _row("Type",        props.get("node_type")),
        _row("Operator",    props.get("operator")),
        _row("Status",      props.get("status")),
        _row("City",        props.get("city")),
        _row("Country",     props.get("country_iso")),
        _row("Website",     website_link),
        _row("PeeringDB",   pdb_link),
        _row("Floor space", f"{props.get('floor_space_sqm')} m²" if props.get('floor_space_sqm') else None),
        _row("Power",       f"{props.get('power_mw')} MW" if props.get('power_mw') else None),
        _row("Source",      source_link),
        _row("License",     props.get("license")),
        _row("Notes",       props.get("notes")),
    ])
    return f"<table>{rows}</table>"


# ---------------------------------------------------------------------------
# CZML document builders
# ---------------------------------------------------------------------------

def _czml_document_packet(name: str) -> dict:
    return {
        "id": "document",
        "name": name,
        "version": "1.0",
        "clock": {
            "interval": "2020-01-01T00:00:00Z/2030-12-31T23:59:59Z",
            "currentTime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "multiplier": 1,
        }
    }


def build_czml(features: list[dict], name: str) -> list[dict]:
    """Convert a list of GeoJSON features to a CZML packet list."""
    packets: list[dict] = [_czml_document_packet(name)]
    span_seq: dict[str, int] = {}
    node_seq: dict[str, int] = {}

    for feat in features:
        props = feat.get("properties") or {}
        layer = props.get("ofm_layer", "")

        if layer == "fiber-spans":
            span_id = props.get("span_id") or "span"
            seq = span_seq.get(span_id, 0) + 1
            span_seq[span_id] = seq
            czml_id = f"span/{span_id}" if seq == 1 else f"span/{span_id}/{seq}"

            geom = feat.get("geometry") or {}
            if geom.get("type") == "MultiLineString":
                # Emit one packet per LineString segment
                coords_list = geom.get("coordinates") or []
                for i, coords in enumerate(coords_list):
                    sub_feat = {
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": coords},
                        "properties": feat["properties"],
                    }
                    pkt = _span_packet(sub_feat, f"{czml_id}/seg{i}")
                    if pkt:
                        packets.append(pkt)
            else:
                pkt = _span_packet(feat, czml_id)
                if pkt:
                    packets.append(pkt)

        elif layer == "fiber-nodes":
            node_id = props.get("node_id") or "node"
            seq = node_seq.get(node_id, 0) + 1
            node_seq[node_id] = seq
            czml_id = f"node/{node_id}" if seq == 1 else f"node/{node_id}/{seq}"

            pkt = _node_packet(feat, czml_id)
            if pkt:
                packets.append(pkt)

    return packets


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate(input_path: Optional[Path] = None, split: bool = False) -> None:
    print("\n=== CZML generator ===")

    if input_path is None:
        input_path = PUBLIC_DATA / "fiber-global.geojson"

    if not input_path.exists():
        print(f"  ERROR: Input file not found: {input_path}")
        print("  Run merge.py first.")
        return

    fc = load_geojson(input_path)
    features = fc.get("features") or []
    print(f"  Loaded {len(features)} features from {input_path.name}")

    spans = [f for f in features if (f.get("properties") or {}).get("ofm_layer") == "fiber-spans"]
    nodes = [f for f in features if (f.get("properties") or {}).get("ofm_layer") == "fiber-nodes"]

    # Spans CZML
    spans_czml = build_czml(spans, "OpenFiberMap Fiber Routes")
    spans_out = PUBLIC_DATA / "fiber-spans.czml"
    with open(spans_out, "w", encoding="utf-8") as f:
        json.dump(spans_czml, f, ensure_ascii=False, separators=(",", ":"))
    kb = spans_out.stat().st_size / 1024
    print(f"  Spans CZML: {len(spans_czml)-1} packets → {spans_out} ({kb:.0f} KB)")

    # Nodes CZML
    nodes_czml = build_czml(nodes, "OpenFiberMap Fiber Nodes")
    nodes_out = PUBLIC_DATA / "fiber-nodes.czml"
    with open(nodes_out, "w", encoding="utf-8") as f:
        json.dump(nodes_czml, f, ensure_ascii=False, separators=(",", ":"))
    kb = nodes_out.stat().st_size / 1024
    print(f"  Nodes CZML: {len(nodes_czml)-1} packets → {nodes_out} ({kb:.0f} KB)")

    if split:
        # Per-continent CZML
        regions = set()
        for feat in features:
            r = (feat.get("properties") or {}).get("region") or "global"
            regions.add(r)

        for region in regions:
            region_feats = [
                f for f in features
                if (f.get("properties") or {}).get("region") == region
            ]
            region_czml = build_czml(region_feats, f"OpenFiberMap — {region.title()}")
            out = PUBLIC_DATA / f"fiber-{region}.czml"
            with open(out, "w") as f:
                json.dump(region_czml, f, ensure_ascii=False, separators=(",", ":"))
            kb = out.stat().st_size / 1024
            print(f"  {region} CZML: {len(region_czml)-1} packets → {out} ({kb:.0f} KB)")


def main():
    parser = argparse.ArgumentParser(description="Generate CZML from OpenFiberMap GeoJSON")
    parser.add_argument("--input", type=Path, help="Input GeoJSON file (default: fiber-global.geojson)")
    parser.add_argument("--split", action="store_true", help="Also generate per-continent CZML files")
    args = parser.parse_args()
    generate(input_path=args.input, split=args.split)


if __name__ == "__main__":
    main()
