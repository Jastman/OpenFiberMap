/**
 * Toolbar.tsx — Floating toolbar with zoom-to-region, 3D/2D toggle,
 * underground view, and dark/light mode.
 */

import type { Region } from "@/types";

interface Props {
  is3D: boolean;
  underground: boolean;
  onToggle3D: () => void;
  onToggleUnderground: () => void;
  onZoomRegion: (region: Region | "global") => void;
}

// ─── Icon button ──────────────────────────────────────────────────────────────

function IconBtn({
  onClick, active = false, title, children,
}: {
  onClick: () => void;
  active?: boolean;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`flex items-center justify-center w-9 h-9 rounded-lg transition-all text-sm font-medium ${
        active
          ? "bg-sky-600 text-white shadow-inner"
          : "bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white"
      }`}
    >
      {children}
    </button>
  );
}

// ─── Region quick-zoom buttons ────────────────────────────────────────────────

const REGIONS: { key: Region | "global"; emoji: string; label: string }[] = [
  { key: "global",      emoji: "🌍", label: "Global view" },
  { key: "africa",      emoji: "🌍", label: "Africa" },
  { key: "americas",    emoji: "🌎", label: "Americas" },
  { key: "europe",      emoji: "🌍", label: "Europe" },
  { key: "asia-pacific",emoji: "🌏", label: "Asia–Pacific" },
];

// ─── Main component ───────────────────────────────────────────────────────────

export default function Toolbar({
  is3D, underground, onToggle3D, onToggleUnderground, onZoomRegion,
}: Props) {
  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 flex items-center gap-1.5
                    bg-[rgba(13,17,28,0.95)] border border-white/10 rounded-2xl px-3 py-2 shadow-panel
                    backdrop-blur-sm">

      {/* Region quick-zoom */}
      <div className="flex items-center gap-1 pr-2 border-r border-white/10">
        {REGIONS.map(({ key, emoji, label }) => (
          <button
            key={key}
            onClick={() => onZoomRegion(key)}
            title={label}
            className="px-2 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white
                       hover:bg-slate-700 transition-all whitespace-nowrap"
          >
            {key === "global" ? (
              <span className="flex items-center gap-1">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" strokeWidth="2"/>
                  <path strokeLinecap="round" strokeWidth="2"
                    d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                </svg>
                Global
              </span>
            ) : (
              label
            )}
          </button>
        ))}
      </div>

      {/* 3D / 2D toggle */}
      <div className="flex items-center gap-1 px-2 border-r border-white/10">
        <IconBtn onClick={onToggle3D} active={is3D} title="Toggle 3D globe / 2D map">
          {is3D ? "3D" : "2D"}
        </IconBtn>
      </div>

      {/* Underground toggle */}
      <div className="flex items-center gap-1">
        <IconBtn onClick={onToggleUnderground} active={underground} title="Toggle underground / translucent terrain">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M3 7h18M3 12h18M3 17h18" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M7 17v2m4-2v4m4-4v1" opacity={underground ? 1 : 0.4} />
          </svg>
        </IconBtn>
        {underground && (
          <span className="text-xs text-amber-400 font-medium animate-pulse px-1">
            Underground
          </span>
        )}
      </div>
    </div>
  );
}
