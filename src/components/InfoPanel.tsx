/**
 * InfoPanel.tsx — Slide-in panel showing full attributes of a selected
 * fiber span or node, with source links and attribution.
 */

import type { SelectedFeature, FiberSpanProperties, FiberNodeProperties } from "@/types";
import { CAPACITY_COLORS, NODE_COLORS } from "@/lib/cesiumStyles";

interface Props {
  feature: SelectedFeature | null;
  onClose: () => void;
}

// ─── Status badges ────────────────────────────────────────────────────────────

const STATUS_COLORS: Record<string, string> = {
  deployed:           "bg-green-700 text-green-100",
  lit:                "bg-emerald-700 text-emerald-100",
  "ready-for-service":"bg-blue-700 text-blue-100",
  "under-construction":"bg-amber-600 text-amber-100",
  planned:            "bg-slate-600 text-slate-100",
  decommissioned:     "bg-red-700 text-red-100",
  operational:        "bg-green-700 text-green-100",
  unknown:            "bg-gray-700 text-gray-100",
};

function StatusBadge({ status }: { status: string }) {
  const cls = STATUS_COLORS[status] ?? STATUS_COLORS.unknown;
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wide ${cls}`}>
      {status.replace(/-/g, " ")}
    </span>
  );
}

// ─── Row ─────────────────────────────────────────────────────────────────────

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  if (value === null || value === undefined || value === "") return null;
  return (
    <div className="grid grid-cols-2 gap-x-3 py-1.5 border-b border-white/5 text-sm">
      <span className="text-slate-400 font-medium">{label}</span>
      <span className="text-slate-100 break-words">{value}</span>
    </div>
  );
}

// ─── Capacity dot ─────────────────────────────────────────────────────────────

function CapacityDot({ cls }: { cls: string }) {
  const colors: Record<string, string> = {
    "ultra-high": "#00E6FF",
    "high":       "#32C850",
    "medium":     "#FFC800",
    "low":        "#FF7800",
    "unknown":    "#8C8C8C",
  };
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
        style={{ background: colors[cls] ?? colors.unknown }}
      />
      {cls}
    </span>
  );
}

// ─── Span panel ───────────────────────────────────────────────────────────────

function SpanPanel({ props }: { props: FiberSpanProperties }) {
  return (
    <div className="space-y-0.5">
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <h3 className="text-white font-semibold text-base leading-tight">
            {props.name ?? props.operator}
          </h3>
          {props.name && (
            <p className="text-slate-400 text-xs mt-0.5">{props.operator}</p>
          )}
        </div>
        <StatusBadge status={props.status} />
      </div>

      <Row label="Capacity"
        value={props.capacity_gbps
          ? <><CapacityDot cls={props.capacity_class ?? "unknown"} /> {props.capacity_gbps} Gbps</>
          : <CapacityDot cls={props.capacity_class ?? "unknown"} />
        }
      />
      <Row label="Length"     value={props.length_km ? `${props.length_km.toLocaleString()} km` : null} />
      <Row label="Burial"     value={props.burial_type?.replace(/-/g, " ")} />
      <Row label="Fiber type" value={props.fiber_type} />
      <Row label="Countries"  value={(props.countries ?? [props.country_iso]).filter(Boolean).join(", ")} />
      <Row label="Region"     value={props.region} />

      {props.phase_name && <Row label="Phase"   value={props.phase_name} />}
      {(props.funders?.length ?? 0) > 0 && (
        <Row label="Funders" value={props.funders!.join(", ")} />
      )}
      {props.construction_start && (
        <Row label="Construction start" value={props.construction_start} />
      )}
      {props.ready_for_service && (
        <Row label="Ready for service" value={props.ready_for_service} />
      )}

      <div className="mt-3 pt-3 border-t border-white/10 space-y-1">
        <Row label="Source" value={
          props.source_url
            ? <a href={props.source_url} target="_blank" rel="noopener noreferrer"
                className="text-sky-400 hover:text-sky-300 underline underline-offset-2">
                {props.source}
              </a>
            : props.source
        } />
        <Row label="License" value={props.license} />
        <Row label="Last updated" value={props.last_updated} />
        {props.notes && <Row label="Notes" value={<em className="text-slate-400">{props.notes}</em>} />}
      </div>
    </div>
  );
}

// ─── Node panel ───────────────────────────────────────────────────────────────

function NodePanel({ props }: { props: FiberNodeProperties }) {
  return (
    <div className="space-y-0.5">
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <h3 className="text-white font-semibold text-base leading-tight">
            {props.name}
          </h3>
          <p className="text-slate-400 text-xs mt-0.5">
            {props.node_type.replace(/-/g, " ").toUpperCase()} · {props.city}
          </p>
        </div>
        <StatusBadge status={props.status} />
      </div>

      <Row label="Operator"  value={props.operator} />
      <Row label="Type"      value={props.node_type.replace(/-/g, " ")} />
      <Row label="City"      value={props.city} />
      <Row label="Country"   value={props.country_iso} />
      <Row label="Region"    value={props.region} />
      {props.floor_space_sqm && (
        <Row label="Floor space" value={`${props.floor_space_sqm.toLocaleString()} m²`} />
      )}
      {props.power_mw && (
        <Row label="Power" value={`${props.power_mw} MW`} />
      )}
      {props.website && (
        <Row label="Website" value={
          <a href={props.website} target="_blank" rel="noopener noreferrer"
             className="text-sky-400 hover:text-sky-300 underline underline-offset-2 truncate block">
            {props.website.replace(/^https?:\/\//, "")}
          </a>
        } />
      )}
      {(props.peeringdb_id ?? props.peeringdb_ix_id) && (
        <Row label="PeeringDB" value={
          <a
            href={`https://www.peeringdb.com/${props.peeringdb_ix_id ? "ix" : "fac"}/${props.peeringdb_ix_id ?? props.peeringdb_id}`}
            target="_blank" rel="noopener noreferrer"
            className="text-sky-400 hover:text-sky-300 underline underline-offset-2">
            #{props.peeringdb_ix_id ?? props.peeringdb_id}
          </a>
        } />
      )}

      {"cables" in props && props.cables && props.cables.length > 0 && (
        <Row label="Cables" value={props.cables.slice(0, 6).join(", ") + (props.cables.length > 6 ? "…" : "")} />
      )}

      <div className="mt-3 pt-3 border-t border-white/10 space-y-1">
        <Row label="Source" value={
          props.source_url
            ? <a href={props.source_url} target="_blank" rel="noopener noreferrer"
                className="text-sky-400 hover:text-sky-300 underline underline-offset-2">
                {props.source}
              </a>
            : props.source
        } />
        <Row label="License" value={props.license} />
        {props.notes && <Row label="Notes" value={<em className="text-slate-400">{props.notes}</em>} />}
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function InfoPanel({ feature, onClose }: Props) {
  if (!feature) return null;

  return (
    <div className="absolute right-0 top-0 bottom-0 w-80 z-20 flex flex-col pointer-events-auto">
      <div className="flex-1 bg-[rgba(15,20,35,0.95)] border-l border-white/10 shadow-panel overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-[rgba(15,20,35,0.98)] border-b border-white/10 flex items-center justify-between px-4 py-3 z-10">
          <span className="text-slate-300 text-xs font-semibold uppercase tracking-widest">
            {feature.type === "span" ? "Fiber Span" : "Network Node"}
          </span>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors p-1 rounded hover:bg-white/10"
            aria-label="Close"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {feature.type === "span" ? (
            <SpanPanel props={feature.properties as FiberSpanProperties} />
          ) : (
            <NodePanel props={feature.properties as FiberNodeProperties} />
          )}
        </div>
      </div>
    </div>
  );
}
