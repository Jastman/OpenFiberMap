/**
 * Sidebar.tsx — Left panel with layer toggles, region/operator/status filters,
 * and dataset attribution list.
 */

import type { FilterState, Region, FiberStatus, CapacityClass } from "@/types";

interface Props {
  filters: FilterState;
  showSpans: boolean;
  showNodes: boolean;
  onShowSpans: (v: boolean) => void;
  onShowNodes: (v: boolean) => void;
  onRegion: (v: Region | "all") => void;
  onOperator: (v: string) => void;
  onStatus: (v: FiberStatus | "all") => void;
  onCapacity: (v: CapacityClass | "all") => void;
  onReset: () => void;
  isOpen: boolean;
  onToggle: () => void;
}

// ─── Small reusables ──────────────────────────────────────────────────────────

function Toggle({
  label, checked, onChange, color = "#32C850",
}: { label: string; checked: boolean; onChange: (v: boolean) => void; color?: string }) {
  return (
    <label className="flex items-center gap-3 cursor-pointer select-none group">
      <span
        className="relative inline-flex h-5 w-9 flex-shrink-0 rounded-full transition-colors duration-200"
        style={{ background: checked ? color : "#374151" }}
        onClick={() => onChange(!checked)}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform duration-200 mt-0.5 ${
            checked ? "translate-x-4 ml-0.5" : "translate-x-0.5"
          }`}
        />
      </span>
      <span className="text-sm text-slate-300 group-hover:text-white transition-colors">
        {label}
      </span>
    </label>
  );
}

function Select<T extends string>({
  label, value, options, onChange,
}: {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <div className="space-y-1">
      <label className="block text-xs text-slate-500 uppercase tracking-wider font-semibold">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as T)}
        className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-sky-500 cursor-pointer"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  );
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-3 mt-5 first:mt-0">
      {children}
    </h3>
  );
}

// ─── Dataset attribution ──────────────────────────────────────────────────────

const DATASETS = [
  { name: "AfTerFibre (NSRC)", url: "https://afterfibre.nsrc.org", license: "CC-BY", region: "Africa" },
  { name: "RNP (Brazil)", url: "https://rnp.br", license: "CC-BY", region: "Americas" },
  { name: "OFDS-datasets", url: "https://github.com/stevesong/OFDS-datasets", license: "CC-BY", region: "Global" },
  { name: "PeeringDB", url: "https://peeringdb.com", license: "CC0", region: "Global" },
  { name: "Submarine Cable Map", url: "https://submarinecablemap.com", license: "CC-BY-SA", region: "Global" },
  { name: "OpenStreetMap", url: "https://openstreetmap.org", license: "ODbL", region: "Global" },
];

// ─── Main component ───────────────────────────────────────────────────────────

export default function Sidebar({
  filters, showSpans, showNodes,
  onShowSpans, onShowNodes,
  onRegion, onOperator, onStatus, onCapacity,
  onReset, isOpen, onToggle,
}: Props) {
  const hasActiveFilters =
    filters.region !== "all" ||
    filters.operator !== "all" ||
    filters.status !== "all" ||
    filters.capacityClass !== "all";

  return (
    <>
      {/* Toggle tab */}
      <button
        onClick={onToggle}
        className="absolute left-0 top-1/2 -translate-y-1/2 z-30 bg-slate-900 border border-white/10 rounded-r-xl px-1.5 py-4 text-slate-400 hover:text-white hover:bg-slate-800 transition-all shadow-lg"
        style={{ left: isOpen ? "288px" : "0" }}
        aria-label={isOpen ? "Close sidebar" : "Open sidebar"}
      >
        <svg className={`w-4 h-4 transition-transform duration-300 ${isOpen ? "rotate-180" : ""}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>

      {/* Panel */}
      <div
        className={`absolute left-0 top-0 bottom-0 z-20 flex flex-col transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        style={{ width: "288px" }}
      >
        <div className="flex-1 bg-[rgba(13,17,28,0.97)] border-r border-white/10 shadow-panel overflow-y-auto flex flex-col">

          {/* Logo / header */}
          <div className="px-5 pt-5 pb-4 border-b border-white/8">
            <div className="flex items-center gap-2.5 mb-1">
              <span className="text-2xl">🌐</span>
              <span className="text-white font-bold text-lg tracking-tight">OpenFiberMap</span>
            </div>
            <p className="text-slate-500 text-xs leading-relaxed">
              Open-source global fiber optic network visualization
            </p>
          </div>

          <div className="flex-1 px-5 py-4 space-y-1 overflow-y-auto">

            {/* ── Layer visibility ── */}
            <SectionHeader>Layers</SectionHeader>
            <div className="space-y-3">
              <Toggle
                label="Fiber Routes"
                checked={showSpans}
                onChange={onShowSpans}
                color="#32C850"
              />
              <Toggle
                label="Network Nodes"
                checked={showNodes}
                onChange={onShowNodes}
                color="#00E6FF"
              />
            </div>

            {/* ── Filters ── */}
            <SectionHeader>Filters</SectionHeader>
            <div className="space-y-3">
              <Select<Region | "all">
                label="Region"
                value={filters.region}
                onChange={onRegion}
                options={[
                  { value: "all",          label: "All Regions" },
                  { value: "africa",       label: "Africa" },
                  { value: "americas",     label: "Americas" },
                  { value: "europe",       label: "Europe" },
                  { value: "asia-pacific", label: "Asia–Pacific" },
                  { value: "middle-east",  label: "Middle East" },
                ]}
              />

              <Select<FiberStatus | "all">
                label="Status"
                value={filters.status as FiberStatus | "all"}
                onChange={onStatus}
                options={[
                  { value: "all",               label: "All Statuses" },
                  { value: "deployed",          label: "Deployed" },
                  { value: "lit",               label: "Lit" },
                  { value: "ready-for-service", label: "Ready for Service" },
                  { value: "under-construction",label: "Under Construction" },
                  { value: "planned",           label: "Planned" },
                  { value: "decommissioned",    label: "Decommissioned" },
                ]}
              />

              <Select<CapacityClass | "all">
                label="Capacity"
                value={filters.capacityClass}
                onChange={onCapacity}
                options={[
                  { value: "all",        label: "All Capacities" },
                  { value: "ultra-high", label: "≥ 1 Tbps (Ultra-high)" },
                  { value: "high",       label: "100–999 Gbps (High)" },
                  { value: "medium",     label: "10–99 Gbps (Medium)" },
                  { value: "low",        label: "< 10 Gbps (Low)" },
                  { value: "unknown",    label: "Unknown" },
                ]}
              />

              {hasActiveFilters && (
                <button
                  onClick={onReset}
                  className="w-full text-xs text-amber-400 hover:text-amber-300 border border-amber-400/30 hover:border-amber-400/60 rounded-lg px-3 py-1.5 transition-all"
                >
                  Reset filters
                </button>
              )}
            </div>

            {/* ── Data sources ── */}
            <SectionHeader>Data Sources</SectionHeader>
            <div className="space-y-2">
              {DATASETS.map((ds) => (
                <div key={ds.name} className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <a
                      href={ds.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-sky-400 hover:text-sky-300 underline underline-offset-2 truncate block"
                    >
                      {ds.name}
                    </a>
                    <span className="text-xs text-slate-600">{ds.region}</span>
                  </div>
                  <span className="text-xs text-slate-600 flex-shrink-0 font-mono">{ds.license}</span>
                </div>
              ))}
            </div>

          </div>

          {/* Footer */}
          <div className="px-5 py-3 border-t border-white/8 text-xs text-slate-600">
            <a
              href="https://github.com/jastman/OpenFiberMap"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-slate-400 transition-colors"
            >
              GitHub · MIT License · Contribute data
            </a>
          </div>
        </div>
      </div>
    </>
  );
}
