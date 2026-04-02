/**
 * App.tsx — Root component. Owns all state, wires together:
 *   CesiumViewer ← data + filter state
 *   Sidebar      ← layer/filter controls
 *   InfoPanel    ← selected feature details
 *   Toolbar      ← view mode controls
 *   SearchBar    ← search / geo-jump
 *   Legend       ← colour legend
 */

import { useState, useRef, useCallback } from "react";
import CesiumViewer, { type CesiumViewerHandle } from "@/components/CesiumViewer";
import Sidebar    from "@/components/Sidebar";
import InfoPanel  from "@/components/InfoPanel";
import Toolbar    from "@/components/Toolbar";
import SearchBar  from "@/components/SearchBar";
import Legend     from "@/components/Legend";
import { useFilters } from "@/hooks/useFilters";
import type { SelectedFeature, Region } from "@/types";

// Read Cesium ion token from env (set VITE_CESIUM_ION_TOKEN= in .env.local)
const CESIUM_TOKEN = import.meta.env.VITE_CESIUM_ION_TOKEN as string | undefined;

export default function App() {
  const viewerRef = useRef<CesiumViewerHandle>(null);

  // ── Layer visibility ──────────────────────────────────────────────────────
  const [showSpans, setShowSpans] = useState(true);
  const [showNodes, setShowNodes] = useState(true);

  // ── Filters ───────────────────────────────────────────────────────────────
  const {
    filters,
    setRegion, setOperator, setStatus, setCapacityClass, setSearchQuery, reset,
  } = useFilters();

  // ── View state ────────────────────────────────────────────────────────────
  const [is3D, setIs3D]               = useState(true);
  const [underground, setUnderground] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // ── Selected feature ──────────────────────────────────────────────────────
  const [selectedFeature, setSelectedFeature] = useState<SelectedFeature | null>(null);

  // ── Callbacks ─────────────────────────────────────────────────────────────

  const handleToggle3D = useCallback(() => {
    const next = !is3D;
    setIs3D(next);
    viewerRef.current?.set3DMode(next);
  }, [is3D]);

  const handleToggleUnderground = useCallback(() => {
    const next = !underground;
    setUnderground(next);
    viewerRef.current?.setUnderground(next);
  }, [underground]);

  const handleZoomRegion = useCallback((region: Region | "global") => {
    viewerRef.current?.zoomToRegion(region);
  }, []);

  const handleGeoJump = useCallback((lon: number, lat: number) => {
    viewerRef.current?.zoomToFeature(lon, lat);
  }, []);

  const handleFeatureSelect = useCallback((f: SelectedFeature | null) => {
    setSelectedFeature(f);
  }, []);

  const handleCloseInfo = useCallback(() => setSelectedFeature(null), []);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="relative w-full h-full overflow-hidden select-none">

      {/* Globe — full-screen base layer */}
      <CesiumViewer
        ref={viewerRef}
        filters={filters}
        showSpans={showSpans}
        showNodes={showNodes}
        onFeatureSelect={handleFeatureSelect}
        cesiumIonToken={CESIUM_TOKEN}
      />

      {/* Sidebar */}
      <Sidebar
        filters={filters}
        showSpans={showSpans}
        showNodes={showNodes}
        onShowSpans={setShowSpans}
        onShowNodes={setShowNodes}
        onRegion={setRegion}
        onOperator={setOperator}
        onStatus={setStatus}
        onCapacity={setCapacityClass}
        onReset={reset}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen((o) => !o)}
      />

      {/* Search bar — top center */}
      <SearchBar onSearch={setSearchQuery} onGeoJump={handleGeoJump} />

      {/* Info panel — right side, slides in when feature selected */}
      {selectedFeature && (
        <InfoPanel feature={selectedFeature} onClose={handleCloseInfo} />
      )}

      {/* Legend — bottom right */}
      <Legend />

      {/* Toolbar — bottom center */}
      <Toolbar
        is3D={is3D}
        underground={underground}
        onToggle3D={handleToggle3D}
        onToggleUnderground={handleToggleUnderground}
        onZoomRegion={handleZoomRegion}
      />

      {/* Loading indicator */}
      <LoadingBanner />
    </div>
  );
}

// ─── Transient loading banner (auto-hides after 4s) ───────────────────────────

function LoadingBanner() {
  const [visible, setVisible] = useState(true);

  if (!visible) return null;

  return (
    <div
      className="absolute bottom-20 left-1/2 -translate-x-1/2 z-30
                 bg-[rgba(13,17,28,0.95)] border border-white/10 rounded-xl
                 px-4 py-2 text-xs text-slate-400 shadow-panel
                 animate-fiber-pulse pointer-events-none"
      onAnimationIteration={(e) => {
        // After ~4 pulses, fade out
        const el = e.currentTarget as HTMLElement;
        const count = parseInt(el.dataset.count ?? "0") + 1;
        el.dataset.count = String(count);
        if (count >= 3) setVisible(false);
      }}
    >
      Loading fiber network data…
    </div>
  );
}
