/**
 * cesiumStyles.ts — Cesium colour/style helpers for fiber spans and nodes.
 * Kept in sync with scripts/etl/generate_czml.py styling rules.
 */

import * as Cesium from "cesium";
import type { CapacityClass, FiberStatus, NodeType } from "@/types";

// ─── Capacity tier colours (RGBA 0–1) ────────────────────────────────────────

export const CAPACITY_COLORS: Record<CapacityClass, Cesium.Color> = {
  "ultra-high": Cesium.Color.fromCssColorString("#00E6FF"),
  "high":       Cesium.Color.fromCssColorString("#32C850"),
  "medium":     Cesium.Color.fromCssColorString("#FFC800"),
  "low":        Cesium.Color.fromCssColorString("#FF7800"),
  "unknown":    Cesium.Color.fromCssColorString("#8C8C8C"),
};

// ─── Status alpha ──────────────────────────────────────────────────────────────

const STATUS_ALPHAS: Record<string, number> = {
  "deployed":           1.0,
  "lit":                1.0,
  "ready-for-service":  0.9,
  "under-construction": 0.75,
  "planned":            0.45,
  "decommissioned":     0.25,
  "unknown":            0.3,
  // node statuses
  "operational":        1.0,
};

export function spanColor(
  capacityClass: CapacityClass | null,
  status: FiberStatus
): Cesium.Color {
  const base = CAPACITY_COLORS[capacityClass ?? "unknown"];
  const alpha = STATUS_ALPHAS[status] ?? 0.5;
  return base.withAlpha(alpha);
}

// ─── Span width ────────────────────────────────────────────────────────────────

const CAPACITY_WIDTHS: Record<CapacityClass, number> = {
  "ultra-high": 4.0,
  "high":       3.0,
  "medium":     2.0,
  "low":        1.5,
  "unknown":    1.2,
};

export function spanWidth(capacityClass: CapacityClass | null): number {
  return CAPACITY_WIDTHS[capacityClass ?? "unknown"];
}

// ─── Node icon paths ─────────────────────────────────────────────────────────

export const NODE_ICONS: Record<NodeType, string> = {
  "ixp":             "/icons/ixp.svg",
  "data-center":     "/icons/datacenter.svg",
  "pop":             "/icons/pop.svg",
  "landing-station": "/icons/landing.svg",
  "amplifier":       "/icons/amplifier.svg",
  "exchange":        "/icons/exchange.svg",
  "telecom-hotel":   "/icons/datacenter.svg",
  "government-node": "/icons/pop.svg",
  "research-node":   "/icons/pop.svg",
  "unknown":         "/icons/pop.svg",
};

export const NODE_SCALES: Record<NodeType, number> = {
  "ixp":             0.9,
  "data-center":     1.0,
  "pop":             0.65,
  "landing-station": 1.0,
  "amplifier":       0.45,
  "exchange":        0.55,
  "telecom-hotel":   0.8,
  "government-node": 0.6,
  "research-node":   0.6,
  "unknown":         0.5,
};

// ─── Node colour (for billboard tint / fallback pin) ─────────────────────────

export const NODE_COLORS: Record<NodeType, Cesium.Color> = {
  "ixp":             Cesium.Color.fromCssColorString("#00E6FF"),
  "data-center":     Cesium.Color.fromCssColorString("#A855F7"),
  "pop":             Cesium.Color.fromCssColorString("#6366F1"),
  "landing-station": Cesium.Color.fromCssColorString("#F59E0B"),
  "amplifier":       Cesium.Color.fromCssColorString("#6B7280"),
  "exchange":        Cesium.Color.fromCssColorString("#64748B"),
  "telecom-hotel":   Cesium.Color.fromCssColorString("#8B5CF6"),
  "government-node": Cesium.Color.fromCssColorString("#10B981"),
  "research-node":   Cesium.Color.fromCssColorString("#3B82F6"),
  "unknown":         Cesium.Color.fromCssColorString("#9CA3AF"),
};

// ─── Capacity legend entries (for Legend component) ───────────────────────────

export interface LegendEntry {
  label: string;
  color: string;
  description: string;
}

export const CAPACITY_LEGEND: LegendEntry[] = [
  { label: "≥ 1 Tbps",       color: "#00E6FF", description: "Ultra-high capacity" },
  { label: "100–999 Gbps",   color: "#32C850", description: "High capacity" },
  { label: "10–99 Gbps",     color: "#FFC800", description: "Medium capacity" },
  { label: "< 10 Gbps",      color: "#FF7800", description: "Low capacity" },
  { label: "Unknown capacity",color: "#8C8C8C", description: "No data" },
];

export const STATUS_LEGEND: LegendEntry[] = [
  { label: "Deployed / Lit",         color: "#32C850", description: "In service" },
  { label: "Under Construction",     color: "#F59E0B", description: "Being built" },
  { label: "Planned",                color: "#6B7280", description: "Announced, not built" },
  { label: "Decommissioned",         color: "#EF4444", description: "No longer in service" },
];
