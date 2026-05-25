'use client';

import React, { useState, useEffect, useRef } from 'react';
import Sidebar from '@/components/Sidebar';
import ChatInterface from '@/components/ChatInterface';

interface Message {
  role: 'user' | 'bot';
  content: string;
}

export interface Session {
  id: string;
  messages: Message[];
  createdAt: number;
  preview: string;
}

const GREETING =
  "Hello! I am your waste management assistant. Ask me about how to properly dispose, recycle, or handle any item. How can I help you today?";

// Generate a stable ID once per browser tab (survives re-renders, not page reloads)
function newSessionId() {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([{ role: 'bot', content: GREETING }]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [activeView, setActiveView] = useState<'chat' | 'history'>('chat');
  const [sessions, setSessions] = useState<Session[]>([]);
  const [ready, setReady] = useState(false); // prevent sending before backend is reset

  const sessionIdRef = useRef<string>('');
  const sessionCreatedAtRef = useRef<number>(Date.now());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // On mount: create a fresh session ID and reset it on the backend BEFORE chat is usable
  useEffect(() => {
    const id = newSessionId();
    sessionIdRef.current = id;
    sessionCreatedAtRef.current = Date.now();

    const stored = localStorage.getItem('chat_sessions');
    if (stored) {
      try { setSessions(JSON.parse(stored)); } catch { localStorage.removeItem('chat_sessions'); }
    }

    // Wait for backend reset to complete before allowing messages
    fetch(`http://localhost:8001/reset_session?session_id=${id}`, { method: 'POST' })
      .catch(() => {}) // backend might be down — still allow chat
      .finally(() => setReady(true));
  }, []);

  // Auto-save session to localStorage whenever messages change
  useEffect(() => {
    const userMessages = messages.filter((m) => m.role === 'user');
    if (userMessages.length === 0 || !sessionIdRef.current) return;

    const session: Session = {
      id: sessionIdRef.current,
      messages,
      createdAt: sessionCreatedAtRef.current,
      preview: userMessages[0].content,
    };

    setSessions((prev) => {
      const others = prev.filter((s) => s.id !== sessionIdRef.current);
      const updated = [session, ...others].slice(0, 50);
      localStorage.setItem('chat_sessions', JSON.stringify(updated));
      return updated;
    });
  }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || !ready) return;
    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setIsTyping(true);

    try {
      const response = await fetch('http://localhost:8001/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          history: [],          // backend manages its own context — don't send stale frontend history
          session_id: sessionIdRef.current,
        }),
      });

      if (!response.ok) throw new Error(`Server error: ${response.statusText}`);
      const data = await response.json();
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        { role: 'bot', content: data.response ?? 'I encountered an issue. Please try again.' },
      ]);
    } catch (error) {
      setIsTyping(false);
      const msg = error instanceof Error ? error.message : 'Unknown error';
      setMessages((prev) => [
        ...prev,
        { role: 'bot', content: `Network error: ${msg}. Make sure the chatbot backend is running at http://localhost:8001` },
      ]);
    }
  };

  const handleClearChat = () => {
    const id = newSessionId();
    sessionIdRef.current = id;
    sessionCreatedAtRef.current = Date.now();
    setReady(false);
    setMessages([{ role: 'bot', content: 'Chat cleared. What would you like to know about waste management?' }]);
    setActiveView('chat');
    fetch(`http://localhost:8001/reset_session?session_id=${id}`, { method: 'POST' })
      .catch(() => {})
      .finally(() => setReady(true));
  };

  const handleLoadSession = (session: Session) => {
    // Viewing history only — do NOT reset the backend; just display the messages
    sessionIdRef.current = session.id;
    sessionCreatedAtRef.current = session.createdAt;
    setMessages(session.messages);
    setActiveView('chat');
  };

  const handleDeleteSession = (id: string) => {
    setSessions((prev) => {
      const updated = prev.filter((s) => s.id !== id);
      localStorage.setItem('chat_sessions', JSON.stringify(updated));
      return updated;
    });
  };

  return (
    <div className="app-container">
      <Sidebar
        onClearChat={handleClearChat}
        activeView={activeView}
        setActiveView={setActiveView}
        sessions={sessions}
        onLoadSession={handleLoadSession}
        onDeleteSession={handleDeleteSession}
      />
      <ChatInterface
        messages={messages}
        input={input}
        setInput={setInput}
        onSend={handleSend}
        isTyping={isTyping || !ready}
        messagesEndRef={messagesEndRef}
        activeView={activeView}
      />
    </div>
  );
}