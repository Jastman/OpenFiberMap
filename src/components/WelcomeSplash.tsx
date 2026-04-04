/**
 * WelcomeSplash.tsx — First-visit modal explaining what OpenFiberMap is.
 * Shown once per session (suppressed if user arrived via a share link).
 */

import { useEffect } from "react";

interface Props {
  onClose: () => void;
}

export default function WelcomeSplash({ onClose }: Props) {
  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="absolute inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(7,10,18,0.85)", backdropFilter: "blur(6px)" }}
    >
      <div className="relative w-full max-w-lg rounded-2xl border border-white/10 shadow-2xl overflow-hidden"
           style={{ background: "rgba(13,17,28,0.97)" }}>

        {/* Header stripe */}
        <div className="px-8 pt-8 pb-5">
          <div className="flex items-center gap-3 mb-5">
            {/* Fiber icon */}
            <span className="text-2xl">🌐</span>
            <h1 className="text-xl font-bold text-white tracking-tight">OpenFiberMap</h1>
          </div>

          <p className="text-slate-300 text-sm leading-relaxed mb-3">
            Terrestrial fiber infrastructure — the backbone routes, conduits, and peering
            points that carry internet traffic across continents — has no unified public
            map. Submarine cables are comprehensively documented, but on-land routes are
            fragmented across national regulatory filings, operator disclosures, and
            crowdsourced contributions with inconsistent coverage and no common schema.
          </p>
          <p className="text-slate-300 text-sm leading-relaxed mb-3">
            OpenFiberMap aggregates open-licensed datasets (AfTerFibre, OFDS, PeeringDB,
            and others) into a single interactive globe, visualizing routes by capacity
            tier, operational status, and operator. Coverage is densest in Africa and
            select countries where structured open data exists.
          </p>
          <p className="text-slate-400 text-xs leading-relaxed">
            Geometries are approximate — many routes are digitized from public maps rather
            than authoritative records. Click any route or node to inspect its metadata.
          </p>
        </div>

        {/* Divider */}
        <div className="border-t border-white/10 mx-0" />

        {/* Data source pills */}
        <div className="px-8 py-4">
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Open data sources</p>
          <div className="flex flex-wrap gap-2">
            {[
              "AfTerFibre (NSRC)",
              "OFDS-datasets",
              "PeeringDB",
              "Submarine Cable Map",
              "RNP Brazil",
            ].map((s) => (
              <span key={s}
                className="px-2.5 py-1 rounded-full text-xs bg-white/5 text-slate-400 border border-white/10">
                {s}
              </span>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-8 pb-8 pt-2 flex items-center gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 active:bg-cyan-600
                       text-sm font-semibold text-slate-900 transition-colors"
          >
            Explore the map
          </button>
          <a
            href="https://github.com/Jastman/OpenFiberMap"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2.5 rounded-xl border border-white/10 text-xs text-slate-400
                       hover:text-slate-200 hover:border-white/20 transition-colors whitespace-nowrap"
          >
            View on GitHub
          </a>
        </div>
      </div>
    </div>
  );
}
