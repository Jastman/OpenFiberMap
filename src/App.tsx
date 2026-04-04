/**
 * App.tsx — Root component. Owns all state and wires together:
 *   CesiumViewer  ← data + filter state
 *   Sidebar       ← layer/filter controls + About button
 *   InfoPanel     ← selected feature details
 *   Toolbar       ← view mode controls
 *   SearchBar     ← search / geo-jump
 *   Legend        ← colour legend
 *   AboutModal    ← data sources + limitations
 *   ShareButton   ← copy current view URL
 *   TimelineSlider← year-range filter for planned builds
 */

import { useState, useRef, useCallback, useEffect } from "react";
import CesiumViewer, { type CesiumViewerHandle } from "@/components/CesiumViewer";
import Sidebar        from "@/components/Sidebar";
import InfoPanel      from "@/components/InfoPanel";
import Toolbar        from "@/components/Toolbar";
import SearchBar      from "@/components/SearchBar";
import Legend         from "@/components/Legend";
import HoverTooltip   from "@/components/HoverTooltip";
import AboutModal     from "@/components/AboutModal";
import WelcomeSplash  from "@/components/WelcomeSplash";
import ShareButton    from "@/components/ShareButton";
import TimelineSlider, { type YearRange } from "@/components/TimelineSlider";
import { useFilters }   from "@/hooks/useFilters";
import { useShareUrl, decodeShareHash } from "@/hooks/useShareUrl";
import { useMobile }    from "@/hooks/useMobile";
import type { SelectedFeature, Region } from "@/types";

// Read Cesium ion token from env (set VITE_CESIUM_ION_TOKEN= in .env.local)
const CESIUM_TOKEN      = import.meta.env.VITE_CESIUM_ION_TOKEN as string | undefined;
const GOOGLE_MAPS_KEY   = import.meta.env.VITE_GOOGLE_MAPS_API_KEY as string | undefined;

// Dataset year extent — update when adding newer planned-build data
const TIMELINE_RANGE: YearRange = { min: 2000, max: 2030 };

