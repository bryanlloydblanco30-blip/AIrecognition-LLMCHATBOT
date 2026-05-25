'use client';

import React from 'react';
import {
  ChevronLeft,
  Bot,
  Trash2,
  History,
  CircleUserRound,
} from 'lucide-react';
import { Session } from '@/app/page';

interface SidebarProps {
  onClearChat?: () => void;
  activeView: 'chat' | 'history';
  setActiveView: (view: 'chat' | 'history') => void;
  sessions: Session[];
  onLoadSession: (session: Session) => void;
  onDeleteSession: (id: string) => void;
}

export default function Sidebar({
  onClearChat,
  activeView,
  setActiveView,
  sessions,
  onLoadSession,
  onDeleteSession,
}: SidebarProps) {
  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800&display=swap');

        .sb-root {
          display: flex;
          flex-direction: column;
          width: 280px;
          min-height: 100vh;
          background: linear-gradient(160deg, #2ec4a9 0%, #1aab90 60%, #0f9278 100%);
          font-family: 'Nunito', sans-serif;
          padding: 0;
          position: relative;
          overflow: hidden;
        }

        /* Decorative blobs for depth */
        .sb-root::before {
          content: '';
          position: absolute;
          top: -60px;
          right: -60px;
          width: 200px;
          height: 200px;
          border-radius: 50%;
          background: rgba(255,255,255,0.07);
          pointer-events: none;
        }
        .sb-root::after {
          content: '';
          position: absolute;
          bottom: 100px;
          left: -80px;
          width: 240px;
          height: 240px;
          border-radius: 50%;
          background: rgba(255,255,255,0.05);
          pointer-events: none;
        }

        /* ── Header ── */
        .sb-header {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 22px 20px 18px;
        }
        .sb-back-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 34px;
          height: 34px;
          border-radius: 50%;
          border: none;
          background: rgba(255,255,255,0.18);
          color: #fff;
          cursor: pointer;
          transition: background 0.18s;
          flex-shrink: 0;
        }
        .sb-back-btn:hover {
          background: rgba(255,255,255,0.30);
        }
        .sb-title {
          font-size: 17px;
          font-weight: 800;
          color: #fff;
          letter-spacing: 0.01em;
          line-height: 1.2;
        }

        /* ── Nav ── */
        .sb-nav {
          display: flex;
          flex-direction: column;
          gap: 10px;
          padding: 6px 18px 0;
        }
        .sb-nav-btn {
          display: flex;
          align-items: center;
          gap: 14px;
          width: 100%;
          padding: 14px 18px;
          border-radius: 16px;
          border: none;
          background: rgba(255,255,255,0.18);
          color: #fff;
          font-family: 'Nunito', sans-serif;
          font-size: 16px;
          font-weight: 700;
          cursor: pointer;
          text-align: left;
          transition: background 0.18s, transform 0.15s;
          backdrop-filter: blur(4px);
          position: relative;
          overflow: hidden;
        }
        .sb-nav-btn::before {
          content: '';
          position: absolute;
          inset: 0;
          border-radius: 16px;
          border: 1.5px solid rgba(255,255,255,0.25);
          pointer-events: none;
        }
        .sb-nav-btn:hover {
          background: rgba(255,255,255,0.26);
          transform: translateY(-1px);
        }
        .sb-nav-btn:active {
          transform: translateY(0);
        }
        .sb-nav-btn.active {
          background: rgba(255,255,255,0.32);
         
        }
        .sb-nav-btn.active::before {
          border-color: rgba(255,255,255,0.5);
        }
        .sb-nav-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 40px;
          height: 40px;
          border-radius: 12px;
          background: rgba(255,255,255,0.18);
          flex-shrink: 0;
        }
        .sb-nav-btn.active .sb-nav-icon {
          background: rgba(255,255,255,0.28);
        }

        /* ── Divider ── */
        .sb-divider {
          margin: 18px 18px 0;
          height: 1px;
          background: rgba(255,255,255,0.18);
          border-radius: 1px;
        }

        /* ── History list ── */
        .sb-history {
          flex: 1;
          overflow-y: auto;
          padding: 12px 18px 0;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .sb-history::-webkit-scrollbar { width: 4px; }
        .sb-history::-webkit-scrollbar-track { background: transparent; }
        .sb-history::-webkit-scrollbar-thumb {
          background: rgba(255,255,255,0.25);
          border-radius: 4px;
        }
        .sb-history-label {
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          color: rgba(255,255,255,0.6);
          padding: 0 2px 6px;
        }
        .sb-history-empty {
          font-size: 13px;
          color: rgba(255,255,255,0.55);
          text-align: center;
          padding: 20px 0;
        }
        .sb-history-item {
          display: flex;
          align-items: center;
          gap: 6px;
          border-radius: 10px;
          background: rgba(255,255,255,0.12);
          overflow: hidden;
          transition: background 0.15s;
        }
        .sb-history-item:hover {
          background: rgba(255,255,255,0.20);
        }
        .sb-history-preview {
          flex: 1;
          padding: 9px 12px;
          font-size: 13px;
          font-weight: 600;
          color: rgba(255,255,255,0.92);
          text-align: left;
          background: none;
          border: none;
          cursor: pointer;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          font-family: 'Nunito', sans-serif;
        }
        .sb-history-delete {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 9px 10px;
          background: none;
          border: none;
          color: rgba(255,255,255,0.5);
          cursor: pointer;
          transition: color 0.15s;
          flex-shrink: 0;
        }
        .sb-history-delete:hover {
          color: #ff8585;
        }

        /* ── Spacer ── */
        .sb-spacer { flex: 1; }

        /* ── Footer ── */
        .sb-footer {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 18px 20px 24px;
          border-top: 1px solid rgba(255,255,255,0.15);
          margin-top: auto;
        }
        .sb-avatar {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 44px;
          height: 44px;
          border-radius: 50%;
          background: rgba(255,255,255,0.20);
          flex-shrink: 0;
          border: 2px solid rgba(255,255,255,0.35);
        }
        .sb-username {
          font-size: 15px;
          font-weight: 700;
          color: #fff;
          letter-spacing: 0.01em;
        }
      `}</style>

      <aside className="sb-root">
        {/* Header */}
        <div className="sb-header">
          <button
            className="sb-back-btn"
            aria-label="Go back to dashboard"
            onClick={() => { window.location.href = 'http://localhost:3000'; }}
          >
            <ChevronLeft size={18} strokeWidth={2.5} />
          </button>
          <span className="sb-title">Waste&nbsp;Manager AI</span>
        </div>

        {/* Nav */}
        <nav className="sb-nav">
          <button
            onClick={() => setActiveView('chat')}
            className={`sb-nav-btn${activeView === 'chat' ? ' active' : ''}`}
          >
            <span className="sb-nav-icon">
              <Bot size={22} strokeWidth={1.8} />
            </span>
            Chat
          </button>

          {onClearChat && (
            <button onClick={onClearChat} className="sb-nav-btn">
              <span className="sb-nav-icon">
                <Trash2 size={22} strokeWidth={1.8} />
              </span>
              Clear Chat
            </button>
          )}

          <button
            onClick={() => setActiveView('history')}
            className={`sb-nav-btn${activeView === 'history' ? ' active' : ''}`}
          >
            <span className="sb-nav-icon">
              <History size={22} strokeWidth={1.8} />
            </span>
            History
          </button>
        </nav>

        {/* History list */}
        {activeView === 'history' ? (
          <>
            <div className="sb-divider" />
            <div className="sb-history">
              <p className="sb-history-label">Past Sessions</p>
              {sessions.length === 0 ? (
                <p className="sb-history-empty">No past sessions yet.</p>
              ) : (
                sessions.map((session) => (
                  <div key={session.id} className="sb-history-item">
                    <button
                      className="sb-history-preview"
                      onClick={() => onLoadSession(session)}
                    >
                      {session.preview}
                    </button>
                    <button
                      className="sb-history-delete"
                      onClick={() => onDeleteSession(session.id)}
                      aria-label="Delete session"
                    >
                      <Trash2 size={14} strokeWidth={1.5} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </>
        ) : (
          <div className="sb-spacer" />
        )}

        {/* Footer */}
        <div className="sb-footer">
          <div className="sb-avatar">
            <CircleUserRound size={26} strokeWidth={1.5} color="#fff" />
          </div>
          <span className="sb-username">Username</span>
        </div>
      </aside>
    </>
  );
}