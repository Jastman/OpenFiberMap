/**
 * useShareUrl.ts — Encode/decode the current map view state into the URL hash.
 *
 * Hash format: #r=africa&s=deployed&c=high&q=mainone&lat=-1.29&lon=36.82&z=5
 *
 * This lets users copy the URL from the browser address bar and share a
 * pre-filtered, pre-positioned view of the map.
 */

import { useEffect, useCallback } from "react";
import type { FilterState, Region, FiberStatus, CapacityClass } from "@/types";

interface ViewPosition {
  lat: number;
  lon: number;
  alt: number; // camera altitude in metres
}

interface ShareState {
  filters: FilterState;
  position?: ViewPosition;
}

// ─── Encode ───────────────────────────────────────────────────────────────────

export function encodeShareHash(state: ShareState): string {
  const params = new URLSearchParams();
  const { filters, position } = state;

  if (filters.region       !== "all") params.set("r", filters.region);
  if (filters.operator     !== "all") params.set("op", filters.operator);
  if (filters.status       !== "all") params.set("s", filters.status);
  if (filters.capacityClass !== "all") params.set("c", filters.capacityClass);
  if (filters.searchQuery)            params.set("q", filters.searchQuery);

  if (position) {
    params.set("lat", position.lat.toFixed(4));
    params.set("lon", position.lon.toFixed(4));
    params.set("alt", Math.round(position.alt).toString());
  }

  const str = params.toString();
  return str ? `#${str}` : "";
}

// ─── Decode ───────────────────────────────────────────────────────────────────

export function decodeShareHash(): { filters: Partial<FilterState>; position?: ViewPosition } {
  const hash = window.location.hash.slice(1); // strip leading #
  if (!hash) return { filters: {} };

  const params = new URLSearchParams(hash);

  const filters: Partial<FilterState> = {};
  const r  = params.get("r");
  const op = params.get("op");
  const s  = params.get("s");
  const c  = params.get("c");
  const q  = params.get("q");

  if (r)  filters.region        = r as Region;
  if (op) filters.operator      = op;
  if (s)  filters.status        = s as FiberStatus;
  if (c)  filters.capacityClass = c as CapacityClass;
  if (q)  filters.searchQuery   = q;

  let position: ViewPosition | undefined;
  const lat = parseFloat(params.get("lat") ?? "");
  const lon = parseFloat(params.get("lon") ?? "");
  const alt = parseFloat(params.get("alt") ?? "");
  if (!isNaN(lat) && !isNaN(lon)) {
    position = { lat, lon, alt: isNaN(alt) ? 2_000_000 : alt };
  }

  return { filters, position };
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useShareUrl(
  filters: FilterState,
  getPosition: () => ViewPosition | undefined,
) {
  // Keep hash in sync with filter state (debounced via effect)
  useEffect(() => {
    const hash = encodeShareHash({ filters });
    const newUrl = window.location.pathname + window.location.search + hash;
    window.history.replaceState(null, "", newUrl || window.location.pathname);
  }, [filters]);

  const copyShareLink = useCallback(async (): Promise<boolean> => {
    const position = getPosition();
    const hash = encodeShareHash({ filters, position });
    const url = window.location.origin + window.location.pathname + hash;
    try {
      await navigator.clipboard.writeText(url);
      return true;
    } catch {
      // Fallback for browsers without clipboard API
      const input = document.createElement("input");
      input.value = url;
      document.body.appendChild(input);
      input.select();
      document.execCommand("copy");
      document.body.removeChild(input);
      return true;
    }
  }, [filters, getPosition]);

  return { copyShareLink };
}
