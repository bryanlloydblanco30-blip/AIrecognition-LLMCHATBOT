'use client';

import React from 'react';
import { Send } from 'lucide-react';

interface Message {
  role: 'user' | 'bot';
  content: string;
}

interface ChatInterfaceProps {
  messages: Message[];
  input: string;
  setInput: (val: string) => void;
  onSend: () => void;
  isTyping: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  activeView: 'chat' | 'history';
}

// Parse inline markdown within a single line: **bold** and `code`
const parseInlineMarkdown = (text: string, keyPrefix: string): (string | React.ReactNode)[] => {
  const parts: (string | React.ReactNode)[] = [];
  const regex = /\*\*(.*?)\*\*|`([^`]+)`/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    if (match[1] !== undefined) {
      parts.push(<strong key={`${keyPrefix}-b-${match.index}`}>{match[1]}</strong>);
    } else if (match[2] !== undefined) {
      parts.push(
        <code
          key={`${keyPrefix}-c-${match.index}`}
          style={{
            background: 'rgba(0,0,0,0.1)',
            borderRadius: '3px',
            padding: '1px 4px',
            fontFamily: 'monospace',
            fontSize: '0.9em'
          }}
        >
          {match[2]}
        </code>
      );
    }
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : [text];
};

// Render a full markdown message as React elements
const renderMarkdown = (content: string): React.ReactNode => {
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (trimmed === '') {
      i++;
      continue;
    }

    if (trimmed.startsWith('### ')) {
      const text = trimmed.slice(4);
      elements.push(
        <div
          key={i}
          style={{ fontWeight: 700, fontSize: '0.95em', marginTop: '0.8rem', marginBottom: '0.2rem', opacity: 0.95 }}
        >
          {parseInlineMarkdown(text, `h3-${i}`)}
        </div>
      );
      i++;
      continue;
    }

    if (trimmed.startsWith('## ')) {
      const text = trimmed.slice(3);
      elements.push(
        <div
          key={i}
          style={{ fontWeight: 700, fontSize: '1.05em', marginTop: '1rem', marginBottom: '0.3rem', opacity: 1 }}
        >
          {parseInlineMarkdown(text, `h2-${i}`)}
        </div>
      );
      i++;
      continue;
    }

    if (trimmed.startsWith('# ')) {
      const text = trimmed.slice(2);
      elements.push(
        <div
          key={i}
          style={{ fontWeight: 700, fontSize: '1.15em', marginTop: '1rem', marginBottom: '0.4rem', opacity: 1 }}
        >
          {parseInlineMarkdown(text, `h1-${i}`)}
        </div>
      );
      i++;
      continue;
    }

    if (/^[*-] /.test(trimmed)) {
      const items: React.ReactNode[] = [];
      while (i < lines.length && /^[*-] /.test(lines[i].trim())) {
        const itemText = lines[i].trim().slice(2);
        items.push(
          <li key={i} style={{ marginBottom: '0.2rem' }}>
            {parseInlineMarkdown(itemText, `li-${i}`)}
          </li>
        );
        i++;
      }
      elements.push(
        <ul key={`ul-${i}`} style={{ paddingLeft: '1.3rem', marginTop: '0.3rem', marginBottom: '0.3rem' }}>
          {items}
        </ul>
      );
      continue;
    }

    if (/^\d+\. /.test(trimmed)) {
      const items: React.ReactNode[] = [];
      while (i < lines.length && /^\d+\. /.test(lines[i].trim())) {
        const itemText = lines[i].trim().replace(/^\d+\. /, '');
        items.push(
          <li key={i} style={{ marginBottom: '0.2rem' }}>
            {parseInlineMarkdown(itemText, `ol-${i}`)}
          </li>
        );
        i++;
      }
      elements.push(
        <ol key={`ol-${i}`} style={{ paddingLeft: '1.3rem', marginTop: '0.3rem', marginBottom: '0.3rem' }}>
          {items}
        </ol>
      );
      continue;
    }

    if (trimmed === '---' || trimmed === '***') {
      elements.push(
        <hr key={i} style={{ border: 'none', borderTop: '1px solid rgba(0,0,0,0.1)', margin: '0.5rem 0' }} />
      );
      i++;
      continue;
    }

    elements.push(
      <p key={i} style={{ margin: '0.2rem 0', lineHeight: '1.5' }}>
        {parseInlineMarkdown(trimmed, `p-${i}`)}
      </p>
    );
    i++;
  }

  return <>{elements}</>;
};

export default function ChatInterface({
  messages,
  input,
  setInput,
  onSend,
  isTyping,
  messagesEndRef,
  activeView
}: ChatInterfaceProps) {
  // Check if messages list is empty
  const isEmpty = messages.length === 0;

  return (
    <main className="main-container">
      {/* Top teal bar */}
      <div className="top-bar" />

      {/* Content wrapper with background image */}
      <div className="content-wrapper">
        <img
          src="/mountains.png"
          alt="Background Mountains"
          className="background-image"
        />

        {/* Scrollable chat area */}
        <div className="chat-area">
          {activeView === 'history' && isEmpty && (
            <div className="chat-placeholder">
              No chat history yet.
            </div>
          )}

          {activeView === 'chat' && isEmpty && (
            <div className="chat-placeholder">
              Ask me anything about trash management — recycling, composting, sorting, and more.
            </div>
          )}

          {/* Render messages */}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`message-bubble-container ${msg.role === 'user' ? 'user' : 'bot'}`}
            >
              <div className="message-bubble">
                {msg.role === 'bot' ? renderMarkdown(msg.content) : msg.content}
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="message-bubble-container bot">
              <div className="message-bubble" style={{ fontStyle: 'italic', opacity: 0.7 }}>
                DeepSeek is thinking...
              </div>
            </div>
          )}

          {/* Scroll Target */}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="input-outer-container">
          <div className="input-inner-wrapper">
            <input
              type="text"
              className="text-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && onSend()}
              placeholder="Ask me anything about trash management ...."
              autoComplete="off"
            />
            <button className="send-button" onClick={onSend}>
              <Send size={22} style={{ color: '#00c8b3' }} strokeWidth={2} />
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}