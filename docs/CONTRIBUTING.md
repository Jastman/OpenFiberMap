# Contributing to OpenFiberMap

## Adding New Datasets

All data contributions must follow these rules:

### Eligibility
- Data must be **publicly available** under an open license (CC0, CC-BY, CC-BY-SA, ODbL, or equivalent)
- **Never submit** data scraped from paywalled or login-required sources without explicit written permission
- If you are unsure about a source's license, open a GitHub Issue to discuss before submitting

### Format Requirements
All submitted GeoJSON must:
1. Validate against `schema/fiber-schema.json` (run `python scripts/validate_schema.py your-file.geojson`)
2. Include `source`, `source_url`, `license`, and `attribution` on every Feature
3. Use `ofm_layer: "fiber-spans"` or `ofm_layer: "fiber-nodes"` on every Feature
4. Use WGS84 coordinates (EPSG:4326)
5. Approximate geometries are acceptable — mark them with `"notes": "Geometry is approximate"`

### How to Submit
1. Fork the repository
2. Add your dataset to `data/submissions/{country-iso}-{operator-slug}.geojson`
3. Run validation: `python scripts/validate_schema.py data/submissions/your-file.geojson -v`
4. Add an entry to `docs/PHASE1-DATA-SOURCES.md` under the appropriate region
5. Open a Pull Request with a description of: source, license, coverage, and how you obtained it

## Reporting Data Errors
Open a GitHub Issue with:
- The `span_id` or `node_id` of the incorrect feature
- What is wrong (geometry, attribute, status)
- A link to a better source

## Code Contributions
- ETL scripts: Python 3.10+, use `geopandas`, `requests`, `shapely`
- Frontend: TypeScript strict mode, ESLint, Prettier
- Run `npm test` before opening a PR
