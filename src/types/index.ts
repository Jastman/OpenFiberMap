// OpenFiberMap TypeScript types — aligned with schema/fiber-schema.json

// ─── GeoJSON base ────────────────────────────────────────────────────────────

export interface GeoJSONFeatureCollection {
  type: "FeatureCollection";
  name?: string;
  description?: string;
  version?: string;
  last_updated?: string;
  license?: string;
  attribution?: string;
  features: OFMFeature[];
}

export type OFMFeature = FiberSpanFeature | FiberNodeFeature;

// ─── Span (LineString) ────────────────────────────────────────────────────────

export type FiberStatus =
  | "deployed"
  | "ready-for-service"
  | "lit"
  | "under-construction"
  | "planned"
  | "decommissioned"
  | "unknown";

export type BurialType =
  | "underground"
  | "aerial"
  | "subsea"
  | "direct-buried"
  | "conduit"
  | "mixed"
  | "unknown";

export type CapacityClass =
  | "ultra-high"
  | "high"
  | "medium"
  | "low"
  | "unknown";

export type Region =
  | "africa"
  | "americas"
  | "europe"
  | "asia-pacific"
  | "middle-east"
  | "global";

export interface FiberSpanProperties {
  ofm_layer: "fiber-spans";
  span_id: string;
  network_id: string;
  name: string | null;
  operator: string;
  operator_id: string | null;
  country_iso: string | null;
  countries: string[] | null;
  region: Region | null;
  status: FiberStatus;
  burial_type: BurialType | null;
  length_km: number | null;
  capacity_gbps: number | null;
  capacity_class: CapacityClass | null;
  fiber_pairs: number | null;
  fiber_type: string | null;
  phase_id: string | null;
  phase_name: string | null;
  construction_start: string | null;
  ready_for_service: string | null;
  funders: string[] | null;
  contracts: string[] | null;
  source: string;
  source_url: string | null;
  license: string | null;
  attribution: string | null;
  last_updated: string | null;
  notes: string | null;
  ofds_span_id: string | null;
  osm_way_id: string | null;
}

export interface FiberSpanFeature {
  type: "Feature";
  geometry: {
    type: "LineString" | "MultiLineString";
    coordinates: number[][] | number[][][];
  };
  properties: FiberSpanProperties;
}

// ─── Node (Point) ─────────────────────────────────────────────────────────────

export type NodeType =
  | "ixp"
  | "data-center"
  | "pop"
  | "landing-station"
  | "amplifier"
  | "exchange"
  | "telecom-hotel"
  | "government-node"
  | "research-node"
  | "unknown";

export type NodeStatus =
  | "operational"
  | "planned"
  | "under-construction"
  | "decommissioned"
  | "unknown";

export interface FiberNodeProperties {
  ofm_layer: "fiber-nodes";
  node_id: string;
  network_id: string;
  name: string;
  name_short: string | null;
  operator: string;
  node_type: NodeType;
  status: NodeStatus;
  city: string | null;
  country_iso: string | null;
  region: Region | null;
  address: string | null;
  floor_space_sqm: number | null;
  power_mw: number | null;
  connected_networks: string[] | null;
  peeringdb_id: number | null;
  peeringdb_ix_id: number | null;
  website: string | null;
  source: string;
  source_url: string | null;
  license: string | null;
  attribution: string | null;
  last_updated: string | null;
  notes: string | null;
  osm_node_id: string | null;
  // optional submarine cable extension
  cable_count?: number;
  cables?: string[];
}

export interface FiberNodeFeature {
  type: "Feature";
  geometry: {
    type: "Point";
    coordinates: [number, number] | [number, number, number];
  };
  properties: FiberNodeProperties;
}

// ─── App state ────────────────────────────────────────────────────────────────

export interface LayerVisibility {
  spans: boolean;
  nodes: boolean;
  // By type
  ixp: boolean;
  "data-center": boolean;
  pop: boolean;
  "landing-station": boolean;
  amplifier: boolean;
  // By status
  deployed: boolean;
  planned: boolean;
  "under-construction": boolean;
  // By region
  africa: boolean;
  americas: boolean;
  europe: boolean;
  "asia-pacific": boolean;
  "middle-east": boolean;
}

export interface FilterState {
  region: Region | "all";
  operator: string | "all";
  status: FiberStatus | NodeStatus | "all";
  capacityClass: CapacityClass | "all";
  searchQuery: string;
}

export type DatasetKey =
  | "afterfibre-africa"
  | "brazil"
  | "ofds-africa"
  | "ofds-americas"
  | "peeringdb"
  | "landing-stations"
  | "osm-africa"
  | "osm-americas"
  | "osm-europe";

export interface DatasetConfig {
  key: DatasetKey;
  label: string;
  spansFile: string | null;
  nodesFile: string | null;
  region: Region;
  source: string;
  license: string;
}

export interface SelectedFeature {
  type: "span" | "node";
  properties: FiberSpanProperties | FiberNodeProperties;
}
