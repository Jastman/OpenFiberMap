# OpenFiberMap Schema

## Overview

`fiber-schema.json` is a JSON Schema (Draft 2020-12) describing a single GeoJSON `FeatureCollection` that contains two interleaved feature types, distinguished by the `ofm_layer` property:

| `ofm_layer` value | GeoJSON geometry | Description |
|-------------------|-----------------|-------------|
| `fiber-spans` | LineString or MultiLineString | Physical cable routes / corridors |
| `fiber-nodes` | Point | POPs, IXPs, data centers, landing stations, amplifiers |

## OFDS Alignment

This schema is inspired by the [Open Fibre Data Standard (OFDS) v1.0](https://open-fibre-data-standard.readthedocs.io/) and maps to its concepts as follows:

| OFDS Concept | OFM Property | Notes |
|-------------|-------------|-------|
| `Span.id` | `span_id` | Globally unique within dataset |
| `Span.name` | `name` | Human-readable label |
| `Span.physicalInfrastructureProvider` | `operator` | Network operator name |
| `Span.status` | `status` | Extended codelist |
| `Span.deploymentDetails.fibreType` | `burial_type` | Underground/aerial/subsea |
| `Node.id` | `node_id` | Globally unique within dataset |
| `Node.type` | `node_type` | Extended codelist |
| `PhaseCollection` | `phase_id` / `phase_name` | Links to project phases |

## Status Codelist

### FiberSpan.status
| Value | Description |
|-------|-------------|
| `deployed` | Cable is physically installed |
| `ready-for-service` | Installed, awaiting activation |
| `lit` | Active and carrying traffic |
| `under-construction` | Currently being built |
| `planned` | Announced but not yet under construction |
| `decommissioned` | No longer in service |
| `unknown` | Status not available |

### FiberNode.status
| Value | Description |
|-------|-------------|
| `operational` | Active and functional |
| `planned` | Announced, not yet built |
| `under-construction` | Being built |
| `decommissioned` | No longer in service |
| `unknown` | Status not available |

## Capacity Classes

The `capacity_class` field is derived by ETL from `capacity_gbps`:

| Class | Range | Color (map) |
|-------|-------|-------------|
| `ultra-high` | ≥ 1000 Gbps (1 Tbps+) | Bright cyan |
| `high` | 100–999 Gbps | Green |
| `medium` | 10–99 Gbps | Yellow |
| `low` | < 10 Gbps | Orange |
| `unknown` | No data | Grey |

## Validation

Validate datasets using the [OFDS CoVE validator](https://ofds.cove.opendataservices.coop/) for OFDS compliance, or use `ajv` for JSON Schema validation:

```bash
npm install -g ajv-cli
ajv validate -s schema/fiber-schema.json -d data/samples/sample-africa.geojson
```

## ID Namespacing

IDs follow the pattern `{country_iso}-{operator_slug}--{sequential}`:

```
ng-mainone--001     → Nigeria, MainOne, span 1
ke-safaricom--042   → Kenya, Safaricom, span 42
ixp-ng-lixp-01      → IXP, Nigeria, LIXP, node 1
dc-za-teraco-jb1    → Data center, South Africa, Teraco JB1
ls-ke-mombasa-01    → Landing station, Kenya, Mombasa, node 1
```

Country code `XA` is used for cross-border spans (non-standard, internal convention).
