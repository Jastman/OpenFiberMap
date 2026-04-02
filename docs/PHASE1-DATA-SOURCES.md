# Phase 1 — Data Sources Inventory

_OpenFiberMap collects only publicly available, openly licensed data. Every source is credited per-feature via `source_url` and `license` properties._

---

## Table of Contents

1. [Primary Sources — OFDS-Compliant](#1-primary-sources--ofds-compliant)
2. [Africa — AfTerFibre & Regional](#2-africa--afterfibre--regional)
3. [Americas — Brazil, US](#3-americas--brazil-us)
4. [OpenStreetMap Extracts](#4-openstreetmap-extracts)
5. [IXPs & Nodes — PeeringDB](#5-ixps--nodes--peeringdb)
6. [Regulatory / Government Sources](#6-regulatory--government-sources)
7. [Research & Academic](#7-research--academic)
8. [Reference-Only (No Scraping)](#8-reference-only-no-scraping)
9. [Priority Matrix](#9-priority-matrix)

---

## 1. Primary Sources — OFDS-Compliant

### 1.1 OFDS Datasets (stevesong/OFDS-datasets)

| Field | Value |
|-------|-------|
| URL | https://github.com/stevesong/OFDS-datasets |
| Demo | https://stevesong.github.io/OFDS-datasets/ |
| Format | GeoJSON → PMTiles |
| License | Varies per dataset (repo is testing/non-authoritative) |
| Coverage | Africa (20+ countries), Brazil, Canada, Costa Rica, Georgia, New Zealand, Nicaragua, Panama, Venezuela |
| Priority | **HIGH** — best single aggregation of OFDS-format data |

**Countries with confirmed data in the repo:**
- Africa: Angola, Botswana, Burundi, Cameroon, DRC, Kenya, Mozambique, Namibia, Niger, Nigeria, Rwanda, South Africa, Sudan, Tanzania, Togo, Uganda, Zambia, Zimbabwe
- Americas: Brazil, Canada, Costa Rica, Nicaragua, Panama, Venezuela
- Other: Georgia, New Zealand

**Notes:**
- Files are organized as `/{country}/{operator}/nodes.geojson` and `/{country}/{operator}/spans.geojson`
- Must check individual dataset licenses before including
- Tippecanoe + PMTiles pipeline already exists — can reuse for our tiling layer

### 1.2 OFDS CoVE Validator

| Field | Value |
|-------|-------|
| URL | https://ofds.cove.opendataservices.coop/ |
| Purpose | Validate our output GeoJSON against OFDS specification |
| Standard | Open Fibre Data Standard v1.0 |
| Usage | Run ETL output through CoVE to catch schema errors |

### 1.3 OFDS Official Specification

| Field | Value |
|-------|-------|
| URL | https://open-fibre-data-standard.readthedocs.io/en/latest/ |
| Schema | https://github.com/Open-Fibre-Data-Standard/open-fibre-data-standard |
| License | Apache 2.0 |
| Format | JSON Schema + documentation |

**Key OFDS concepts used in our schema:**
- `PhaseCollection` → we use `FeatureCollection` with `layer` property
- `Span` → LineString with required: id, name, phase, physicalInfrastructureProvider
- `Node` → Point with required: id, name, phase, type
- Status codelist: `[deployed, ready for service, lit, under construction, planning]`
- Physical infrastructure types: `[Aerial, Underground, Subsea, Unknown]`

---

## 2. Africa — AfTerFibre & Regional

### 2.1 AfTerFibre (NSRC)

| Field | Value |
|-------|-------|
| URL | https://afterfibre.nsrc.org |
| Maintainer | Network Startup Resource Center (NSRC) |
| Format | Interactive map; underlying data extractable as GeoJSON/KML |
| License | CC-BY (attribution required) |
| Coverage | Pan-African terrestrial fiber — comprehensive for backbone routes |
| Priority | **HIGH** — most authoritative Africa backbone dataset |

**Known operators covered:**
- Liquid Telecom / Liquid Intelligent Technologies
- MTN, Vodacom, Airtel backbone routes
- WIOCC, SEACOM terrestrial backhaul
- NAPAfrica, RINX interconnects
- Government backbone networks (e.g., National ICT Company routes)

**Extraction approach:**
- AfTerFibre exposes data via a public-facing API endpoint and GeoJSON layers
- Primary endpoint: `https://afterfibre.nsrc.org/api/` (verify current path)
- Alternative: Download KMZ exports from the interactive map

### 2.2 Alliance for Affordable Internet (A4AI) / Web Foundation Data

| Field | Value |
|-------|-------|
| URL | https://a4ai.org/research/ |
| Coverage | Africa, Asia-Pacific policy data |
| Format | Reports + CSV; limited GeoJSON |
| Priority | LOW — policy data, useful for context only |

### 2.3 Internet Society (ISOC) IXP Map

| Field | Value |
|-------|-------|
| URL | https://www.internetsociety.org/ixps/ |
| Coverage | IXP locations in Africa and developing regions |
| Format | HTML table / export |
| Priority | **MEDIUM** — IXP node locations useful for our nodes layer |

### 2.4 African Union / AfDB Infrastructure Data

| Field | Value |
|-------|-------|
| URL | https://www.afdb.org/en/topics-and-sectors/topics/infrastructure |
| Coverage | Funded backbone projects |
| Format | Project documents (PDF), some GeoJSON via IATI |
| Priority | MEDIUM — covers planned/under-construction routes |

---

## 3. Americas — Brazil, US

### 3.1 Brazil — ANATEL / MCTIC Open Data

| Field | Value |
|-------|-------|
| URL | https://dados.gov.br/dataset?groups=telecomunicacoes |
| Maintainer | ANATEL (Brazilian telecom regulator) |
| Format | SHP, CSV, GeoJSON |
| License | CC-BY (Brazilian Open Government Data License) |
| Coverage | Brazil national fiber routes, backhaul, licensed operators |
| Priority | **HIGH** — official regulator data, OFDS pilots done in Brazil |

**Known datasets:**
- `ANATEL Infraestrutura de Rede` — fiber infrastructure by operator
- RNP (Rede Nacional de Pesquisa) backbone — academic/research network
- GESAC program routes

### 3.2 Brazil — RNP (National Research Network)

| Field | Value |
|-------|-------|
| URL | https://www.rnp.br/en/network/infrastructure |
| License | CC-BY |
| Coverage | Academic fiber backbone across all Brazilian states |
| Priority | **HIGH** — clean, verified, publicly documented routes |

### 3.3 United States — FCC Broadband Data Collection (BDC)

| Field | Value |
|-------|-------|
| URL | https://broadbandmap.fcc.gov/home |
| API | https://broadbandmap.fcc.gov/location/availability |
| Format | CSV, GeoJSON (availability by location, NOT routes) |
| License | Public domain |
| Priority | **MEDIUM** — gives served/unserved coverage; NOT route-level data |
| Limitation | BDC does not include actual fiber route geometries |

### 3.4 United States — FCC Form 477 (Historical) + Infrastructure Maps

| Field | Value |
|-------|-------|
| URL | https://www.fcc.gov/general/broadband-deployment-data-fcc-form-477 |
| Format | CSV (no route geometries) |
| Priority | LOW — census-block coverage only, no line routes |

### 3.5 United States — Internet2 / ESnet Academic Backbone

| Field | Value |
|-------|-------|
| URL | https://www.internet2.edu/network/ |
| ESnet | https://www.es.net/network/ |
| Format | Interactive maps; GeoJSON available via API in some cases |
| License | Publicly documented; contact for data reuse |
| Priority | **MEDIUM** — clean US backbone routes for research network overlay |

### 3.6 United States — State Broadband Offices (NTIA BEAD)

| Field | Value |
|-------|-------|
| URL | https://broadbandusa.ntia.gov/programs-and-data |
| Format | Varies by state; many publish GeoJSON/SHP via state GIS portals |
| License | Public domain (federal); varies by state |
| Priority | MEDIUM — BEAD-funded fiber deployment maps coming 2025-2027 |

---

## 4. OpenStreetMap Extracts

### 4.1 OSM Telecom Infrastructure Tags

| Field | Value |
|-------|-------|
| URL | https://www.openstreetmap.org |
| Overpass API | https://overpass-api.de |
| License | ODbL 1.0 |
| Priority | **HIGH** — global coverage, community-maintained |

**Key OSM query tags for fiber:**
```
telecom=cable                    # Fiber optic cable/duct routes
telecom=exchange                 # Telecom exchange / POP
telecom=data_center              # Data centers
telecom=service_device           # Amplifiers, repeaters
man_made=pipeline + content=fiber  # Alternative tagging
highway=* + telecom=yes          # Roads with fiber ducts
```

**Overpass query for fiber routes:**
```overpass
[out:json][timeout:300];
(
  way["telecom"="cable"]["telecom:medium"="fiber"];
  way["telecom"="cable"]["cable:type"="fiber"];
  relation["telecom"="cable"];
);
out geom;
```

**Tools:**
- Overpass Turbo: https://overpass-turbo.eu
- Geofabrik extracts: https://download.geofabrik.de (pre-filtered .osm.pbf)
- osmium-tool for filtering PBF by tag

**Limitations:**
- OSM fiber tagging is sparse; coverage highly varies by country
- Best in dense urban areas and some African/Asian corridors
- Operators rarely tag capacity or ownership accurately

---

## 5. IXPs & Nodes — PeeringDB

### 5.1 PeeringDB

| Field | Value |
|-------|-------|
| URL | https://www.peeringdb.com |
| API | https://www.peeringdb.com/api/ |
| Format | JSON REST API |
| License | CC0 (public domain) |
| Priority | **HIGH** — authoritative global IXP and data center locations |

**Key API endpoints:**
```
GET /api/ix          → Internet Exchanges (IXPs)
GET /api/fac         → Facilities (data centers, carrier hotels)
GET /api/net         → Networks (ASNs) + their facilities
GET /api/ixlan       → IXP LAN details
GET /api/poc         → Points of Contact
```

**Fields for our nodes layer:**
- `name`, `name_long`, `city`, `country`, `latitude`, `longitude`
- `aka` (also known as), `website`, `notes`
- `tech_email`, `org` (organization)

**Rate limiting:** 100 req/min unauthenticated; 1000/min with API key (free)

### 5.2 Packet Clearing House (PCH) IXP Directory

| Field | Value |
|-------|-------|
| URL | https://www.pch.net/ixp/dir |
| Format | CSV / HTML |
| License | CC-BY |
| Priority | MEDIUM — supplements PeeringDB, especially for smaller regional IXPs |

---

## 6. Regulatory / Government Sources

### 6.1 European Union — BEREC / GÉANT

| Field | Value |
|-------|-------|
| GÉANT | https://www.geant.org/Networks/Pan-European_Research_Network |
| Format | Published maps and route data; GeoJSON on request |
| License | CC-BY |
| Coverage | Pan-European research & education network backbone |
| Priority | **MEDIUM** — high-quality European backbone |

### 6.2 EU Open Data Portal

| Field | Value |
|-------|-------|
| URL | https://data.europa.eu/en |
| Coverage | EU member state broadband/NGA maps |
| Format | SHP, GeoJSON via national portals |
| Priority | MEDIUM — varies heavily by country |

### 6.3 ITU Broadband Infrastructure Data

| Field | Value |
|-------|-------|
| URL | https://www.itu.int/en/ITU-D/Statistics/Pages/broadband/default.aspx |
| Format | Reports, limited open GIS data |
| License | ITU open data policy (CC-BY for statistics) |
| Priority | LOW — statistical, not geometric |

### 6.4 World Bank / IFC Infrastructure Projects

| Field | Value |
|-------|-------|
| URL | https://projects.worldbank.org/en/projects-operations/projects-list?os=0&lang=en&searchQuery=fiber |
| IATI | https://www.iatiregistry.org |
| Format | IATI XML (geocoded project locations) |
| License | CC-BY |
| Priority | **MEDIUM** — funded projects (Africa, Asia) often include route data |

---

## 7. Research & Academic

### 7.1 CAIDA Internet Infrastructure Data

| Field | Value |
|-------|-------|
| URL | https://www.caida.org/catalog/datasets/ |
| Coverage | Global internet topology inferred from traceroutes |
| License | CAIDA Dataset License (free for research) |
| Format | JSON, CSV |
| Priority | LOW — IP topology, not physical routes |

### 7.2 Submarine Cable Map (TeleGeography)

| Field | Value |
|-------|-------|
| URL | https://www.submarinecablemap.com |
| API | https://www.submarinecablemap.com/api/v3/ |
| License | CC-BY-SA |
| Coverage | Global submarine cables + landing stations |
| Priority | **HIGH for nodes layer** — landing stations are critical fiber endpoints |

**Note:** We use landing station Point locations only (nodes layer), not submarine cable routes.

### 7.3 Speedchecker / M-Lab Network Infrastructure

| Field | Value |
|-------|-------|
| URL | https://www.measurementlab.net/data/ |
| License | CC0 |
| Priority | LOW — measurement data, not infrastructure geometry |

---

## 8. Reference-Only (No Scraping)

These sources are excellent references but **must not be scraped** — use them only to verify alignment or as design inspiration:

| Source | URL | Reason |
|--------|-----|--------|
| Infrapedia | https://infrapedia.com | Requires signup/license; proprietary aggregation |
| TeleGeography GIS | https://www.telegeography.com/products/telegeography-gis/ | Commercial product |
| Kentik | https://www.kentik.com | Commercial network intelligence |
| Cable.co.uk maps | https://cable.co.uk | Terms disallow scraping |
| Operator coverage maps | Various | Interactive JS maps without data APIs |

---

## 9. Priority Matrix

| Source | Region | Type | License | Data Quality | ETL Effort | Priority |
|--------|--------|------|---------|-------------|------------|----------|
| stevesong/OFDS-datasets | Global | Spans + Nodes | Mixed | High | Low | **P1** |
| AfTerFibre (NSRC) | Africa | Spans + Nodes | CC-BY | Very High | Low | **P1** |
| PeeringDB API | Global | Nodes (IXP/DC) | CC0 | Very High | Low | **P1** |
| Brazil ANATEL | Brazil | Spans | CC-BY | High | Medium | **P1** |
| Brazil RNP | Brazil | Spans | CC-BY | High | Low | **P1** |
| Submarine Cable Map | Global | Nodes (landing) | CC-BY-SA | Very High | Low | **P1** |
| OSM Overpass | Global | Spans + Nodes | ODbL | Medium | Medium | **P2** |
| GÉANT | Europe | Spans | CC-BY | High | Medium | **P2** |
| Internet2 / ESnet | USA | Spans | Public | High | Medium | **P2** |
| PCH IXP Directory | Global | Nodes | CC-BY | Medium | Low | **P2** |
| World Bank IATI | Global | Project locs | CC-BY | Medium | High | **P3** |
| NTIA BEAD state maps | USA | Spans | Varies | Medium | High | **P3** |
| ISOC IXP map | Africa | Nodes | Varies | Medium | Medium | **P3** |
| ITU Statistics | Global | Stats only | CC-BY | Low | Low | **P4** |
| CAIDA | Global | IP topology | Research | Low | High | **P4** |

**Execution order for Phase 2 ETL:**
1. PeeringDB → global IXP/DC nodes (fast, clean API, CC0)
2. stevesong/OFDS-datasets → Africa + Americas fiber spans
3. Submarine Cable Map API → global landing station nodes
4. AfTerFibre → Africa backbone verification + gap-fill
5. Brazil RNP + ANATEL → South America spans
6. OSM Overpass → global gap-fill where OSM coverage exists

---

_Last updated: 2026-04-02_  
_Maintained by OpenFiberMap contributors. Submit corrections via GitHub Issues._
