/**
 * dataLoader.ts — Load OpenFiberMap GeoJSON into Cesium as styled primitives.
 *
 * Strategy:
 *   - Spans → Cesium PolylineCollection (primitive; much faster than entities
 *     for thousands of lines, supports per-instance colour).
 *   - Nodes → Cesium BillboardCollection + LabelCollection.
 *   - We also keep a lookup map from Cesium primitive ID → OFM properties
 *     so click handlers can show the info panel.
 */

import * as Cesium from "cesium";
import type {
  GeoJSONFeatureCollection,
  FiberSpanFeature,
  FiberNodeFeature,
  FiberSpanProperties,
  FiberNodeProperties,
  FilterState,
  CapacityClass,
  FiberStatus,
  NodeType,
} from "@/types";
import { spanColor, spanWidth, NODE_COLORS, NODE_SCALES } from "./cesiumStyles";

// ─── Types ───────────────────────────────────────────────────────────────────

export interface LoadedLayer {
  polylines: Cesium.PolylineCollection;
  billboards: Cesium.BillboardCollection;
  labels: Cesium.LabelCollection;
  /** Map from primitive id (polyline/billboard index) → feature properties */
  spanIndex: Map<string, FiberSpanProperties>;
  nodeIndex: Map<string, FiberNodeProperties>;
  sourceFile: string;
}

// ─── Coordinate helpers ───────────────────────────────────────────────────────

function coordsToCartesian(
  coords: number[][] | number[][][],
  geomType: string
): Cesium.Cartesian3[][] {
  if (geomType === "MultiLineString") {
    return (coords as number[][][]).map((ring) =>
      ring.map(([lon, lat]) => Cesium.Cartesian3.fromDegrees(lon, lat))
    );
  }
  return [(coords as number[][]).map(([lon, lat]) => Cesium.Cartesian3.fromDegrees(lon, lat))];
}

// ─── Filter predicate ─────────────────────────────────────────────────────────

export function spanMatchesFilter(
  props: FiberSpanProperties,
  filter: FilterState
): boolean {
  if (filter.region !== "all" && props.region !== filter.region) return false;
  if (filter.operator !== "all" && props.operator !== filter.operator) return false;
  if (filter.status !== "all" && props.status !== filter.status) return false;
  if (filter.capacityClass !== "all" && props.capacity_class !== filter.capacityClass) return false;
  if (filter.searchQuery) {
    const q = filter.searchQuery.toLowerCase();
    const name = (props.name ?? "").toLowerCase();
    const op   = (props.operator ?? "").toLowerCase();
    if (!name.includes(q) && !op.includes(q)) return false;
  }
  return true;
}

export function nodeMatchesFilter(
  props: FiberNodeProperties,
  filter: FilterState
): boolean {
  if (filter.region !== "all" && props.region !== filter.region) return false;
  if (filter.operator !== "all" && props.operator !== filter.operator) return false;
  if (filter.searchQuery) {
    const q = filter.searchQuery.toLowerCase();
    const name = (props.name ?? "").toLowerCase();
    const op   = (props.operator ?? "").toLowerCase();
    const city = (props.city ?? "").toLowerCase();
    if (!name.includes(q) && !op.includes(q) && !city.includes(q)) return false;
  }
  return true;
}

// ─── Span loader ─────────────────────────────────────────────────────────────

function addSpan(
  polylines: Cesium.PolylineCollection,
  spanIndex: Map<string, FiberSpanProperties>,
  feat: FiberSpanFeature,
  filter: FilterState,
): void {
  const props = feat.properties;
  if (!spanMatchesFilter(props, filter)) return;

  const geom = feat.geometry;
  const lineGroups = coordsToCartesian(geom.coordinates, geom.type);
  const color = spanColor(props.capacity_class as CapacityClass, props.status as FiberStatus);
  const width = spanWidth(props.capacity_class as CapacityClass);
  const isDashed = props.status === "planned" || props.status === "under-construction";

  for (const positions of lineGroups) {
    if (positions.length < 2) continue;

    const id = `span:${props.span_id}:${Math.random().toString(36).slice(2)}`;
    const polyline = polylines.add({
      positions,
      width,
      material: isDashed
        ? new Cesium.Material({
            fabric: {
              type: "PolylineDash",
              uniforms: {
                color: color,
                gapColor: Cesium.Color.TRANSPARENT,
                dashLength: props.status === "planned" ? 20.0 : 12.0,
              },
            },
          })
        : new Cesium.Material({
            fabric: {
              type: "Color",
              uniforms: { color },
            },
          }),
      clampToGround: true,
      show: true,
      id,
    });

    spanIndex.set(id, props);
  }
}

// ─── Node loader ─────────────────────────────────────────────────────────────

