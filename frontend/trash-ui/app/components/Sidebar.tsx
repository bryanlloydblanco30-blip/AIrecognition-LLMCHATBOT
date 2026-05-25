"use client";

import Link from "next/link";

type NavKey = "dashboard" | "scan" | "chat";

const navItems: Array<{
  key: NavKey;
  label: string;
  href?: string;
  external?: boolean;
}> = [
  { key: "dashboard", label: "Dashboard", href: "/" },
  { key: "scan", label: "Scan & Identify", href: "/scan" },
  { key: "chat", label: "Chatbot", href: "http://localhost:3001", external: true },
];

export function Sidebar({ active }: { active: NavKey }) {
  return (
    <aside className="eco-sidebar" aria-label="Main navigation">
      <Link className="brand brand-link" href="/">
        <span className="brand-icon">🌿</span>
        <div>
          <strong>Group-6</strong>
          <span>Trash_Recognition</span>
        </div>
      </Link>

      <nav className="nav-stack">
        {navItems.map((item) => {
          const content = (
            <>
              <SidebarIcon type={item.key} />
              <span>{item.label}</span>
            </>
          );

          return item.href ? (
            item.external ? (
              <a
                className={`nav-link ${active === item.key ? "is-active" : ""}`}
                href={item.href}
                key={item.key}
                target="_blank"
                rel="noopener noreferrer"
              >
                {content}
              </a>
            ) : (
            <Link
              className={`nav-link ${active === item.key ? "is-active" : ""}`}
              href={item.href}
              key={item.key}
            >
              {content}
            </Link>
            )
          ) : (
            <button
              className={`nav-link ${active === item.key ? "is-active" : ""}`}
              type="button"
              key={item.key}
            >
              {content}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}

function SidebarIcon({ type }: { type: NavKey }) {
  return (
    <span className="nav-icon custom-nav-icon" aria-hidden="true">
      {type === "dashboard" && <DashboardIcon />}
      {type === "scan" && <ScanIcon />}
      {type === "chat" && <ChatIcon />}
    </span>
  );
}

function DashboardIcon() {
  return (
    <svg viewBox="0 0 64 64" role="img">
      <rect className="icon-bg" x="6" y="6" width="52" height="52" rx="12" />
      <rect className="icon-cell dark" x="16" y="16" width="15" height="15" rx="2" />
      <rect className="icon-cell" x="33" y="16" width="15" height="15" rx="2" />
      <rect className="icon-cell dark" x="16" y="33" width="15" height="15" rx="2" />
      <rect className="icon-cell light" x="33" y="33" width="15" height="15" rx="2" />
    </svg>
  );
}

function ScanIcon() {
  return (
    <svg viewBox="0 0 64 64" role="img">
      <rect className="icon-bg" x="6" y="6" width="52" height="52" rx="12" />
      <path className="icon-stroke" d="M18 27v-8h8M38 19h8v8M46 38v8h-8M26 46h-8v-8" />
      <rect className="icon-mark" x="26" y="26" width="12" height="12" rx="4" />
    </svg>
  );
}


function ChatIcon() {
  return (
    <svg viewBox="0 0 64 64" role="img">
      <rect className="icon-bg" x="6" y="6" width="52" height="52" rx="12" />
      <path className="icon-stroke" d="M32 16v7M27 16h10" />
      <rect className="icon-fill" x="18" y="25" width="28" height="20" rx="10" />
      <path className="icon-stroke" d="M18 33h-4M50 33h-4" />
      <circle className="bot-eye" cx="28" cy="35" r="2.3" />
      <circle className="bot-eye" cx="36" cy="35" r="2.3" />
    </svg>
  );
}
