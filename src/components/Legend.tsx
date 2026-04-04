/**
 * Legend.tsx — Map legend showing capacity colour ramps and status indicators.
 * Collapsed by default on mobile; expanded on desktop.
 */

import { useState } from "react";
import { CAPACITY_LEGEND, STATUS_LEGEND } from "@/lib/cesiumStyles";

export default function Legend() {
  const [open, setOpen] = useState(true);

  return (
    <div className="absolute bottom-20 right-4 z-20 w-52">
      {/* Toggle header */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-3 py-2
                   bg-[rgba(13,17,28,0.95)] border border-white/10 rounded-xl
                   text-xs font-semibold text-slate-300 hover:text-white
                   shadow-panel transition-all"
      >
        <span className="uppercase tracking-widest">Legend</span>
        <svg
          className={`w-3.5 h-3.5 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="mt-1 bg-[rgba(13,17,28,0.97)] border border-white/10 rounded-xl shadow-panel p-3 space-y-4">

          {/* Capacity */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
              Capacity (line colour)
            </p>
            <div className="space-y-1.5">
              {CAPACITY_LEGEND.map(({ label, color }) => (
                <div key={label} className="flex items-center gap-2">
                  <span
                    className="inline-block w-8 h-1.5 rounded-full flex-shrink-0"
                    style={{ background: color }}
                  />
                  <span className="text-xs text-slate-300">{label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Status */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
              Status (line style)
            </p>
            <div className="space-y-1.5">
              {[
                { label: "Deployed / Lit", style: "solid",  color: "#32C850" },
                { label: "Under Construction", style: "dash-short", color: "#FFC800" },
                { label: "Planned", style: "dash-long", color: "#8C8C8C" },
              ].map(({ label, style, color }) => (
                <div key={label} className="flex items-center gap-2">
                  <span className="inline-block w-8 h-1.5 flex-shrink-0 relative">
                    {style === "solid" ? (
                      <span className="absolute inset-0 rounded-full" style={{ background: color }} />
                    ) : (
                      <span
                        className="absolute inset-0 rounded-full"
                        style={{
                          background: `repeating-linear-gradient(90deg, ${color} 0px, ${color} ${style === "dash-short" ? "4px" : "3px"}, transparent ${style === "dash-short" ? "4px" : "3px"}, transparent ${style === "dash-short" ? "8px" : "9px"})`,
                        }}
                      />
                    )}
                  </span>
                  <span className="text-xs text-slate-300">{label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Node types */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
              Nodes
            </p>
            <div className="space-y-1.5">
              {[
                { label: "IXP",             color: "#00E6FF", text: "IX", tip: "Internet Exchange Point — neutral facility where networks interconnect and exchange traffic." },
                { label: "Data Center",     color: "#A855F7", text: "DC", tip: "Colocation facility housing servers, routers, and cross-connects for multiple operators." },
                { label: "Landing Station", color: "#F59E0B", text: "LS", tip: "Coastal facility where a submarine cable comes ashore and connects to the terrestrial network." },
                { label: "PoP",             color: "#6366F1", text: "P",  tip: "Point of Presence — local access node where an operator's network reaches a city or region." },
              ].map(({ label, color, text, tip }) => (
                <div key={label} className="group relative flex items-center gap-2 cursor-default">
                  <span
                    className="inline-flex items-center justify-center w-5 h-5 rounded-full flex-shrink-0 text-white font-bold"
                    style={{ background: color, fontSize: "8px" }}
                  >
                    {text}
                  </span>
                  <span className="text-xs text-slate-300">{label}</span>
                  {/* Tooltip */}
                  <div className="pointer-events-none absolute left-0 bottom-full mb-2 z-50
                                  w-52 px-2.5 py-2 rounded-lg text-xs text-slate-200 leading-snug
                                  bg-[rgba(13,17,28,0.98)] border border-white/15 shadow-xl
                                  opacity-0 group-hover:opacity-100 transition-opacity duration-150">
                    {tip}
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
