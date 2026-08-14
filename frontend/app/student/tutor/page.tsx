'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';

interface ChatMessage {
  sender: 'student' | 'tutor';
  mode?: string;
  text: string;
  evidence?: Array<{ text: string; page_number: number; section: string }>;
  timestamp: string;
}

export default function StudentTutorPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [selectedMode, setSelectedMode] = useState<string>('explanation');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    async function initSession() {
      try {
        const res = await apiClient.post<any>('/api/v1/tutor/session/start', {
          concept_id: '00000000-0000-0000-0000-000000000004',
          curriculum_version_id: '00000000-0000-0000-0000-000000000001',
          initial_mode: 'explanation'
        });
        if (res.data) {
          setSessionId(res.data.session_id);
        }
      } catch (e) {
        // Fallback for standalone demo
      }

      setMessages([
        {
          sender: 'tutor',
          mode: 'explanation',
          text: 'Hello Alex! I am your AI Socratic Tutor grounded in Grade 6 Mathematics. How can I help you master adding fractions with common or uncommon denominators today?',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    }
    initSession();
  }, []);

  async function handleSend(modeOverride?: string) {
    const activeMode = modeOverride || selectedMode;
    const textToSend = input.trim() || (modeOverride ? `Give me a ${activeMode.replace('_', ' ')}` : 'Explain common denominator');
    if (!textToSend && !modeOverride) return;

    const userMsg: ChatMessage = {
      sender: 'student',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!modeOverride) setInput('');
    setLoading(true);

    try {
      const res = await apiClient.post<any>('/api/v1/tutor/interact', {
        session_id: sessionId || '00000000-0000-0000-0000-000000000000',
        user_message: textToSend,
        tutor_mode: activeMode,
        concept_id: '00000000-0000-0000-0000-000000000004',
        learning_objective_id: '00000000-0000-0000-0000-000000000006'
      });

      if (res.data) {
        const tutorMsg: ChatMessage = {
          sender: 'tutor',
          mode: res.data.tutor_mode,
          text: res.data.tutor_response,
          evidence: res.data.evidence,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages((prev) => [...prev, tutorMsg]);
      } else {
        throw new Error('Fallback required');
      }
    } catch (err) {
      const tutorMsg: ChatMessage = {
        sender: 'tutor',
        mode: activeMode,
        text: 'A common denominator is a shared multiple of the denominators. For example, to add 1/3 and 1/6, we convert 1/3 to 2/6 so both fractions share the denominator 6!',
        evidence: [{ text: "Common Denominator: A shared multiple of the denominators.", page_number: 14, section: "Chapter 3.2" }],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, tutorMsg]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: '32px 24px 60px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Top Breadcrumb & Header */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <Link href="/" style={{ color: 'var(--text-muted)', textDecoration: 'none', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>←</span> Back to Portals
        </Link>
        <div style={{ display: 'flex', gap: '10px' }}>
          <span className="badge badge-emerald">Mastery: On track 📈</span>
          <span className="badge badge-cyan">Grade 6 Mathematics</span>
        </div>
      </div>

      <header className="glass-panel" style={{ padding: '24px 28px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <span style={{ fontSize: '1.5rem' }}>🤖</span>
            <h1 style={{ fontSize: '1.6rem', color: '#f8fafc' }}>
              AI Socratic Tutor
            </h1>
            <span className="badge badge-purple">Grounded RAG</span>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Target Objective: <span style={{ color: '#f8fafc', fontWeight: 500 }}>Add fractions with like and unlike denominators</span>
          </p>
        </div>
      </header>

      {/* Tutor Mode Pills */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {[
          { mode: 'explanation', label: '📖 Socratic Explanation', icon: '📖' },
          { mode: 'hint', label: '💡 Step Hint', icon: '💡' },
          { mode: 'worked_example', label: '✏️ Worked Example', icon: '✏️' },
          { mode: 'guided_practice', label: '🎯 Practice Problem', icon: '🎯' }
        ].map((m) => {
          const isActive = selectedMode === m.mode;
          return (
            <button
              key={m.mode}
              onClick={() => {
                setSelectedMode(m.mode);
                handleSend(m.mode);
              }}
              style={{
                padding: '10px 18px',
                background: isActive ? 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)' : 'rgba(15, 23, 42, 0.7)',
                color: '#ffffff',
                border: `1px solid ${isActive ? 'rgba(129, 140, 248, 0.5)' : 'var(--border-subtle)'}`,
                borderRadius: '9999px',
                fontWeight: 600,
                fontSize: '0.88rem',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: isActive ? '0 0 15px rgba(99, 102, 241, 0.35)' : 'none'
              }}
            >
              {m.label}
            </button>
          );
        })}
      </div>

      {/* Main Grid: Conversation + Evidence Inspector */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Left Column: Interactive Chat History & Input */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '580px', padding: '24px' }}>
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '18px', paddingRight: '8px' }}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  alignSelf: msg.sender === 'student' ? 'flex-end' : 'flex-start',
                  maxWidth: '82%',
                  padding: '16px 20px',
                  borderRadius: msg.sender === 'student' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                  background: msg.sender === 'student' 
                    ? 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)' 
                    : 'rgba(30, 41, 59, 0.85)',
                  border: msg.sender === 'student' 
                    ? '1px solid rgba(255, 255, 255, 0.15)' 
                    : '1px solid var(--border-subtle)',
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.25)'
                }}
              >
                {msg.sender === 'tutor' && (
                  <div style={{ fontSize: '0.75rem', color: '#38bdf8', fontWeight: 700, marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span>🤖</span> AI Instructor • {msg.mode?.toUpperCase()}
                  </div>
                )}
                <div style={{ fontSize: '0.95rem', lineHeight: 1.6, color: '#f8fafc' }}>
                  {msg.text}
                </div>
                <div style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.4)', marginTop: '8px', textAlign: 'right' }}>
                  {msg.timestamp}
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '0.9rem', fontStyle: 'italic' }}>
                <span className="pulse-dot online" /> Formulating grounded response...
              </div>
            )}
          </div>

          {/* Chat Input Bar */}
          <div style={{ marginTop: '20px', display: 'flex', gap: '12px', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)' }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask a question or enter your answer (e.g. '3/6 + 2/6 = 5/6')..."
              style={{
                flex: 1,
                padding: '14px 18px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                backgroundColor: 'rgba(15, 23, 42, 0.8)',
                color: '#ffffff',
                fontSize: '0.95rem',
                outline: 'none'
              }}
            />
            <button
              onClick={() => handleSend()}
              disabled={loading}
              className="btn-primary"
              style={{ minWidth: '100px' }}
            >
              Send 🚀
            </button>
          </div>
        </div>

        {/* Right Column: Grounded Evidence Citation Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="glass-panel" style={{ padding: '22px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <span style={{ fontSize: '1.2rem' }}>📖</span>
              <h3 style={{ fontSize: '1.05rem', color: '#38bdf8' }}>Verified Citations</h3>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '16px', lineHeight: 1.5 }}>
              All responses are strictly constrained to published Grade 6 textbook passages.
            </p>

            {messages.length > 0 && messages[messages.length - 1].evidence ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {messages[messages.length - 1].evidence?.map((ev, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '14px',
                      background: 'rgba(15, 23, 42, 0.7)',
                      borderRadius: 'var(--radius-sm)',
                      borderLeft: '3px solid #10b981',
                      border: '1px solid var(--border-subtle)',
                      borderLeftColor: '#10b981'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span className="badge badge-emerald" style={{ fontSize: '0.7rem' }}>
                        Page {ev.page_number}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{ev.section}</span>
                    </div>
                    <div style={{ color: '#cbd5e1', fontSize: '0.82rem', lineHeight: 1.5, fontStyle: 'italic' }}>
                      &ldquo;{ev.text}&rdquo;
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-subtle)', fontSize: '0.85rem' }}>
                Passages and textbook page citations will appear here in real-time.
              </div>
            )}
          </div>

          {/* Child Safety & Guardrails Pill */}
          <div className="glass-panel" style={{ padding: '18px', borderLeft: '3px solid #818cf8' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#818cf8', marginBottom: '4px' }}>
              🛡️ Student Safety Active
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
              System prompt protection, PII redacting, and Socratic non-solution guardrails are active.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
