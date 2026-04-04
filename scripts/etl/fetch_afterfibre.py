#!/usr/bin/env python3
"""
fetch_afterfibre.py — Fetch AfTerFibre Africa fiber backbone data from NSRC.

AfTerFibre (https://afterfibre.nsrc.org) is the most authoritative open
dataset for Africa terrestrial fiber backbone routes. It is maintained by the
Network Startup Resource Center (NSRC) and licensed CC-BY.

The live map serves data via a tile/API endpoint. This fetcher tries several
known endpoint patterns and falls back to a curated hand-coded approximation
of key backbone routes if the API is unavailable (e.g. in CI).

Known endpoint (as of 2025):
  https://afterfibre.nsrc.org/api/v1/network/geojson   (JSON FeatureCollection)
  https://afterfibre.nsrc.org/api/v1/node/geojson

If these change, update SPANS_URL / NODES_URL below.

Outputs:
  public/data/spans-afterfibre-africa.geojson
  public/data/nodes-afterfibre-africa.geojson

Usage:
  python scripts/etl/fetch_afterfibre.py
  python scripts/etl/fetch_afterfibre.py --refresh
  python scripts/etl/fetch_afterfibre.py --offline   # use built-in seed data only
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
    get_json, save_geojson, feature_collection,
    span_feature, node_feature, slugify, make_node_id, make_span_id,
    region_from_iso, classify_capacity,
    is_cached, read_cache, write_cache,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SPANS_URLS = [
    # Current domain (opentelecomdata.org)
    "https://afterfibre.opentelecomdata.org/api/v1/network/geojson",
    "https://afterfibre.opentelecomdata.org/api/networks.geojson",
    "https://afterfibre.opentelecomdata.org/geo/networks.geojson",
    "https://afterfibre.opentelecomdata.org/data/spans.geojson",
    # Legacy domain (nsrc.org)
    "https://afterfibre.nsrc.org/api/v1/network/geojson",
    "https://afterfibre.nsrc.org/api/networks.geojson",
]
NODES_URLS = [
    # Current domain
    "https://afterfibre.opentelecomdata.org/api/v1/node/geojson",
    "https://afterfibre.opentelecomdata.org/api/nodes.geojson",
    "https://afterfibre.opentelecomdata.org/geo/nodes.geojson",
    "https://afterfibre.opentelecomdata.org/data/nodes.geojson",
    # Legacy domain
    "https://afterfibre.nsrc.org/api/v1/node/geojson",
    "https://afterfibre.nsrc.org/api/nodes.geojson",
]

SOURCE      = "AfTerFibre"
LICENSE     = "CC-BY-4.0"
ATTRIBUTION = "AfTerFibre / OpenTelecomData (CC-BY) — https://afterfibre.opentelecomdata.org"

# AfTerFibre status strings → OFM
STATUS_MAP = {
    "live":              "deployed",
    "active":            "deployed",
    "operational":       "deployed",
    "deployed":          "deployed",
    "under construction":"under-construction",
    "planned":           "planned",
    "proposed":          "planned",
    "lit":               "lit",
    "dark":              "deployed",
    "unknown":           "unknown",
}


# ---------------------------------------------------------------------------
# Seed data — curated backup routes (approximate alignments, CC-BY)
# Used if the live API is unreachable.
# ---------------------------------------------------------------------------

SEED_SPANS = [
    # Nigeria backbone
    dict(
        network_id="ng-mainone", operator="MainOne", country_iso="NG",
        name="MainOne Lagos–Abuja", status="deployed", burial_type="underground",
        capacity_gbps=100, length_km=730,
        coordinates=[[3.38,6.52],[3.95,7.38],[5.63,7.73],[7.49,9.06],[7.54,9.07]],
    ),
    dict(
        network_id="ng-glo1", operator="Glo (Globacom)", country_iso="NG",
        name="Glo Lagos–Port Harcourt", status="deployed", burial_type="underground",
        capacity_gbps=40, length_km=470,
        coordinates=[[3.38,6.52],[3.60,6.78],[4.50,5.80],[6.97,4.85],[7.02,4.82]],
    ),
    # Kenya backbone
    dict(
        network_id="ke-safaricom", operator="Safaricom", country_iso="KE",
        name="Safaricom Nairobi–Mombasa", status="deployed", burial_type="underground",
        capacity_gbps=40, length_km=450,
        coordinates=[[36.82,-1.29],[37.42,-1.65],[38.00,-2.40],[39.00,-3.25],[39.67,-4.05]],
    ),
    dict(
        network_id="ke-telkom", operator="Telkom Kenya", country_iso="KE",
        name="Telkom Kenya National Backbone (partial)", status="deployed", burial_type="underground",
        capacity_gbps=20, length_km=1200,
        coordinates=[[36.82,-1.29],[36.85,-0.50],[37.10,0.50],[37.65,3.12],[37.75,3.68]],
    ),
    # Tanzania backbone
    dict(
        network_id="tz-ttcl", operator="Tanzania Telecommunications (TTCL)", country_iso="TZ",
        name="TTCL National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=20, length_km=2600,
        coordinates=[[39.29,-6.82],[37.67,-3.36],[36.82,-1.29],[34.65,0.45],[32.58,0.35],[31.62,4.85]],
    ),
    # Ethiopia backbone
    dict(
        network_id="et-ethiotelecom", operator="Ethio Telecom", country_iso="ET",
        name="Ethio Telecom National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=10, length_km=2000,
        coordinates=[[38.74,9.01],[39.48,8.55],[39.93,7.47],[40.18,6.37],[41.85,4.65]],
    ),
    # South Africa backbone
    dict(
        network_id="za-openserve", operator="Openserve (Telkom SA)", country_iso="ZA",
        name="Openserve Cape Town–Johannesburg", status="deployed", burial_type="underground",
        capacity_gbps=200, length_km=1400,
        coordinates=[[18.42,-33.93],[19.90,-33.60],[22.00,-33.00],[25.57,-33.58],[28.03,-26.20]],
    ),
    dict(
        network_id="za-liquid", operator="Liquid Intelligent Technologies", country_iso="ZA",
        name="Liquid SA Johannesburg–Harare", status="deployed", burial_type="underground",
        capacity_gbps=200, length_km=890,
        coordinates=[[28.03,-26.20],[28.90,-25.00],[29.83,-23.90],[31.05,-25.97],[31.02,-17.83]],
        countries=["ZA","ZW"],
    ),
    # Uganda backbone
    dict(
        network_id="ug-nbi", operator="National Backbone Infrastructure (NBI)", country_iso="UG",
        name="Uganda NBI National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=10, length_km=2000,
        coordinates=[[32.58,0.35],[31.53,0.66],[30.65,0.61],[29.37,-0.16],[30.09,-1.10],[30.13,-4.91]],
        countries=["UG","RW"],
    ),
    # West Africa ring (partial)
    dict(
        network_id="waf-wacs-terrestrial", operator="MTN GlobalConnect", country_iso="GH",
        name="West Africa Terrestrial Corridor (partial)", status="deployed", burial_type="underground",
        capacity_gbps=100, length_km=3500,
        coordinates=[[-17.44,14.69],[-16.58,13.45],[-15.60,11.85],[-13.68,9.54],[-10.82,6.31],
                     [-8.00,5.35],[-5.35,5.27],[-1.87,5.56],[0.02,5.56],[2.37,6.37],[3.38,6.52]],
        countries=["SN","GN","GW","SL","LR","CI","GH","TG","BJ","NG"],
    ),
    # Rwanda + DRC
    dict(
        network_id="rw-rwandatel", operator="Rwanda Telecom / RURA", country_iso="RW",
        name="Rwanda National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=10, length_km=2800,
        coordinates=[[30.06,-1.94],[30.13,-4.91],[29.73,-9.46],[28.32,-14.44],[28.18,-15.42]],
        countries=["RW","BI","TZ","ZM","MZ"],
    ),
    # Cameroon
    dict(
        network_id="cm-camtel", operator="Camtel", country_iso="CM",
        name="Camtel National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=20, length_km=2100,
        coordinates=[[9.70,4.06],[11.52,3.87],[13.58,4.36],[14.47,10.46],[15.05,12.11]],
    ),
    # Egypt backbone
    dict(
        network_id="eg-telecom-egypt", operator="Telecom Egypt", country_iso="EG",
        name="Telecom Egypt National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=100, length_km=3500,
        coordinates=[[31.24,30.06],[31.40,29.90],[32.27,29.02],[32.54,27.18],[33.80,23.97],
                     [32.90,22.00],[32.53,21.52],[13.18,23.60]],
        countries=["EG","SD"],
    ),
    # Sudan backbone
    dict(
        network_id="sd-sudatel", operator="Sudatel", country_iso="SD",
        name="Sudatel National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=10, length_km=2400,
        coordinates=[[32.53,15.60],[33.00,13.50],[34.00,11.50],[35.00,9.60],[36.00,8.00],[38.74,9.01]],
        countries=["SD","ET"],
    ),
    # Morocco backbone
    dict(
        network_id="ma-maroc-telecom", operator="Maroc Telecom", country_iso="MA",
        name="Maroc Telecom National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=100, length_km=3000,
        coordinates=[[-5.00,35.77],[-5.83,35.76],[-7.62,33.59],[-8.00,31.63],
                     [-8.99,27.15],[-12.90,23.68],[-13.15,18.08],[-15.97,12.36]],
        countries=["MA","MR","SN"],
    ),
    # Algeria backbone
    dict(
        network_id="dz-algerie-telecom", operator="Algérie Télécom", country_iso="DZ",
        name="Algérie Télécom National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=40, length_km=4000,
        coordinates=[[3.07,36.75],[3.00,35.00],[2.00,33.00],[0.00,31.00],
                     [-2.00,28.00],[-5.00,25.00],[-3.00,23.00],[1.52,21.65]],
        countries=["DZ","ML","NE"],
    ),
    # DRC backbone (Liquid)
    dict(
        network_id="cd-liquid-telecom", operator="Liquid Intelligent Technologies", country_iso="CD",
        name="Liquid DRC Backbone", status="deployed", burial_type="underground",
        capacity_gbps=40, length_km=3000,
        coordinates=[[15.27,-4.32],[17.00,-5.50],[22.00,-7.00],[24.00,-8.50],
                     [26.00,-8.80],[27.47,-8.76],[28.32,-14.44],[28.29,-15.41]],
        countries=["CD","ZM"],
    ),
    # Mozambique backbone (TDM)
    dict(
        network_id="mz-tdm", operator="Telecomunicações de Moçambique (TDM)", country_iso="MZ",
        name="TDM National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=20, length_km=2500,
        coordinates=[[32.59,-25.97],[33.50,-24.50],[34.80,-22.00],[35.30,-19.00],
                     [35.56,-17.36],[35.33,-15.40],[35.00,-13.00],[35.92,-11.34]],
        countries=["MZ","ZW","ZM","TZ"],
    ),
    # Zambia backbone (Zamtel)
    dict(
        network_id="zm-zamtel", operator="Zamtel", country_iso="ZM",
        name="Zamtel National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=10, length_km=2100,
        coordinates=[[28.29,-15.41],[28.45,-14.50],[28.40,-13.00],[28.18,-12.00],
                     [27.87,-8.78],[28.22,-7.00],[29.73,-6.80],[32.58,-9.27]],
        countries=["ZM","CD","TZ"],
    ),
    # Ghana backbone (GHANA)
    dict(
        network_id="gh-vodafone-gh", operator="Vodafone Ghana", country_iso="GH",
        name="Vodafone Ghana National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=40, length_km=1400,
        coordinates=[[-0.19,5.56],[-0.18,6.69],[-1.62,7.34],[-2.10,9.40],
                     [-1.05,10.61],[0.84,10.89],[1.10,9.50]],
        countries=["GH","TG"],
    ),
    # South Africa — detailed
    dict(
        network_id="za-liquid-sa", operator="Liquid Intelligent Technologies South Africa",
        country_iso="ZA", name="Liquid SA Cape Town–Durban", status="deployed",
        burial_type="underground", capacity_gbps=200, length_km=1600,
        coordinates=[[18.42,-33.93],[19.00,-33.80],[22.00,-33.90],[24.84,-33.98],
                     [26.87,-33.01],[29.00,-29.90],[30.87,-29.87],[31.03,-29.86]],
    ),
    # Libya backbone
    dict(
        network_id="ly-lptic", operator="LPTIC (Libya)", country_iso="LY",
        name="Libya LPTIC Backbone", status="deployed", burial_type="underground",
        capacity_gbps=10, length_km=2500,
        coordinates=[[13.18,32.89],[13.50,32.40],[14.00,31.00],[15.00,30.00],
                     [18.00,29.00],[22.00,29.10],[25.00,30.00],[24.92,30.97]],
    ),
    # Tunisia backbone
    dict(
        network_id="tn-tunisie-telecom", operator="Tunisie Télécom", country_iso="TN",
        name="Tunisie Télécom National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=40, length_km=1200,
        coordinates=[[10.17,36.82],[9.56,35.83],[9.20,34.74],[8.70,33.88],
                     [8.80,32.00],[9.50,30.26],[10.80,29.10]],
    ),
    # Zimbabwe — Liquid
    dict(
        network_id="zw-liquid", operator="Liquid Intelligent Technologies Zimbabwe",
        country_iso="ZW", name="Liquid Zimbabwe National Backbone", status="deployed",
        burial_type="underground", capacity_gbps=100, length_km=1200,
        coordinates=[[31.02,-17.83],[31.50,-18.00],[31.60,-19.50],[32.67,-20.15],
                     [28.58,-20.13],[27.00,-20.07],[26.00,-20.52],[25.85,-18.01]],
    ),
    # Botswana backbone
    dict(
        network_id="bw-bofinet", operator="BoFiNet Botswana", country_iso="BW",
        name="BoFiNet National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=10, length_km=1800,
        coordinates=[[25.91,-24.65],[25.00,-23.00],[24.65,-21.00],[24.00,-20.00],
                     [25.85,-18.01],[27.00,-20.07],[26.37,-20.50]],
    ),
    # Namibia backbone (Paratus)
    dict(
        network_id="na-paratus", operator="Paratus Namibia", country_iso="NA",
        name="Paratus Namibia Backbone", status="deployed", burial_type="underground",
        capacity_gbps=20, length_km=2500,
        coordinates=[[17.08,-22.56],[17.00,-22.00],[18.50,-20.50],[19.00,-19.00],
                     [20.00,-18.30],[21.00,-18.00],[22.00,-18.00],[23.00,-17.90],
                     [24.27,-17.90],[25.00,-17.80],[25.85,-18.01]],
        countries=["NA","BW","ZM"],
    ),
    # Angola backbone
    dict(
        network_id="ao-angola-telecom", operator="Angola Telecom", country_iso="AO",
        name="Angola Telecom National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=10, length_km=3000,
        coordinates=[[13.23,-8.84],[14.00,-10.00],[15.00,-11.00],[16.00,-12.00],
                     [17.00,-12.50],[17.86,-12.37],[18.50,-13.00],[19.00,-13.50],
                     [19.92,-13.41],[20.00,-14.00],[21.50,-15.00],[22.00,-16.50],
                     [22.00,-17.50],[18.00,-17.50],[16.00,-15.00],[14.00,-12.00]],
    ),
    # Senegal backbone
    dict(
        network_id="sn-sonatel", operator="Sonatel", country_iso="SN",
        name="Sonatel National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=40, length_km=1500,
        coordinates=[[-17.44,14.69],[-17.00,15.00],[-16.50,14.20],[-15.50,13.50],
                     [-14.50,12.90],[-13.50,12.50],[-12.00,12.70],[-10.00,13.50],
                     [-9.00,14.50],[-8.00,14.00]],
        countries=["SN","GM","GN","ML"],
    ),
    # Guinea / Sierra Leone / Liberia
    dict(
        network_id="gn-orange-gn", operator="Orange Guinea", country_iso="GN",
        name="Orange Guinea–Sierra Leone–Liberia Corridor", status="deployed",
        burial_type="underground", capacity_gbps=10, length_km=1500,
        coordinates=[[-13.68,9.54],[-13.00,10.00],[-12.00,10.50],[-11.00,10.00],
                     [-10.50,9.00],[-10.82,6.31],[-10.60,5.80],[-8.70,4.40]],
        countries=["GN","SL","LR"],
    ),
    # North Africa coastal route
    dict(
        network_id="waf-north-coastal", operator="Various (North Africa Coastal)",
        country_iso="TN", name="North Africa Mediterranean Coastal Route",
        status="deployed", burial_type="underground", capacity_gbps=40, length_km=4000,
        coordinates=[[10.17,36.82],[8.50,37.00],[5.00,36.50],[3.07,36.75],
                     [0.00,36.60],[-2.00,35.50],[-5.00,35.77]],
        countries=["TN","DZ","MA"],
    ),
    # East Africa coastal (SEACOM terrestrial)
    dict(
        network_id="eaf-seacom-terrestrial", operator="SEACOM", country_iso="KE",
        name="SEACOM East Africa Terrestrial", status="deployed", burial_type="underground",
        capacity_gbps=100, length_km=2000,
        coordinates=[[39.67,-4.05],[37.67,-3.36],[36.82,-1.29],[35.00,0.50],
                     [33.00,1.00],[32.58,0.35],[32.58,-1.10],[31.62,4.85]],
        countries=["KE","TZ","UG","SS"],
    ),
    # Niger backbone
    dict(
        network_id="ne-niger-telecom", operator="Niger Télécoms", country_iso="NE",
        name="Niger Télécoms National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=10, length_km=2200,
        coordinates=[[2.12,13.51],[3.00,14.00],[4.00,13.50],[6.00,13.30],
                     [7.99,13.50],[8.99,13.29],[10.00,13.00],[13.32,13.31],
                     [14.89,13.10],[14.50,15.00],[13.50,15.50],[13.18,23.60]],
    ),
    # Mali backbone
    dict(
        network_id="ml-sotelma", operator="Sotelma / Orange Mali", country_iso="ML",
        name="Sotelma Mali National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=10, length_km=2500,
        coordinates=[[-7.99,12.65],[-8.00,13.00],[-6.00,14.00],[-4.00,15.00],
                     [-2.00,16.00],[0.00,17.00],[1.52,21.65]],
        countries=["ML","MR","DZ"],
    ),
    # Burundi backbone
    dict(
        network_id="bi-onatel-bi", operator="ONATEL Burundi", country_iso="BI",
        name="ONATEL Burundi National Backbone", status="deployed", burial_type="underground",
        capacity_gbps=10, length_km=800,
        coordinates=[[29.36,-3.38],[30.00,-3.00],[30.06,-1.94],[29.73,-3.38],
                     [29.50,-4.00],[30.13,-4.91]],
        countries=["BI","RW"],
    ),
]

SEED_NODES = [
    # IXPs
    dict(name="KINIX", name_short="KINIX", city="Kinshasa", country_iso="CD", node_type="ixp",
         lon=15.27, lat=-4.32, operator="KINIX"),
    dict(name="IXPN Lagos", name_short="IXPN", city="Lagos", country_iso="NG", node_type="ixp",
         lon=3.38, lat=6.45, operator="IXPN"),
    dict(name="KIXP Nairobi", name_short="KIXP", city="Nairobi", country_iso="KE", node_type="ixp",
         lon=36.82, lat=-1.29, operator="TESPOK"),
    dict(name="JINX Johannesburg", name_short="JINX", city="Johannesburg", country_iso="ZA",
         node_type="ixp", lon=28.03, lat=-26.20, operator="Teraco"),
    dict(name="AMSIX Dar es Salaam", name_short="AMSIX-DAR", city="Dar es Salaam", country_iso="TZ",
         node_type="ixp", lon=39.29, lat=-6.82, operator="AMSIX Tanzania"),
    dict(name="UIXP Kampala", name_short="UIXP", city="Kampala", country_iso="UG",
         node_type="ixp", lon=32.58, lat=0.35, operator="UIXP"),
    dict(name="RWIX Kigali", name_short="RWIX", city="Kigali", country_iso="RW",
         node_type="ixp", lon=30.06, lat=-1.94, operator="RURA"),
    dict(name="GHIX Accra", name_short="GHIX", city="Accra", country_iso="GH",
         node_type="ixp", lon=-0.19, lat=5.56, operator="GHIX"),
    dict(name="DECIX Nairobi", name_short="DECIX-NBO", city="Nairobi", country_iso="KE",
         node_type="ixp", lon=36.83, lat=-1.30, operator="DE-CIX"),
    # Landing stations (terrestrial anchor points)
    dict(name="SEACOM Mombasa Landing Station", name_short="SEACOM Mombasa",
         city="Mombasa", country_iso="KE", node_type="landing-station",
         lon=39.67, lat=-4.05, operator="SEACOM"),
    dict(name="EASSy Mombasa Landing Station", name_short="EASSy Mombasa",
         city="Mombasa", country_iso="KE", node_type="landing-station",
         lon=39.68, lat=-4.04, operator="EASSy Consortium"),
    dict(name="WACS Cape Town Landing Station", name_short="WACS CPT",
         city="Cape Town", country_iso="ZA", node_type="landing-station",
         lon=18.42, lat=-33.93, operator="MTN"),
    dict(name="MainOne Lagos Landing Station", name_short="MainOne LGS",
         city="Lagos", country_iso="NG", node_type="landing-station",
         lon=3.38, lat=6.42, operator="MainOne"),
    dict(name="ACE Dakar Landing Station", name_short="ACE Dakar",
         city="Dakar", country_iso="SN", node_type="landing-station",
         lon=-17.44, lat=14.69, operator="Orange"),
    # Data centres
    dict(name="Teraco JB1 Johannesburg", name_short="Teraco JB1",
         city="Johannesburg", country_iso="ZA", node_type="data-center",
         lon=28.13, lat=-26.18, operator="Teraco Data Environments"),
    dict(name="Africa Data Centres Nairobi", name_short="ADC Nairobi",
         city="Nairobi", country_iso="KE", node_type="data-center",
         lon=36.83, lat=-1.27, operator="Africa Data Centres"),
    dict(name="MDXi Lagos", name_short="MDXi Lagos",
         city="Lagos", country_iso="NG", node_type="data-center",
         lon=3.39, lat=6.60, operator="MainOne (MDXi)"),
]


# ---------------------------------------------------------------------------
# Live API fetch
# ---------------------------------------------------------------------------

def _try_fetch_geojson(urls: list[str], cache_name: str, refresh: bool) -> Optional[dict]:
    if not refresh and is_cached(cache_name, max_age_hours=48):
        return json.loads(read_cache(cache_name))

    for url in urls:
        try:
            print(f"  Trying {url} ...")
            data = get_json(url, timeout=20)
            if data and (data.get("type") == "FeatureCollection" or data.get("features")):
                write_cache(cache_name, json.dumps(data).encode())
                print(f"  Success: {len(data.get('features', []))} features")
                return data
        except Exception as e:
            print(f"    WARN: {url} → {e}")

    print(f"  INFO: AfTerFibre live API unreachable — will use seed data")
    return None


# ---------------------------------------------------------------------------
# Live feature converters
# ---------------------------------------------------------------------------

def _live_span_to_ofm(feat: dict, seq: int) -> Optional[dict]:
    props = feat.get("properties") or {}
    geom  = feat.get("geometry") or {}
    geom_type = geom.get("type", "")
    if geom_type not in ("LineString", "MultiLineString"):
        return None
    coords = geom.get("coordinates")
    if not coords:
        return None

    operator    = props.get("operator") or props.get("network") or props.get("name") or "Unknown"
    country_iso = (props.get("country") or props.get("country_iso") or "").upper() or None
    status_raw  = (props.get("status") or "").lower()
    status      = STATUS_MAP.get(status_raw, "unknown")
    capacity    = props.get("capacity_gbps") or props.get("capacity") or None
    if capacity:
        try:
            capacity = float(capacity)
        except (TypeError, ValueError):
            capacity = None

    network_id = f"{(country_iso or 'xx').lower()}-{slugify(operator)}"

    return span_feature(
        span_id=make_span_id(network_id, seq),
        network_id=network_id,
        name=props.get("name") or None,
        operator=operator,
        coordinates=coords,
        country_iso=country_iso,
        region=region_from_iso(country_iso or ""),
        status=status,
        burial_type="underground",
        capacity_gbps=capacity,
        source=SOURCE,
        source_url="https://afterfibre.nsrc.org",
        license=LICENSE,
        attribution=ATTRIBUTION,
    )


def _live_node_to_ofm(feat: dict, seq: int) -> Optional[dict]:
    props = feat.get("properties") or {}
    geom  = feat.get("geometry") or {}
    if geom.get("type") != "Point":
        return None
    coords = geom.get("coordinates") or []
    if len(coords) < 2:
        return None

    lon, lat = float(coords[0]), float(coords[1])
    name     = props.get("name") or f"Node {seq}"
    operator = props.get("operator") or props.get("network") or name
    country_iso = (props.get("country") or "").upper() or None

    node_type_raw = (props.get("type") or "").lower()
    node_type = {
        "ixp": "ixp", "pop": "pop", "landing": "landing-station",
        "landing station": "landing-station", "data centre": "data-center",
        "data center": "data-center",
    }.get(node_type_raw, "pop")

    slug = slugify(name[:40])
    node_id = make_node_id(node_type, country_iso or "xx", slug, seq)
    network_id = f"{(country_iso or 'xx').lower()}-{slugify(operator)}"

    return node_feature(
        node_id=node_id, network_id=network_id,
        name=name, operator=operator, node_type=node_type,
        lon=lon, lat=lat, country_iso=country_iso,
        region=region_from_iso(country_iso or ""),
        source=SOURCE, source_url="https://afterfibre.nsrc.org",
        license=LICENSE, attribution=ATTRIBUTION,
    )


# ---------------------------------------------------------------------------
# Seed data builders
# ---------------------------------------------------------------------------

def _build_seed_spans() -> list[dict]:
    features = []
    for i, s in enumerate(SEED_SPANS, start=1):
        coords = s.pop("coordinates")
        countries = s.pop("countries", None)
        feat = span_feature(
            span_id=make_span_id(s["network_id"], i),
            coordinates=coords,
            countries=countries,
            source=SOURCE,
            source_url="https://afterfibre.nsrc.org",
            license=LICENSE,
            attribution=ATTRIBUTION,
            notes="Approximate alignment from public AfTerFibre map. Not authoritative.",
            region=region_from_iso(s.get("country_iso", "")),
            **s,
        )
        features.append(feat)
    return features


def _build_seed_nodes() -> list[dict]:
    features = []
    seq_map: dict[str, int] = {}
    for nd in SEED_NODES:
        slug = slugify(nd["name"][:40])
        seq  = seq_map.get(slug, 1)
        seq_map[slug] = seq + 1
        feat = node_feature(
            node_id=make_node_id(nd["node_type"], nd["country_iso"], slug, seq),
            network_id=f"{nd['country_iso'].lower()}-{slugify(nd['operator'])}",
            name=nd["name"],
            name_short=nd.get("name_short"),
            operator=nd["operator"],
            node_type=nd["node_type"],
            lon=nd["lon"],
            lat=nd["lat"],
            city=nd.get("city"),
            country_iso=nd["country_iso"],
            region=region_from_iso(nd["country_iso"]),
            source=SOURCE,
            source_url="https://afterfibre.nsrc.org",
            license=LICENSE,
            attribution=ATTRIBUTION,
            notes="Curated from public AfTerFibre map. Coordinates approximate.",
        )
        features.append(feat)
    return features


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def fetch(refresh: bool = False, offline: bool = False) -> dict[str, dict]:
    print("\n=== AfTerFibre fetcher ===")

    span_features: list[dict] = []
    node_features: list[dict] = []

    if not offline:
        # Try live API
        spans_fc = _try_fetch_geojson(SPANS_URLS, "afterfibre_spans.json", refresh)
        nodes_fc = _try_fetch_geojson(NODES_URLS, "afterfibre_nodes.json", refresh)

        if spans_fc:
            for i, feat in enumerate(spans_fc.get("features", []), 1):
                ofm = _live_span_to_ofm(feat, i)
                if ofm:
                    span_features.append(ofm)
            print(f"  Live spans converted: {len(span_features)}")

        if nodes_fc:
            for i, feat in enumerate(nodes_fc.get("features", []), 1):
                ofm = _live_node_to_ofm(feat, i)
                if ofm:
                    node_features.append(ofm)
            print(f"  Live nodes converted: {len(node_features)}")

    # Supplement with seed data (always include seed if live returned < 5 features)
    if len(span_features) < 5:
        seed_spans = _build_seed_spans()
        print(f"  Adding {len(seed_spans)} seed spans (live API unavailable or insufficient)")
        span_features.extend(seed_spans)

    if len(node_features) < 5:
        seed_nodes = _build_seed_nodes()
        print(f"  Adding {len(seed_nodes)} seed nodes")
        node_features.extend(seed_nodes)

    results: dict[str, dict] = {}

    spans_fc = feature_collection(
        span_features,
        name="OpenFiberMap-Spans-AfTerFibre-Africa",
        description="Africa terrestrial fiber backbone spans from AfTerFibre / NSRC",
        license=LICENSE, attribution=ATTRIBUTION, source=SOURCE,
    )
    out_spans = PUBLIC_DATA / "spans-afterfibre-africa.geojson"
    save_geojson(spans_fc, out_spans)
    results["spans-afterfibre-africa.geojson"] = spans_fc

    nodes_fc = feature_collection(
        node_features,
        name="OpenFiberMap-Nodes-AfTerFibre-Africa",
        description="Africa fiber network nodes (IXPs, POPs, landing stations) from AfTerFibre / NSRC",
        license=LICENSE, attribution=ATTRIBUTION, source=SOURCE,
    )
    out_nodes = PUBLIC_DATA / "nodes-afterfibre-africa.geojson"
    save_geojson(nodes_fc, out_nodes)
    results["nodes-afterfibre-africa.geojson"] = nodes_fc

    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch AfTerFibre Africa backbone data")
    parser.add_argument("--refresh", action="store_true", help="Force re-download ignoring cache")
    parser.add_argument("--offline", action="store_true", help="Skip live API, use seed data only")
    args = parser.parse_args()
    fetch(refresh=args.refresh, offline=args.offline)


if __name__ == "__main__":
    main()