function addNode(
  billboards: Cesium.BillboardCollection,
  labels: Cesium.LabelCollection,
  nodeIndex: Map<string, FiberNodeProperties>,
  feat: FiberNodeFeature,
  filter: FilterState,
): void {
  const props = feat.properties;
  if (!nodeMatchesFilter(props, filter)) return;

  const [lon, lat] = feat.geometry.coordinates;
  const position = Cesium.Cartesian3.fromDegrees(lon, lat);
  const nodeType = props.node_type as NodeType;
  const color = NODE_COLORS[nodeType] ?? NODE_COLORS["unknown"];
  const scale = NODE_SCALES[nodeType] ?? 0.6;
  const id = `node:${props.node_id}`;

  // Billboard — use a coloured pin as fallback (SVG icons added in Phase 4)
  billboards.add({
    position,
    image: buildPinCanvas(color, nodeType),
    scale,
    verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
    heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
    disableDepthTestDistance: 1_500_000,
    show: true,
    id,
  });

  // Label (fades in on zoom)
  const labelText = props.name_short ?? props.name.slice(0, 24);
  labels.add({
    position,
    text: labelText,
    font: "11px Inter, sans-serif",
    fillColor: Cesium.Color.WHITE,
    outlineColor: Cesium.Color.BLACK,
    outlineWidth: 2,
    style: Cesium.LabelStyle.FILL_AND_OUTLINE,
    verticalOrigin: Cesium.VerticalOrigin.TOP,
    pixelOffset: new Cesium.Cartesian2(0, 10),
    heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
    disableDepthTestDistance: 800_000,
    translucencyByDistance: new Cesium.NearFarScalar(500_000, 1.0, 3_000_000, 0.0),
    show: true,
    id: `label:${props.node_id}`,
  });

  nodeIndex.set(id, props);
}

// ─── Canvas pin builder ───────────────────────────────────────────────────────

const PIN_CACHE = new Map<string, HTMLCanvasElement>();

function buildPinCanvas(color: Cesium.Color, nodeType: NodeType): HTMLCanvasElement {
  const key = `${color.toCssColorString()}-${nodeType}`;
  if (PIN_CACHE.has(key)) return PIN_CACHE.get(key)!;

  const size = 28;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size + 6; // extra for the pin point
  const ctx = canvas.getContext("2d")!;

  const cssColor = color.toCssColorString();

  // Circle body
  ctx.beginPath();
  ctx.arc(size / 2, size / 2, size / 2 - 2, 0, Math.PI * 2);
  ctx.fillStyle = cssColor;
  ctx.fill();
  ctx.strokeStyle = "rgba(255,255,255,0.7)";
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Node type symbol
  ctx.fillStyle = "white";
  ctx.font = `bold ${size * 0.42}px monospace`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const symbol: Record<NodeType, string> = {
    "ixp": "IX",
    "data-center": "DC",
    "pop": "P",
    "landing-station": "LS",
    "amplifier": "A",
    "exchange": "EX",
    "telecom-hotel": "TH",
    "government-node": "G",
    "research-node": "R",
    "unknown": "?",
  };
  ctx.fillText(symbol[nodeType] ?? "?", size / 2, size / 2);

  PIN_CACHE.set(key, canvas);
  return canvas;
}

// ─── Main loader ──────────────────────────────────────────────────────────────

export async function loadGeoJSON(
  scene: Cesium.Scene,
  url: string,
  filter: FilterState,
): Promise<LoadedLayer> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to load ${url}: ${response.status}`);
  const fc: GeoJSONFeatureCollection = await response.json();

  const polylines = new Cesium.PolylineCollection();
  const billboards = new Cesium.BillboardCollection({ scene });
  const labels = new Cesium.LabelCollection({ scene });
  const spanIndex = new Map<string, FiberSpanProperties>();
  const nodeIndex = new Map<string, FiberNodeProperties>();

  for (const feat of fc.features) {
    if (feat.properties.ofm_layer === "fiber-spans") {
      addSpan(polylines, spanIndex, feat as FiberSpanFeature, filter);
    } else if (feat.properties.ofm_layer === "fiber-nodes") {
      addNode(billboards, labels, nodeIndex, feat as FiberNodeFeature, filter);
    }
  }

  scene.primitives.add(polylines);
  scene.primitives.add(billboards);
  scene.primitives.add(labels);

  return { polylines, billboards, labels, spanIndex, nodeIndex, sourceFile: url };
}

export function removeLayer(scene: Cesium.Scene, layer: LoadedLayer): void {
  scene.primitives.remove(layer.polylines);
  scene.primitives.remove(layer.billboards);
  scene.primitives.remove(layer.labels);
}

// ─── Pick handler ─────────────────────────────────────────────────────────────

export function pickFeature(
  scene: Cesium.Scene,
  position: Cesium.Cartesian2,
  layers: LoadedLayer[],
): { type: "span" | "node"; properties: FiberSpanProperties | FiberNodeProperties } | null {
  const picked = scene.pick(position);
  if (!picked) return null;

  const id = picked.id as string | undefined;
  if (!id) return null;

  for (const layer of layers) {
    if (id.startsWith("span:")) {
      const props = layer.spanIndex.get(id);
      if (props) return { type: "span", properties: props };
    }
    if (id.startsWith("node:")) {
      const props = layer.nodeIndex.get(id);
      if (props) return { type: "node", properties: props };
    }
  }
  return null;
}
