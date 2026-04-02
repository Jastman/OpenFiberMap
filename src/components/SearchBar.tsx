/**
 * SearchBar.tsx — Search by operator name, city, or lat,lon coordinates.
 * Positioned top-center over the globe.
 */

import { useState, useCallback, useRef } from "react";

interface Props {
  onSearch: (query: string) => void;
  onGeoJump: (lon: number, lat: number) => void;
}

// Detect "lat, lon" pattern
function parseCoords(text: string): [number, number] | null {
  const m = text.trim().match(/^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/);
  if (!m) return null;
  const lat = parseFloat(m[1]);
  const lon = parseFloat(m[2]);
  if (lat < -90 || lat > 90 || lon < -180 || lon > 180) return null;
  return [lon, lat];
}

export default function SearchBar({ onSearch, onGeoJump }: Props) {
  const [value, setValue] = useState("");
  const [hint, setHint] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const v = e.target.value;
      setValue(v);
      const coords = parseCoords(v);
      setHint(coords ? `Jump to ${coords[1].toFixed(4)}, ${coords[0].toFixed(4)}` : "");
      onSearch(coords ? "" : v);
    },
    [onSearch]
  );

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const coords = parseCoords(value);
      if (coords) {
        onGeoJump(coords[0], coords[1]);
        setValue("");
        setHint("");
        inputRef.current?.blur();
      }
    },
    [value, onGeoJump]
  );

  const handleClear = useCallback(() => {
    setValue("");
    setHint("");
    onSearch("");
    inputRef.current?.focus();
  }, [onSearch]);

  return (
    <form
      onSubmit={handleSubmit}
      className="absolute top-4 left-1/2 -translate-x-1/2 z-20 w-80 max-w-[90vw]"
    >
      <div className="relative">
        {/* Search icon */}
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none"
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>

        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={handleChange}
          placeholder="Search operator, city, or lat, lon…"
          className="w-full bg-[rgba(13,17,28,0.96)] border border-white/15
                     text-slate-100 placeholder-slate-600 text-sm
                     rounded-xl pl-9 pr-8 py-2.5
                     focus:outline-none focus:ring-1 focus:ring-sky-500 focus:border-sky-500/50
                     shadow-panel backdrop-blur-sm transition-all"
        />

        {value && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-2.5 top-1/2 -translate-y-1/2
                       text-slate-500 hover:text-white transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {hint && (
        <button
          type="submit"
          className="mt-1 w-full text-left text-xs text-sky-400 bg-[rgba(13,17,28,0.96)]
                     border border-white/10 rounded-lg px-3 py-2 hover:bg-slate-800
                     transition-all shadow-panel"
        >
          📍 {hint} — press Enter to jump
        </button>
      )}
    </form>
  );
}
