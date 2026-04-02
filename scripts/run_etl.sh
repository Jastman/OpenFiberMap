#!/usr/bin/env bash
# run_etl.sh — Master OpenFiberMap ETL pipeline runner.
#
# Runs all fetchers in priority order, then merges + generates CZML.
# Supports --offline (skip live APIs, use seed/cached data only).
# Supports --refresh (force re-download, ignore all caches).
#
# Usage:
#   ./scripts/run_etl.sh                        # Normal run (uses cache)
#   ./scripts/run_etl.sh --offline              # Offline / CI mode
#   ./scripts/run_etl.sh --refresh              # Force re-download everything
#   ./scripts/run_etl.sh --only peeringdb,brazil # Run specific fetchers only
#   ./scripts/run_etl.sh --skip osm             # Skip slow OSM queries

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

# Defaults
OFFLINE=""
REFRESH=""
ONLY=""
SKIP=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --offline)  OFFLINE="--offline"; shift ;;
    --refresh)  REFRESH="--refresh"; shift ;;
    --only)     ONLY="$2"; shift 2 ;;
    --skip)     SKIP="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: $0 [--offline] [--refresh] [--only LIST] [--skip LIST]"
      echo "  --offline    Use cached/seed data only (no HTTP requests)"
      echo "  --refresh    Force re-download, ignoring all caches"
      echo "  --only LIST  Comma-separated fetchers to run: peeringdb,ofds,submarine,afterfibre,brazil,osm"
      echo "  --skip LIST  Comma-separated fetchers to skip"
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# Colours
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[ETL]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

should_run() {
  local name="$1"
  if [[ -n "$ONLY" ]]; then
    echo "$ONLY" | grep -q "$name" || return 1
  fi
  if [[ -n "$SKIP" ]]; then
    echo "$SKIP" | grep -q "$name" && return 1
  fi
  return 0
}

log "Starting OpenFiberMap ETL pipeline"
log "Mode: ${OFFLINE:-online} ${REFRESH:-cached}"
echo ""

# --- Step 1: PeeringDB (nodes — fast CC0 API) ---
if should_run "peeringdb"; then
  log "1/6  PeeringDB — global IXP + data center nodes"
  python scripts/etl/fetch_peeringdb.py $REFRESH \
    || warn "PeeringDB fetcher failed (non-fatal, will use cached/empty)"
else
  log "1/6  PeeringDB [SKIPPED]"
fi

# --- Step 2: OFDS datasets (spans + nodes) ---
if should_run "ofds"; then
  log "2/6  OFDS-datasets — Africa + Americas fiber spans"
  python scripts/etl/fetch_ofds_datasets.py $REFRESH \
    || warn "OFDS-datasets fetcher failed (non-fatal)"
else
  log "2/6  OFDS-datasets [SKIPPED]"
fi

# --- Step 3: Submarine Cable Map (landing station nodes) ---
if should_run "submarine"; then
  log "3/6  Submarine Cable Map — global landing stations"
  python scripts/etl/fetch_submarine_cables.py $REFRESH \
    || warn "Submarine Cable Map fetcher failed (non-fatal)"
else
  log "3/6  Submarine Cable Map [SKIPPED]"
fi

# --- Step 4: AfTerFibre (Africa backbone) ---
if should_run "afterfibre"; then
  log "4/6  AfTerFibre — Africa backbone spans + nodes"
  python scripts/etl/fetch_afterfibre.py $OFFLINE $REFRESH \
    || warn "AfTerFibre fetcher failed (non-fatal, seed data available)"
else
  log "4/6  AfTerFibre [SKIPPED]"
fi

# --- Step 5: Brazil RNP (South America) ---
if should_run "brazil"; then
  log "5/6  Brazil RNP — South America fiber backbone"
  python scripts/etl/fetch_brazil_rnp.py $OFFLINE $REFRESH \
    || warn "Brazil RNP fetcher failed (non-fatal, seed data available)"
else
  log "5/6  Brazil RNP [SKIPPED]"
fi

# --- Step 6: OSM Overpass (gap-fill — slowest, can be skipped) ---
if should_run "osm" && [[ -z "$OFFLINE" ]]; then
  log "6/6  OSM Overpass — global fiber gap-fill (this may take several minutes)"
  python scripts/etl/fetch_osm.py $REFRESH \
    || warn "OSM fetcher failed (non-fatal, Overpass can be slow)"
else
  log "6/6  OSM Overpass [SKIPPED${OFFLINE:+ — offline mode}]"
fi

echo ""
log "--- Merge all sources ---"
python scripts/etl/merge.py --stats

echo ""
log "--- Generate CZML for Cesium ---"
python scripts/etl/generate_czml.py --split

echo ""
log "--- Validate sample output ---"
python scripts/validate_schema.py data/samples/sample-africa.geojson -v

echo ""
log "ETL pipeline complete."
log "Output files in: public/data/"
ls -lh "$ROOT_DIR/public/data/"*.geojson 2>/dev/null | awk '{print "  "$NF, $5}' || true
