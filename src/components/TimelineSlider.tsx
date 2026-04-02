/**
 * TimelineSlider.tsx — Year-range slider for filtering fiber spans by
 * construction_start / ready_for_service date.
 *
 * Shows only when the dataset contains spans with date information.
 * Collapsed by default; expands on click.
 *
 * Emits a { minYear, maxYear } window that the parent passes to filters.
 * Spans without dates always pass through (shown regardless).
 */

import { useState, useCallback } from "react";

export interface YearRange {
  min: number;
  max: number;
}

interface Props {
  range: YearRange;         // overall min/max in the dataset
  value: YearRange;         // currently selected window
  onChange: (v: YearRange) => void;
}

const THUMB_W = 16; // px, kept in sync with CSS

export default function TimelineSlider({ range, value, onChange }: Props) {
  const [open, setOpen] = useState(false);

  const totalSpan = range.max - range.min || 1;

  const handleMin = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const v = parseInt(e.target.value, 10);
      onChange({ min: Math.min(v, value.max - 1), max: value.max });
    },
    [value, onChange]
  );

  const handleMax = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const v = parseInt(e.target.value, 10);
      onChange({ min: value.min, max: Math.max(v, value.min + 1) });
    },
    [value, onChange]
  );

  const isFiltered = value.min !== range.min || value.max !== range.max;

  return (
    <div className="absolute bottom-20 left-1/2 -translate-x-1/2 z-20"
         style={{ marginBottom: "2.5rem" }}>
      <button
        onClick={() => setOpen((o) => !o)}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium
                    border transition-all shadow-panel backdrop-blur-sm ${
          isFiltered
            ? "bg-sky-900/60 border-sky-500/40 text-sky-300"
            : "bg-[rgba(13,17,28,0.92)] border-white/10 text-slate-400 hover:text-white"
        }`}
      >
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
        </svg>
        Timeline
        {isFiltered && (
          <span className="font-mono">{value.min}–{value.max}</span>
        )}
        <svg className={`w-3 h-3 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"/>
        </svg>
      </button>

      {open && (
        <div className="mt-1.5 bg-[rgba(13,17,28,0.97)] border border-white/10 rounded-xl
                        shadow-panel p-4 w-72">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Construction / service window
            </span>
            {isFiltered && (
              <button
                onClick={() => onChange(range)}
                className="text-xs text-amber-400 hover:text-amber-300"
              >
                Reset
              </button>
            )}
          </div>

          {/* Dual range track */}
          <div className="relative h-5 mb-2">
            {/* Background track */}
            <div className="absolute top-1/2 -translate-y-1/2 left-0 right-0 h-1.5 bg-slate-700 rounded-full" />

            {/* Active segment */}
            <div
              className="absolute top-1/2 -translate-y-1/2 h-1.5 bg-sky-500 rounded-full"
              style={{
                left: `${((value.min - range.min) / totalSpan) * 100}%`,
                right: `${((range.max - value.max) / totalSpan) * 100}%`,
              }}
            />

            {/* Min thumb */}
            <input
              type="range"
              min={range.min}
              max={range.max}
              value={value.min}
              onChange={handleMin}
              className="absolute inset-0 w-full appearance-none bg-transparent cursor-pointer
                         [&::-webkit-slider-thumb]:appearance-none
                         [&::-webkit-slider-thumb]:w-4
                         [&::-webkit-slider-thumb]:h-4
                         [&::-webkit-slider-thumb]:rounded-full
                         [&::-webkit-slider-thumb]:bg-sky-400
                         [&::-webkit-slider-thumb]:border-2
                         [&::-webkit-slider-thumb]:border-slate-900
                         [&::-webkit-slider-thumb]:cursor-pointer"
              style={{ zIndex: value.min > range.max - 5 ? 5 : 3 }}
            />

            {/* Max thumb */}
            <input
              type="range"
              min={range.min}
              max={range.max}
              value={value.max}
              onChange={handleMax}
              className="absolute inset-0 w-full appearance-none bg-transparent cursor-pointer
                         [&::-webkit-slider-thumb]:appearance-none
                         [&::-webkit-slider-thumb]:w-4
                         [&::-webkit-slider-thumb]:h-4
                         [&::-webkit-slider-thumb]:rounded-full
                         [&::-webkit-slider-thumb]:bg-sky-400
                         [&::-webkit-slider-thumb]:border-2
                         [&::-webkit-slider-thumb]:border-slate-900
                         [&::-webkit-slider-thumb]:cursor-pointer"
              style={{ zIndex: 4 }}
            />
          </div>

          {/* Labels */}
          <div className="flex justify-between text-xs font-mono text-slate-400 mt-1">
            <span>{value.min}</span>
            <span className="text-slate-600">→</span>
            <span>{value.max}</span>
          </div>

          <p className="text-xs text-slate-600 mt-2 leading-relaxed">
            Shows spans whose construction or service date falls in this window.
            Spans without date data are always shown.
          </p>
        </div>
      )}
    </div>
  );
}
