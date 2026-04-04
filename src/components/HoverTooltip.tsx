/**
 * HoverTooltip.tsx — Small popup that follows the cursor when hovering
 * over a fiber span or node on the globe. Shows a one-line summary;
 * clicking opens the full InfoPanel.
 */

import type { SelectedFeature } from "@/types";
import type { FiberSpanProperties, FiberNodeProperties } from "@/types";

interface Props {
  feature: SelectedFeature;
  screenX: number;
  screenY: number;
}

const NODE_TYPE_LABELS: Record<string, string> = {
  "ixp":             "Internet Exchange Point",
  "data-center":     "Data Center",
  "landing-station": "Landing Station",
  "pop":             "Point of Presence",
  "amplifier":       "Amplifier",
  "exchange":        "Exchange",
  "telecom-hotel":   "Telecom Hotel",
  "government-node": "Government Node",
  "research-node":   "Research Node",
};

export default function HoverTooltip({ feature, screenX, screenY }: Props) {
  const isSpan = feature.type === "span";
  const props  = feature.properties;

  let title = "";
  let sub   = "";

  if (isSpan) {
    const p = props as FiberSpanProperties;
    title = p.name ?? p.operator ?? "Fiber Span";
    const cap = p.capacity_gbps != null ? `${p.capacity_gbps} Gbps` : p.capacity_class ?? "";
    const status = p.status ? p.status.replace(/-/g, " ") : "";
    sub = [p.operator, cap, status].filter(Boolean).join(" · ");
  } else {
    const p = props as FiberNodeProperties;
    title = p.name ?? p.operator ?? "Node";
    const typeLabel = NODE_TYPE_LABELS[p.node_type ?? ""] ?? p.node_type ?? "";
    sub = [typeLabel, p.city, p.operator].filter(Boolean).join(" · ");
  }

  // Clamp to avoid going off-screen (offset 16px right + 8px above cursor)
  const style: React.CSSProperties = {
    position:  "fixed",
    left:      screenX + 16,
    top:       screenY - 8,
    transform: "translateY(-100%)",
    pointerEvents: "none",
    zIndex:    40,
  };

  return (
    <div style={style}
         className="max-w-xs px-3 py-2 rounded-xl shadow-xl
                    bg-[rgba(13,17,28,0.97)] border border-white/15">
      <p className="text-xs font-semibold text-white truncate">{title}</p>
      {sub && <p className="text-xs text-slate-400 truncate mt-0.5">{sub}</p>}
      <p className="text-[10px] text-slate-600 mt-1">Click for details</p>
    </div>
  );
}
