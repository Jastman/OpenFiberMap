#!/usr/bin/env python3
"""
validate_schema.py — Validate OpenFiberMap GeoJSON files against fiber-schema.json.

Usage:
    python scripts/validate_schema.py data/samples/sample-africa.geojson
    python scripts/validate_schema.py public/data/fiber-global.geojson --verbose

Requires:
    pip install jsonschema
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft202012Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(1)

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "fiber-schema.json"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_file(geojson_path: Path, schema: dict, verbose: bool = False) -> bool:
    print(f"\nValidating: {geojson_path}")
    data = load_json(geojson_path)

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

    if not errors:
        features = data.get("features", [])
        spans = [f for f in features if f.get("properties", {}).get("ofm_layer") == "fiber-spans"]
        nodes = [f for f in features if f.get("properties", {}).get("ofm_layer") == "fiber-nodes"]
        print(f"  PASS — {len(features)} features ({len(spans)} spans, {len(nodes)} nodes)")
        if verbose:
            operators = {f["properties"].get("operator") for f in features if f.get("properties")}
            statuses = {f["properties"].get("status") for f in features if f.get("properties")}
            countries = set()
            for f in features:
                props = f.get("properties", {})
                if props.get("countries"):
                    countries.update(props["countries"])
                elif props.get("country_iso"):
                    countries.add(props["country_iso"])
            print(f"  Operators : {sorted(o for o in operators if o)}")
            print(f"  Statuses  : {sorted(s for s in statuses if s)}")
            print(f"  Countries : {sorted(c for c in countries if c)}")
        return True
    else:
        print(f"  FAIL — {len(errors)} validation error(s):")
        for err in errors[:20]:
            path = " > ".join(str(p) for p in err.absolute_path) or "(root)"
            print(f"    [{path}] {err.message}")
        if len(errors) > 20:
            print(f"    ... and {len(errors) - 20} more errors")
        return False


def main():
    parser = argparse.ArgumentParser(description="Validate OpenFiberMap GeoJSON files")
    parser.add_argument("files", nargs="+", type=Path, help="GeoJSON file(s) to validate")
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH, help="Path to JSON schema")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show dataset summary")
    args = parser.parse_args()

    if not args.schema.exists():
        print(f"ERROR: Schema not found at {args.schema}", file=sys.stderr)
        sys.exit(1)

    schema = load_json(args.schema)
    print(f"Schema: {args.schema}")

    all_passed = True
    for path in args.files:
        if not path.exists():
            print(f"\nERROR: File not found: {path}", file=sys.stderr)
            all_passed = False
            continue
        passed = validate_file(path, schema, verbose=args.verbose)
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("All files passed validation.")
        sys.exit(0)
    else:
        print("Some files failed validation.")
        sys.exit(1)


if __name__ == "__main__":
    main()
