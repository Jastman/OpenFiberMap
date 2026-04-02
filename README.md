# OpenFiberMap

**A free, open-source interactive 3D global map of terrestrial fiber optic networks and telecom backhaul infrastructure.**

> Inspired by [OpenGridWorks](https://opengridworks.com) for electricity grids — but for fiber.

[![Build & Deploy](https://github.com/jastman/OpenFiberMap/actions/workflows/deploy.yml/badge.svg)](https://github.com/jastman/OpenFiberMap/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Schema: OFDS-aligned](https://img.shields.io/badge/Schema-OFDS--aligned-blue)](schema/fiber-schema.json)

---

## Live Demo

**[openfibermap.github.io/OpenFiberMap](https://jastman.github.io/OpenFiberMap)** *(deployed via GitHub Pages)*

---

## What is OpenFiberMap?

OpenFiberMap visualizes the world's fiber optic backbone infrastructure on a CesiumJS 3D globe:

- **Fiber spans** — routes with operator, capacity, status, burial type, length
- **Network nodes** — IXPs, data centers, PoPs, submarine cable landing stations, amplifiers
- **Filters** — by region, operator, status, capacity class
- **Search** — by operator name, city, or lat/lon coordinates
- **Share view** — copy a URL encoding current filters + camera position
- **Timeline** — filter planned/under-construction builds by year range
- **Info panel** — full metadata + source links + PeeringDB integration
- **Underground mode** — translucent terrain to see buried cable routes
- **3D / 2D toggle** — switch between globe and flat map views

---

## Quick Start

### Prerequisites
- Node.js ≥ 20
- Python ≥ 3.10 (for ETL only)

### 1. Clone and install

```bash
git clone https://github.com/jastman/OpenFiberMap.git
cd OpenFiberMap
npm install
pip install -r requirements.txt
```

### 2. Configure (optional)

```bash
cp .env.local.example .env.local
# Edit .env.local to add your Cesium ion token (free at https://ion.cesium.com)
# The app works without a token — it uses OSM imagery + flat terrain.
```

### 3. Run ETL pipeline

```bash
# Offline (uses curated seed data — fast, no network required):
bash scripts/run_etl.sh --offline

# Online (fetches live data from PeeringDB, Submarine Cable Map, etc.):
bash scripts/run_etl.sh
```

### 4. Start dev server

```bash
npm run dev
# → http://localhost:5173
```

---

## Deployment

### GitHub Pages (recommended — free)

1. Fork this repo
2. Go to **Settings → Pages → Source**: set to **GitHub Actions**
3. Optionally set `CESIUM_ION_TOKEN` in **Settings → Secrets → Actions**
4. Push to `main` — the workflow automatically builds and deploys

The workflow runs ETL (offline mode) → Vite build → deploy to Pages.

### Vercel

```bash
npm install -g vercel
vercel --prod
# Set VITE_CESIUM_ION_TOKEN in Vercel dashboard → Project Settings → Environment Variables
# Or: vercel env add VITE_CESIUM_ION_TOKEN
```

`vercel.json` is pre-configured with correct SPA rewrites and GeoJSON cache headers.

### Docker / Self-hosted

```bash
npm run build
# Serve the dist/ directory with any static file server:
npx serve dist/
# or: nginx pointing root to dist/
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Globe | [CesiumJS](https://cesium.com/cesiumjs/) 1.115 |
| Frontend | [Vite](https://vitejs.dev) 5 + [React](https://react.dev) 18 + TypeScript 5 |
| Styling | [Tailwind CSS](https://tailwindcss.com) 3 |
| ETL | Python 3 (requests, jsonschema) |
| Data format | GeoJSON (OFDS-aligned) + CZML |
| Deployment | GitHub Pages / Vercel |

---

## Project Structure

```
OpenFiberMap/
├── public/data/             Static GeoJSON + CZML served at /data/
│   ├── fiber-global.geojson All merged features
│   ├── spans-*.geojson      Per-source span files
│   ├── nodes-*.geojson      Per-source node files
│   ├── fiber-*.czml         Cesium CZML (generated from GeoJSON)
│   └── metadata.json        Dataset statistics
├── data/
│   ├── samples/             Reference sample GeoJSON
│   └── raw/                 ETL download cache (gitignored)
├── schema/
│   ├── fiber-schema.json    JSON Schema (Draft 2020-12)
│   └── README.md            Schema documentation
├── scripts/
│   ├── etl/                 Python ETL fetchers
│   │   ├── fetch_peeringdb.py
│   │   ├── fetch_ofds_datasets.py
│   │   ├── fetch_submarine_cables.py
│   │   ├── fetch_afterfibre.py
│   │   ├── fetch_brazil_rnp.py
│   │   ├── fetch_osm.py
│   │   ├── merge.py
│   │   └── generate_czml.py
│   ├── run_etl.sh           Master pipeline script
│   └── validate_schema.py   Schema validator CLI
├── src/
│   ├── components/          React UI components
│   ├── hooks/               Custom React hooks
│   ├── lib/                 Cesium styling + data loading
│   └── types/               TypeScript types
├── docs/
│   ├── PHASE1-DATA-SOURCES.md
│   └── CONTRIBUTING.md
└── .github/workflows/       CI/CD (deploy + validate)
```

---

## Data Sources

All data comes from public, openly licensed sources. Every GeoJSON feature carries `source`, `source_url`, `license`, and `attribution` properties.

| Source | Region | License | Type |
|--------|--------|---------|------|
| [AfTerFibre (NSRC)](https://afterfibre.nsrc.org) | Africa | CC-BY-4.0 | Spans + Nodes |
| [OFDS-datasets (stevesong)](https://github.com/stevesong/OFDS-datasets) | Global | CC-BY-4.0 | Spans + Nodes |
| [PeeringDB](https://www.peeringdb.com) | Global | CC0-1.0 | Nodes (IXP/DC) |
| [Submarine Cable Map](https://www.submarinecablemap.com) | Global | CC-BY-SA-4.0 | Nodes (landing) |
| [RNP Brazil](https://www.rnp.br/en/network/infrastructure) | Brazil | CC-BY-4.0 | Spans + Nodes |
| [ANATEL](https://dados.gov.br) | Brazil | CC-BY-4.0 | Spans |
| [OpenStreetMap](https://www.openstreetmap.org) | Global | ODbL-1.0 | Spans + Nodes |

> ⚠️ **Data limitations:** Route geometries are often approximate. Coverage is incomplete for many regions. See the About panel in the app for full disclaimer.

---

## Contributing a New Dataset

OpenFiberMap accepts contributions of open/publicly licensed fiber network data via the OFDS pipeline.

### Requirements
- Data must be **publicly available** under CC0, CC-BY, CC-BY-SA, ODbL, or equivalent
- Route geometries must be in WGS84 (EPSG:4326)
- Never submit data scraped from paywalled or login-required sources

### Steps

1. **Convert your data** to the OFM GeoJSON schema:
   ```bash
   # See schema/fiber-schema.json for the full spec
   # See data/samples/sample-africa.geojson for a working example
   ```

2. **Validate** it:
   ```bash
   python scripts/validate_schema.py your-data.geojson -v
   ```

3. **Write an ETL fetcher** in `scripts/etl/fetch_yourregion.py` following the pattern of existing fetchers.

4. **Add it to `scripts/run_etl.sh`** and `scripts/etl/merge.py`'s `INCLUDE_PATTERNS`.

5. **Open a Pull Request** with:
   - The fetcher script
   - An entry in `docs/PHASE1-DATA-SOURCES.md`
   - A sample output file in `data/samples/`

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for full details.

---

## Roadmap

- [ ] Cesium 3D Tiles output for large-scale datasets (> 1M features)
- [ ] OSM real-time diff sync (Osmium changeset monitoring)
- [ ] User-submitted route corrections (GitHub Issues template)
- [ ] EU / GÉANT + Internet2 backbone layers
- [ ] Asia-Pacific data (APRICOT/APNIC networks)
- [ ] Crowdsourced mode (OFDS-validated submissions via PR bot)
- [ ] Export: download visible features as GeoJSON / KML

---

## License

**Code:** MIT License — see [LICENSE](LICENSE)

**Data:** Each dataset retains its original license (see per-feature `license` property in GeoJSON). Derived merged datasets are released under ODbL 1.0 where all source licenses permit.

---

*OpenFiberMap is a public good. If you use it, please credit the original data sources.*