export default function App() {
  const viewerRef = useRef<CesiumViewerHandle>(null);
  const isMobile  = useMobile();

  // ── Layer visibility ──────────────────────────────────────────────────────
  const [showSpans, setShowSpans] = useState(true);
  const [showNodes, setShowNodes] = useState(true);

  // ── Filters ───────────────────────────────────────────────────────────────
  const {
    filters,
    setRegion, setOperator, setStatus, setCapacityClass, setSearchQuery, reset,
  } = useFilters();

  // ── View state ────────────────────────────────────────────────────────────
  const [is3D,       setIs3D]       = useState(true);
  const [underground, setUnderground] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile); // collapsed on mobile by default

  // ── Modal / overlay state ─────────────────────────────────────────────────
  const [showAbout,    setShowAbout]    = useState(false);
  // Show splash on first visit; suppress if user arrived via a share link
  const [showSplash, setShowSplash] = useState(() => !window.location.hash.includes("r="));
  const [selectedFeature, setSelectedFeature] = useState<SelectedFeature | null>(null);
  // Hover tooltip (desktop only)
  const [hoverFeature, setHoverFeature] = useState<SelectedFeature | null>(null);
  const [hoverPos,     setHoverPos]     = useState<{x: number; y: number} | null>(null);

  // ── Timeline ──────────────────────────────────────────────────────────────
  const [timelineValue, setTimelineValue] = useState<YearRange>(TIMELINE_RANGE);

  // ── Share URL ─────────────────────────────────────────────────────────────
  const getPosition = useCallback(() => undefined, []); // extend later with Cesium camera read
  const { copyShareLink } = useShareUrl(filters, getPosition);

  // ── Restore state from URL hash on first load ─────────────────────────────
  useEffect(() => {
    const { filters: hf, position } = decodeShareHash();
    if (hf.region)        setRegion(hf.region as Region);
    if (hf.operator)      setOperator(hf.operator);
    if (hf.status)        setStatus(hf.status as Parameters<typeof setStatus>[0]);
    if (hf.capacityClass) setCapacityClass(hf.capacityClass as Parameters<typeof setCapacityClass>[0]);
    if (hf.searchQuery)   setSearchQuery(hf.searchQuery);
    if (position) {
      // Defer until viewer is mounted
      setTimeout(() => {
        viewerRef.current?.zoomToFeature(position.lon, position.lat);
      }, 800);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
    // Clear hover when clicking
    setHoverFeature(null);
    setHoverPos(null);
  }, []);

  const handleCloseInfo = useCallback(() => setSelectedFeature(null), []);

  const handleFeatureHover = useCallback((f: SelectedFeature | null, x: number, y: number) => {
    setHoverFeature(f);
    setHoverPos(f ? { x, y } : null);
  }, []);

  // Close info panel when clicking backdrop on mobile
  const handleGlobeClick = useCallback(() => {
    if (isMobile && sidebarOpen) setSidebarOpen(false);
  }, [isMobile, sidebarOpen]);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="relative w-full h-full overflow-hidden select-none">

      {/* Globe — full-screen base layer */}
      <div onClick={handleGlobeClick} className="absolute inset-0">
        <CesiumViewer
          ref={viewerRef}
          filters={filters}
          showSpans={showSpans}
          showNodes={showNodes}
          onFeatureSelect={handleFeatureSelect}
          onFeatureHover={isMobile ? undefined : handleFeatureHover}
          cesiumIonToken={CESIUM_TOKEN}
          googleMapsApiKey={GOOGLE_MAPS_KEY}
        />
      </div>

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
        onAbout={() => setShowAbout(true)}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen((o) => !o)}
      />

      {/* Top bar: Search + Share */}
      <div className={`absolute top-4 z-20 flex items-center gap-2 transition-all duration-300 ${
        sidebarOpen ? "left-80" : "left-10"
      } right-4`}>
        <div className="flex-1 max-w-sm">
          <SearchBar onSearch={setSearchQuery} onGeoJump={handleGeoJump} />
        </div>
        <div className="flex-shrink-0">
          <ShareButton onCopy={copyShareLink} />
        </div>
      </div>

      {/* Hover tooltip — desktop only, follows cursor */}
      {!isMobile && hoverFeature && hoverPos && !selectedFeature && (
        <HoverTooltip feature={hoverFeature} screenX={hoverPos.x} screenY={hoverPos.y} />
      )}

      {/* Info panel — right side */}
      {selectedFeature && (
        <InfoPanel feature={selectedFeature} onClose={handleCloseInfo} />
      )}

      {/* Legend — bottom right (above toolbar) */}
      {!isMobile && <Legend />}

      {/* Timeline slider — above toolbar */}
      <TimelineSlider
        range={TIMELINE_RANGE}
        value={timelineValue}
        onChange={setTimelineValue}
      />

      {/* Toolbar — bottom center */}
      <Toolbar
        is3D={is3D}
        underground={underground}
        onToggle3D={handleToggle3D}
        onToggleUnderground={handleToggleUnderground}
        onZoomRegion={handleZoomRegion}
      />

      {/* About modal */}
      {showAbout && (
        <AboutModal onClose={() => setShowAbout(false)} />
      )}

      {/* Welcome splash — shown on first visit */}
      {showSplash && (
        <WelcomeSplash onClose={() => setShowSplash(false)} />
      )}

      {/* Loading banner */}
      <LoadingBanner />

      {/* Mobile touch hint */}
      {isMobile && <MobileTouchHint />}
    </div>
  );
}

// ─── Loading banner (auto-hides) ─────────────────────────────────────────────

function LoadingBanner() {
  const [visible, setVisible] = useState(true);
  useEffect(() => {
    const t = setTimeout(() => setVisible(false), 6000);
    return () => clearTimeout(t);
  }, []);
  if (!visible) return null;
  return (
    <div className="absolute top-16 left-1/2 -translate-x-1/2 z-30 pointer-events-none
                    bg-[rgba(13,17,28,0.90)] border border-white/10 rounded-xl
                    px-4 py-2 text-xs text-slate-400 shadow-panel">
      Loading fiber network data…
    </div>
  );
}

// ─── Mobile touch hint (shown once) ──────────────────────────────────────────

function MobileTouchHint() {
  const [visible, setVisible] = useState(true);
  useEffect(() => {
    const t = setTimeout(() => setVisible(false), 4000);
    return () => clearTimeout(t);
  }, []);
  if (!visible) return null;
  return (
    <div className="absolute bottom-28 left-1/2 -translate-x-1/2 z-30 pointer-events-none
                    bg-[rgba(13,17,28,0.90)] border border-white/10 rounded-xl
                    px-4 py-2 text-xs text-slate-400 shadow-panel text-center">
      Pinch to zoom · Tap a route to inspect
    </div>
  );
}
