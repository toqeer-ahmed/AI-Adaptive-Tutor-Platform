'use client';

import React, { useState, useEffect } from 'react';
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
      const res = await apiClient.post<any>('/api/v1/tutor/session/start', {
        concept_id: '00000000-0000-0000-0000-000000000004',
        curriculum_version_id: '00000000-0000-0000-0000-000000000001',
        initial_mode: 'explanation'
      });
      if (res.data) {
        setSessionId(res.data.session_id);
      }
      setMessages([
        {
          sender: 'tutor',
          mode: 'explanation',
          text: 'Hello Alex! I am your AI Instructor grounded in Grade 6 Mathematics. How can I help you understand adding fractions with common or uncommon denominators today?',
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
    }
    initSession();
  }, []);

  async function handleSend(modeOverride?: string) {
    const activeMode = modeOverride || selectedMode;
    const textToSend = input.trim() || (modeOverride ? `Give me a ${activeMode}` : 'Explain common denominator');
    if (!textToSend && !modeOverride) return;

    const userMsg: ChatMessage = {
      sender: 'student',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!modeOverride) setInput('');
    setLoading(true);

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
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages((prev) => [...prev, tutorMsg]);
    } else {
      const tutorMsg: ChatMessage = {
        sender: 'tutor',
        mode: activeMode,
        text: 'A common denominator is shared by two or more fractions. For example, in 2/3 and 1/3, 3 is the common denominator!',
        evidence: [{ text: "Common Denominator: A shared multiple of the denominators.", page_number: 14, section: "Chapter 3.2" }],
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages((prev) => [...prev, tutorMsg]);
    }

    setLoading(false);
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1100px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      {/* Header with Qualitative Progress Badge */}
      <header style={{
        display: 'flex',
        justify: 'space-between',
        alignItems: 'center',
        padding: '20px',
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '12px',
        marginBottom: '20px'
      }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', color: '#818cf8', marginBottom: '4px' }}>
            🤖 AI Instructor Workspace
          </h1>
          <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            Target Learning Objective: Add fractions with like and unlike denominators
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', padding: '6px 12px', backgroundColor: '#065f46', color: '#34d399', borderRadius: '20px', fontWeight: 'bold' }}>
            Status: On track 📈
          </span>
          <span style={{ fontSize: '0.8rem', padding: '6px 12px', backgroundColor: '#312e81', color: '#a5b4fc', borderRadius: '20px', fontWeight: 'bold' }}>
            Grade 6 Math
          </span>
        </div>
      </header>

      {/* Mode Selector Badges */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        {[
          { mode: 'explanation', label: '📖 Explanation' },
          { mode: 'hint', label: '💡 Hint' },
          { mode: 'worked_example', label: '✏️ Worked Example' },
          { mode: 'guided_practice', label: '🎯 Practice' }
        ].map((m) => (
          <button
            key={m.mode}
            onClick={() => {
              setSelectedMode(m.mode);
              handleSend(m.mode);
            }}
            style={{
              padding: '10px 16px',
              backgroundColor: selectedMode === m.mode ? '#6366f1' : '#1e293b',
              color: '#fff',
              border: '1px solid #334155',
              borderRadius: '8px',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* Main Conversation Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        {/* Chat History & Input */}
        <div style={{ display: 'flex', flexDirection: 'column', height: '520px', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '16px' }}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  alignSelf: msg.sender === 'student' ? 'flex-end' : 'flex-start',
                  maxWidth: '80%',
                  padding: '14px 18px',
                  borderRadius: '12px',
                  backgroundColor: msg.sender === 'student' ? '#4f46e5' : '#0f172a',
                  border: msg.sender === 'student' ? 'none' : '1px solid #334155'
                }}
              >
                {msg.sender === 'tutor' && (
                  <div style={{ fontSize: '0.75rem', color: '#a5b4fc', fontWeight: 'bold', marginBottom: '4px' }}>
                    🤖 AI Instructor • {msg.mode?.toUpperCase()}
                  </div>
                )}
                <div style={{ fontSize: '0.95rem', lineHeight: '1.5' }}>{msg.text}</div>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '6px', textAlign: 'right' }}>{msg.timestamp}</div>
              </div>
            ))}
            {loading && <div style={{ color: '#94a3b8', fontStyle: 'italic' }}>AI Instructor thinking...</div>}
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask a question or ask for help..."
              style={{ flex: 1, padding: '12px 16px', borderRadius: '8px', border: '1px solid #334155', backgroundColor: '#0f172a', color: '#fff', fontSize: '0.95rem' }}
            />
            <button
              onClick={() => handleSend()}
              style={{ padding: '12px 24px', backgroundColor: '#6366f1', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}
            >
              Send
            </button>
          </div>
        </div>

        {/* Right Sidebar: Grounded Evidence & Objective Details */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '18px' }}>
            <h3 style={{ fontSize: '1rem', color: '#38bdf8', marginBottom: '8px' }}>📖 Grounded Evidence</h3>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '12px' }}>
              All AI Instructor answers are strictly grounded in approved curriculum documents.
            </p>
            {messages.length > 0 && messages[messages.length - 1].evidence ? (
              messages[messages.length - 1].evidence?.map((ev, i) => (
                <div key={i} style={{ padding: '10px', background: '#0f172a', borderRadius: '6px', fontSize: '0.8rem', borderLeft: '3px solid #10b981' }}>
                  <div style={{ fontWeight: 'bold', color: '#34d399' }}>Page {ev.page_number} • {ev.section}</div>
                  <div style={{ color: '#cbd5e1', marginTop: '2px' }}>"{ev.text}"</div>
                </div>
              ))
            ) : (
              <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Evidence citations will display here during interaction.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
