/**
 * AboutModal.tsx — Full-screen modal with data sources, methodology,
 * limitations disclaimer, and open-source attribution.
 */

import { useEffect } from "react";

interface Props {
  onClose: () => void;
}

const SOURCES = [
  {
    name: "AfTerFibre (NSRC)",
    url: "https://afterfibre.nsrc.org",
    license: "CC-BY-4.0",
    region: "Africa",
    description:
      "The most authoritative open dataset for Africa terrestrial fiber backbone routes. Maintained by the Network Startup Resource Center (NSRC).",
  },
  {
    name: "OFDS-datasets (stevesong)",
    url: "https://github.com/stevesong/OFDS-datasets",
    license: "CC-BY-4.0",
    region: "Global",
    description:
      "A collection of fiber optic network maps in Open Fibre Data Standard (OFDS) format. Covers 20+ African countries, Brazil, Canada, and others.",
  },
  {
    name: "PeeringDB",
    url: "https://www.peeringdb.com",
    license: "CC0-1.0",
    region: "Global",
    description:
      "The authoritative directory of Internet Exchanges (IXPs) and carrier-neutral data center facilities worldwide.",
  },
  {
    name: "Submarine Cable Map (TeleGeography)",
    url: "https://www.submarinecablemap.com",
    license: "CC-BY-SA-4.0",
    region: "Global",
    description:
      "Landing station locations where submarine fiber cables connect to terrestrial backhaul networks.",
  },
  {
    name: "RNP (Rede Nacional de Pesquisa)",
    url: "https://www.rnp.br/en/network/infrastructure",
    license: "CC-BY-4.0",
    region: "Brazil",
    description:
      "Brazil's national research and education network backbone, connecting all 27 state capitals and major universities.",
  },
  {
    name: "ANATEL Open Data",
    url: "https://dados.gov.br",
    license: "CC-BY-4.0",
    region: "Brazil",
    description:
      "Brazilian telecom regulator open data portal — licensed operator infrastructure reports.",
  },
  {
    name: "OpenStreetMap",
    url: "https://www.openstreetmap.org",
    license: "ODbL-1.0",
    region: "Global",
    description:
      "Crowd-sourced geographic data including fiber optic ducts, telecom exchanges, and data centers tagged by the OSM community.",
  },
  {
    name: "Open Fibre Data Standard (OFDS)",
    url: "https://open-fibre-data-standard.readthedocs.io",
    license: "Apache-2.0",
    region: "Specification",
    description:
      "The schema specification that OpenFiberMap's data model is aligned with. Developed by Open Data Services Co-operative.",
  },
];

const LIMITATIONS = [
  "Route geometries are often **approximate** — traced from public maps, not surveyed. Actual cable alignments may differ significantly.",
  "**Capacity figures** are design capacities, not current utilization. Many older routes have no capacity data.",
  "**Coverage is incomplete.** Large regions (Central Asia, much of Latin America, Oceania) have very sparse or no data.",
  "**Status** (deployed vs. planned) may be outdated. Data is refreshed periodically but not in real time.",
  "**Private operator data** is not included — only publicly disclosed or openly licensed routes appear.",
  "OpenFiberMap is **not authoritative** for any operational or planning purpose. Always verify with primary sources.",
];

export default function AboutModal({ onClose }: Props) {
  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.75)", backdropFilter: "blur(6px)" }}
    >
      <div
        className="relative w-full max-w-3xl max-h-[90vh] flex flex-col
                   bg-[rgba(13,17,28,0.99)] border border-white/10 rounded-2xl shadow-panel overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 flex-shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🌐</span>
            <div>
              <h2 className="text-white font-bold text-lg">About OpenFiberMap</h2>
              <p className="text-slate-500 text-xs">Free, open-source global fiber optic network visualization</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors p-2 rounded-lg hover:bg-white/10"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 px-6 py-5 space-y-8">

          {/* What is it */}
          <section>
            <p className="text-slate-300 text-sm leading-relaxed">
              OpenFiberMap is a free, open-source interactive 3D visualization of the world's terrestrial
              fiber optic backbone infrastructure. It aggregates data from multiple open/public sources into
              a unified schema aligned with the{" "}
              <a href="https://open-fibre-data-standard.readthedocs.io" target="_blank" rel="noopener noreferrer"
                className="text-sky-400 hover:text-sky-300 underline underline-offset-2">
                Open Fibre Data Standard (OFDS)
              </a>{" "}
              and visualizes routes, nodes, IXPs, data centers, and submarine cable landing stations on a
              CesiumJS 3D globe.
            </p>
          </section>

          {/* Limitations */}
          <section>
            <h3 className="text-white font-semibold text-sm uppercase tracking-widest mb-3">
              ⚠️ Data Limitations
            </h3>
            <div className="bg-amber-950/30 border border-amber-500/20 rounded-xl p-4 space-y-2">
              {LIMITATIONS.map((lim, i) => (
                <div key={i} className="flex gap-2 text-sm text-amber-200/80">
                  <span className="text-amber-500 flex-shrink-0 mt-0.5">•</span>
                  <span dangerouslySetInnerHTML={{
                    __html: lim.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>"),
                  }} />
                </div>
              ))}
            </div>
          </section>

          {/* Data sources */}
          <section>
            <h3 className="text-white font-semibold text-sm uppercase tracking-widest mb-3">
              Data Sources & Attribution
            </h3>
            <div className="space-y-3">
              {SOURCES.map((src) => (
                <div key={src.name} className="border border-white/8 rounded-xl p-4 hover:border-white/15 transition-colors">
                  <div className="flex items-start justify-between gap-3 mb-1.5">
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sky-400 hover:text-sky-300 font-medium text-sm underline underline-offset-2"
                    >
                      {src.name}
                    </a>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="text-xs font-mono text-slate-500 bg-slate-800 px-2 py-0.5 rounded">
                        {src.license}
                      </span>
                      <span className="text-xs text-slate-600">{src.region}</span>
                    </div>
                  </div>
                  <p className="text-slate-400 text-xs leading-relaxed">{src.description}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Open source */}
          <section>
            <h3 className="text-white font-semibold text-sm uppercase tracking-widest mb-3">
              Open Source
            </h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              OpenFiberMap is released under the{" "}
              <strong className="text-slate-200">MIT License</strong>.
              The codebase is available on{" "}
              <a
                href="https://github.com/jastman/OpenFiberMap"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sky-400 hover:text-sky-300 underline underline-offset-2"
              >
                GitHub
              </a>. Contributions of new open datasets are welcome — see{" "}
              <a
                href="https://github.com/jastman/OpenFiberMap/blob/main/docs/CONTRIBUTING.md"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sky-400 hover:text-sky-300 underline underline-offset-2"
              >
                CONTRIBUTING.md
              </a>{" "}
              for how to add a new region via the OFDS pipeline.
            </p>
            <p className="text-slate-500 text-xs mt-2">
              Inspired by{" "}
              <a href="https://opengridworks.com" target="_blank" rel="noopener noreferrer"
                className="text-slate-400 hover:text-slate-300 underline underline-offset-2">
                OpenGridWorks
              </a>{" "}
              for electricity grids. Built with CesiumJS, React, Vite, and Tailwind CSS.
            </p>
          </section>

        </div>

        {/* Footer */}
        <div className="border-t border-white/10 px-6 py-3 flex-shrink-0 flex items-center justify-between">
          <span className="text-slate-600 text-xs">
            Data collected from public/open sources only. Never scrapes paywalled or private APIs.
          </span>
          <button
            onClick={onClose}
            className="text-sm text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700
                       px-4 py-1.5 rounded-lg transition-all"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
