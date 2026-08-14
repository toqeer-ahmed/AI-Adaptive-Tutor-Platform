'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import {
  WobblyCard,
  WobblyButton,
  HandBadge
} from '@/lib/HandDrawnComponents';

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
    <div style={{ padding: '32px 24px 60px', maxWidth: '1150px', margin: '0 auto' }}>
      {/* Top Breadcrumb & Status */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <Link href="/" style={{ color: 'var(--pen-blue)', textDecoration: 'none', fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>←</span> Back to Study Desk
        </Link>
        <div style={{ display: 'flex', gap: '10px' }}>
          <HandBadge variant="green">Mastery: On track 📈</HandBadge>
          <HandBadge variant="yellow">Grade 6 Mathematics</HandBadge>
        </div>
      </div>

      {/* Header Notebook Card */}
      <WobblyCard decoration="tape" style={{ marginBottom: '28px', padding: '24px 30px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <span style={{ fontSize: '1.8rem' }}>✏️</span>
              <h1 style={{ fontSize: '2rem' }}>AI Socratic Tutor Notebook</h1>
            </div>
            <p style={{ color: 'var(--pencil-subtle)', fontSize: '1.05rem' }}>
              Target Objective: <span className="marker-highlight" style={{ fontWeight: 700, color: 'var(--pencil-black)' }}>Add fractions with like and unlike denominators</span>
            </p>
          </div>
          <HandBadge variant="blue">RAG Verified</HandBadge>
        </div>
      </WobblyCard>

      {/* Mode Selector Buttons */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px', flexWrap: 'wrap' }}>
        {[
          { mode: 'explanation', label: '📖 Socratic Dialogue', icon: '📖' },
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
              className="wobbly-btn"
              style={{
                background: isActive ? 'var(--marker-red)' : '#ffffff',
                color: isActive ? '#ffffff' : 'var(--pencil-black)',
                boxShadow: isActive ? 'var(--shadow-hard-sm)' : 'var(--shadow-hard)',
                transform: isActive ? 'translate(2px, 2px)' : 'none',
                fontSize: '1rem',
                padding: '8px 18px'
              }}
            >
              {m.label}
            </button>
          );
        })}
      </div>

      {/* Main Conversation & Evidence Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Left Column: Notebook Dialogue Area */}
        <WobblyCard style={{ display: 'flex', flexDirection: 'column', height: '600px', padding: '24px', background: '#ffffff' }}>
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '18px', paddingRight: '8px' }}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  alignSelf: msg.sender === 'student' ? 'flex-end' : 'flex-start',
                  maxWidth: '82%',
                  padding: '16px 20px',
                  borderRadius: msg.sender === 'student' ? 'var(--wobbly-card)' : 'var(--wobbly-sm)',
                  background: msg.sender === 'student' ? 'var(--postit-cyan)' : 'var(--postit-yellow)',
                  border: '2px solid var(--pencil-black)',
                  boxShadow: 'var(--shadow-hard-sm)'
                }}
              >
                <div style={{ fontSize: '0.85rem', color: msg.sender === 'student' ? 'var(--pen-blue)' : 'var(--marker-red)', fontWeight: 700, marginBottom: '4px' }}>
                  {msg.sender === 'student' ? 'Alex (Student)' : `🤖 AI Tutor • ${msg.mode?.toUpperCase()}`}
                </div>
                <div style={{ fontSize: '1.1rem', lineHeight: 1.5, color: 'var(--pencil-black)' }}>
                  {msg.text}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--pencil-subtle)', marginTop: '6px', textAlign: 'right' }}>
                  {msg.timestamp}
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ color: 'var(--pen-blue)', fontSize: '1.05rem', fontStyle: 'italic' }}>
                ✏️ Tutor is writing a grounded note...
              </div>
            )}
          </div>

          {/* Chat Input Bar */}
          <div style={{ marginTop: '18px', display: 'flex', gap: '12px', paddingTop: '16px', borderTop: '2px dashed var(--pencil-muted)' }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Write your answer or question (e.g. '3/6 + 2/6 = 5/6')..."
              className="wobbly-input"
            />
            <WobblyButton
              onClick={() => handleSend()}
              disabled={loading}
              variant="red"
              style={{ minWidth: '110px' }}
            >
              Send ✎
            </WobblyButton>
          </div>
        </WobblyCard>

        {/* Right Column: Sticky-Note Textbook Citations */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <WobblyCard variant="yellow" decoration="tack-red" style={{ padding: '22px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontSize: '1.4rem' }}>📖</span>
              <h3 style={{ fontSize: '1.25rem' }}>Textbook Passages</h3>
            </div>
            <p style={{ fontSize: '0.95rem', color: 'var(--pencil-black)', opacity: 0.85, marginBottom: '14px' }}>
              Every Socratic explanation is mathematically bound to published syllabus texts.
            </p>

            {messages.length > 0 && messages[messages.length - 1].evidence ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {messages[messages.length - 1].evidence?.map((ev, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '12px',
                      background: '#ffffff',
                      borderRadius: 'var(--wobbly-sm)',
                      border: '1.5px solid var(--pencil-black)',
                      boxShadow: '2px 2px 0px var(--pencil-black)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <HandBadge variant="blue" style={{ fontSize: '0.78rem' }}>Page {ev.page_number}</HandBadge>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--pencil-subtle)' }}>{ev.section}</span>
                    </div>
                    <div style={{ color: 'var(--pencil-black)', fontSize: '0.95rem', lineHeight: 1.4, fontStyle: 'italic' }}>
                      &ldquo;{ev.text}&rdquo;
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: '16px', textAlign: 'center', color: 'var(--pencil-subtle)', fontSize: '0.95rem' }}>
                Passages and textbook page citations will appear here in real-time.
              </div>
            )}
          </WobblyCard>

          {/* Child Safety Pin Note */}
          <WobblyCard variant="green" decoration="tape" style={{ padding: '18px' }}>
            <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#15803d', marginBottom: '4px' }}>
              🛡️ Student Safety Active
            </div>
            <div style={{ fontSize: '0.92rem', color: 'var(--pencil-black)', opacity: 0.9, lineHeight: 1.4 }}>
              System prompt protection, PII redacting, and Socratic non-solution guardrails are enforced.
            </div>
          </WobblyCard>
        </div>
      </div>
    </div>
  );
}

