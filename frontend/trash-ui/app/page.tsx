"use client";

import Link from "next/link";
import { useState } from "react";
import { Sidebar } from "./components/Sidebar";

const stats = [
  { label: "CO2 SAVED", icon: "☁️", value: "750g" },
  { label: "TREES SAVED", icon: "🌱", value: "~0" },
  { label: "ITEMS RECYCLED", icon: "♻️", value: "165" },
];

const scanItems = [
  { icon: "📄", label: "Paper", hint: "Documents, cartons, and dry paper waste." },
  { icon: "📦", label: "Carton", hint: "Boxes and clean packaging material." },
  { icon: "🧴", label: "Plastic", hint: "Bottles, containers, and plastic packaging." },
  { icon: "🖊️", label: "Metal", hint: "Cans, wires, and small metal items." },
  { icon: "⚡", label: "E-waste", hint: "Chargers, cables, and electronic pieces." },
  { icon: "🔋", label: "Battery", hint: "Cells and battery-powered waste." },
  { icon: "🖥️", label: "Device", hint: "Screens, keyboards, and accessories." },
  { icon: "👕", label: "Textile", hint: "Clothing, fabric, and reusable cloth." },
  { icon: "🍎", label: "Organic", hint: "Food scraps, peels, and leftovers." },
  { icon: "🌿", label: "Garden", hint: "Leaves, stems, and yard trimmings." },
];

export default function Home() {
  const [selectedScan, setSelectedScan] = useState(scanItems[0]);
  const [botExpanded, setBotExpanded] = useState(false);

  return (
    <main className="eco-shell">
      <Sidebar active="dashboard" />

      <section className={`dashboard-surface ${botExpanded ? "bot-expanded" : "bot-collapsed"}`}>
        <div className="mountain-layer layer-back" />
        <div className="mountain-layer layer-front" />

        <div className="dashboard-main">
          <div className="dashboard-top">
            <header className="dashboard-header">
              <p>MAIN DASHBOARD</p>
              <h1>Welcome back!</h1>
              <span>Let&apos;s keep making a positive impact on our planet.</span>
            </header>

            <section className="scan-hero" aria-labelledby="scan-hero-title">
              <div>
                <span className="hero-kicker">⌖ Identify trash</span>
                <h2 id="scan-hero-title">Scan an item now</h2>
                <p>Use camera or upload a photo to get the trash type and category.</p>
              </div>
              <Link className="hero-cta" href="/scan">
                Scan & Identify
              </Link>
            </section>
          </div>

          <div className="stats-grid">
            {stats.map((stat) => (
              <article className="metric-card" key={stat.label}>
                <p>{stat.label}</p>
                <span>{stat.icon}</span>
                <strong>{stat.value}</strong>
              </article>
            ))}
          </div>

          <section className="scan-board" aria-label="Trash scan shortcuts">
            <div className="scan-board-heading">
              <div>
                <h2>Quick scan</h2>
                <p>Pick a common item type, then open the scanner.</p>
              </div>
              <Link href="/scan">Start scan</Link>
            </div>

            <div className="quick-scan-layout">
              <div className="scan-tile-grid" aria-label="Quick scan item types">
                {scanItems.map((item) => (
                  <button
                    className={`scan-tile ${selectedScan.label === item.label ? "is-selected" : ""}`}
                    type="button"
                    key={item.label}
                    onClick={() => setSelectedScan(item)}
                    aria-label={`Preview ${item.label}`}
                    aria-pressed={selectedScan.label === item.label}
                  >
                    <span>{item.icon}</span>
                    <small>{item.label}</small>
                  </button>
                ))}
              </div>

              <article className="scan-preview" aria-live="polite">
                <span>{selectedScan.icon}</span>
                <div>
                  <p>Selected item</p>
                  <h3>{selectedScan.label}</h3>
                  <small>{selectedScan.hint}</small>
                </div>
                <Link
                  href="/scan"
                  aria-label={`Scan ${selectedScan.label}`}
                >
                  Scan this
                </Link>
              </article>
            </div>
          </section>

          <div className="bottom-dock-container" aria-label="Quick actions">
            <div className="bottom-dock">
              <Link href="/chat" aria-label="Open chatbot" className="dock-item dock-item-left">
                <div className="dock-item-inner">
                  <svg viewBox="0 0 64 64" role="img">
                    <rect className="icon-bg" x="6" y="6" width="52" height="52" rx="12" />
                    <path className="icon-stroke" d="M32 16v7M27 16h10" />
                    <rect className="icon-fill" x="18" y="25" width="28" height="20" rx="10" />
                    <path className="icon-stroke" d="M18 33h-4M50 33h-4" />
                    <circle className="bot-eye" cx="28" cy="35" r="2.3" />
                    <circle className="bot-eye" cx="36" cy="35" r="2.3" />
                  </svg>
                </div>
              </Link>
              
              <Link href="/" aria-label="Home" className="dock-item">
                <div className="dock-item-inner">
                  <svg viewBox="0 0 64 64" role="img">
                    <rect className="icon-bg" x="6" y="6" width="52" height="52" rx="12" />
                    <rect className="icon-cell dark" x="16" y="16" width="15" height="15" rx="2" />
                    <rect className="icon-cell" x="33" y="16" width="15" height="15" rx="2" />
                    <rect className="icon-cell dark" x="16" y="33" width="15" height="15" rx="2" />
                    <rect className="icon-cell light" x="33" y="33" width="15" height="15" rx="2" />
                  </svg>
                </div>
              </Link>
              
              <Link href="/scan" aria-label="Scan" className="dock-item">
                <div className="dock-item-inner">
                  <svg viewBox="0 0 64 64" role="img">
                    <rect className="icon-bg" x="6" y="6" width="52" height="52" rx="12" />
                    <path className="icon-stroke" d="M18 27v-8h8M38 19h8v8M46 38v8h-8M26 46h-8v-8" />
                    <rect className="icon-mark" x="26" y="26" width="12" height="12" rx="4" />
                  </svg>
                </div>
              </Link>
              
              <Link href="/scan" aria-label="Scan item" className="dock-item dock-item-center">
                <div className="dock-item-inner dock-center-inner">
                  <svg viewBox="0 0 64 64" role="img">
                    <path className="icon-stroke-center" d="M20 32h24M32 20v24" />
                  </svg>
                </div>
              </Link>
              
            </div>
          </div>
        </div>

        <aside className={`eco-bot ${botExpanded ? "is-expanded" : "is-collapsed"}`}>
          <div className="bot-header">
            <h2>
              <span>🤖</span>
              <span>EcoBot</span>
            </h2>
            <button
              className="bot-toggle"
              type="button"
              onClick={() => setBotExpanded((current) => !current)}
              aria-expanded={botExpanded}
              aria-label={botExpanded ? "Collapse EcoBot" : "Expand EcoBot"}
            >
              {botExpanded ? "←" : "→"}
            </button>
          </div>

          <div className="bot-content">
            <div className="bot-prompts">
              <button type="button">♻️ How do I recycle this?</button>
              <button type="button">📍 Where is nearest drop point?</button>
              <button type="button">🔎 What can be recycled?</button>
            </div>
            <div className="bot-input">
              <span />
              <button type="button" aria-label="Send message">
                ➤
              </button>
            </div>
          </div>
        </aside>
      </section>
    </main>
  );
}
