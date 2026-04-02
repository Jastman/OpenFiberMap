# OpenFiberMap

**A free, open-source, interactive 3D global map of terrestrial fiber optic networks and telecom backhaul infrastructure.**

Inspired by [OpenGridWorks](https://opengridworks.com) for electricity grids. Built with CesiumJS, React, and Vite.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Phase](https://img.shields.io/badge/Phase-1%20%E2%80%94%20Schema%20%26%20Data%20Sources-blue)]()

---

## What is OpenFiberMap?

OpenFiberMap visualizes the world's fiber optic backbone infrastructure on an interactive 3D globe:

- **Fiber spans** (routes, corridors) with operator, capacity, status, burial type
- **Network nodes** (POPs, IXPs, data centers, submarine cable landing stations, amplifiers)
- **Filters** by region, operator, status, capacity
- **Popups** with full metadata and source links
- **Global scale** with high-quality data starting in Africa and Brazil

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vite + React + TypeScript + CesiumJS |
| Data | GeoJSON (OFDS-aligned) + CZML |
| ETL | Python (geopandas, requests, shapely) |
| Styling | Tailwind CSS + Cesium primitives |
| Deployment | GitHub Pages / Vercel |

## Project Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ Complete | Data sources research + schema design |
| 2 | 🔄 Next | ETL pipeline + initial dataset build |
| 3 | Planned | CesiumJS web app skeleton |
| 4 | Planned | Polish, features, deployment |
| 5 | Planned | Testing & iteration |

## Data Sources

See [docs/PHASE1-DATA-SOURCES.md](docs/PHASE1-DATA-SOURCES.md) for a full inventory of open/public data sources used.

## Schema

See [schema/fiber-schema.json](schema/fiber-schema.json) for the full GeoJSON schema (OFDS-aligned).

## Contributing

We welcome contributions of new datasets via the Open Fibre Data Standard (OFDS). See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

All data must be:
- Publicly available or openly licensed (ODbL, CC-BY, CC0, or equivalent)
- Properly attributed to its original source
- Not scraped from paywalled or private systems

## Attribution

OpenFiberMap aggregates data from many sources. Every feature in the dataset carries a `source_url` property linking back to the original data. See [docs/PHASE1-DATA-SOURCES.md](docs/PHASE1-DATA-SOURCES.md) for full credits.

## License

Code: MIT  
Data: Each dataset retains its original license (see per-feature `license` property). Derived work is released under ODbL where permitted.
