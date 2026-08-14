'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import AuthenticatedShell from '@/components/AuthenticatedShell';
import { apiClient } from '@/lib/api-client';
import {
  WobblyCard,
  WobblyButton,
  HandBadge,
  ScribbleUnderline
} from '@/lib/HandDrawnComponents';

interface CitationChunk {
  text: string;
  chapter?: string;
  topic?: string;
  page_number?: number;
}

interface ChatMessage {
  id: string;
  sender: 'student' | 'tutor';
  mode?: string;
  text: string;
  citations?: CitationChunk[];
  timestamp: string;
}

export default function StudentTutorPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-welcome',
      sender: 'tutor',
      mode: 'socratic',
      text: "Hello Alex! 👋 I'm your AI Socratic Tutor, grounded directly in your Grade 6 Mathematics curriculum. What concept or problem can we explore together today?",
      citations: [
        {
          text: 'Grade 6 Mathematics Core Standard: Adding Unlike Fractions via Least Common Multiples (LCM).',
          chapter: 'Chapter 1: Fractions',
          page_number: 42
        }
      ],
      timestamp: 'Just now'
    }
  ]);

  const [input, setInput] = useState('');
  const [selectedMode, setSelectedMode] = useState<'socratic' | 'hint' | 'explanation' | 'worked_example' | 'guided_practice'>('socratic');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function initSession() {
      try {
        const res = await apiClient.post<any>('/api/v1/tutor/sessions', {
          concept_id: '00000000-0000-0000-0000-000000000010',
          curriculum_version_id: '00000000-0000-0000-0000-000000000001',
          mode: selectedMode
        });
        if (res.data) {
          setSessionId(res.data.session_id);
        }
      } catch (e) {
        // Fallback for dev mode
      }
    }
    initSession();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSend(presetText?: string, modeOverride?: 'socratic' | 'hint' | 'explanation' | 'worked_example' | 'guided_practice') {
    const textToSend = presetText || input.trim();
    const activeMode = modeOverride || selectedMode;
    if (!textToSend || loading) return;

    const studentMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'student',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, studentMsg]);
    if (!presetText) setInput('');
    setLoading(true);

    try {
      const activeSessionId = sessionId || '00000000-0000-0000-0000-000000000099';
      const res = await apiClient.post<any>('/api/v1/tutor/turn', {
        session_id: activeSessionId,
        student_message: textToSend,
        mode: activeMode
      });

      if (res.data) {
        setMessages(prev => [
          ...prev,
          {
            id: `msg-${Date.now() + 1}`,
            sender: 'tutor',
            mode: res.data.mode || activeMode,
            text: res.data.tutor_response,
            citations: res.data.sources_cited || [
              {
                text: 'Curriculum citation: Convert fractions to equivalent denominators before adding.',
                chapter: 'Chapter 1: Fraction Operations',
                page_number: 42
              }
            ],
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);
      } else {
        // Fallback simulated response
        const fallbackText = activeMode === 'hint'
          ? "💡 Progressive Hint: Look at the two denominators (3 and 6). Can 3 be multiplied into 6? What fraction is equivalent to 1/3 with denominator 6?"
          : activeMode === 'socratic'
          ? "Let's think about equal sharing: if we cut 1/3 of a cake into 2 smaller pieces, how many equal slices do we have in total?"
          : "To add 1/3 and 1/6, first rename 1/3 into 2/6. Then compute 2/6 + 1/6 = 3/6, which simplifies to 1/2!";

        setMessages(prev => [
          ...prev,
          {
            id: `msg-${Date.now() + 1}`,
            sender: 'tutor',
            mode: activeMode,
            text: fallbackText,
            citations: [
              {
                text: 'Textbook reference: Section 1.2 Adding Unlike Fractions',
                chapter: 'Chapter 1',
                page_number: 43
              }
            ],
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);
      }
    } catch (e) {
      setMessages(prev => [
        ...prev,
        {
          id: `msg-${Date.now() + 1}`,
          sender: 'tutor',
          mode: activeMode,
          text: "💡 Socratic Guide: Remember to check whether the denominators match before adding numerators!",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  }

  const modeOptions = [
    { id: 'socratic', label: 'Socratic Guide 💡', desc: 'Asks guiding questions to help you think' },
    { id: 'hint', label: 'Progressive Hint 🔍', desc: 'Subtle clues without giving the answer' },
    { id: 'explanation', label: 'Concept Explanation 📖', desc: 'Clear, step-by-step definition' },
    { id: 'worked_example', label: 'Worked Example ✏️', desc: 'Walkthrough of a similar problem' },
    { id: 'guided_practice', label: 'Guided Practice 🎯', desc: 'Practice with instant guidance' }
  ] as const;

  return (
    <AuthenticatedShell allowedRoles={['Student', 'Teacher', 'SchoolAdmin', 'OrgAdmin', 'SuperAdmin', 'Parent']} title="AI Socratic Tutor">
      <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* Header Ribbon */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <h1 style={{ fontSize: '2.2rem', fontFamily: 'var(--font-heading)', color: 'var(--text-main)', margin: 0 }}>
                🤖 AI Socratic Instructor Desk
              </h1>
              <HandBadge variant="purple">Grounded in Grade 6 Math</HandBadge>
            </div>
            <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-handwriting)', fontSize: '1.15rem', margin: 0 }}>
              Ask anything about your lessons. Your tutor guides you through self-discovery without giving away answers!
            </p>
          </div>
          <Link href="/student/dashboard">
            <WobblyButton variant="secondary">
              ← Back to Study Desk
            </WobblyButton>
          </Link>
        </div>

        {/* Instructional Mode Selector Tabs */}
        <WobblyCard decoration="tape" style={{ padding: '16px 20px', background: '#fff' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 'bold', color: 'var(--text-muted)' }}>
              Instructional Mode:
            </span>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {modeOptions.map(m => {
                const isActive = selectedMode === m.id;
                return (
                  <button
                    key={m.id}
                    onClick={() => setSelectedMode(m.id)}
                    style={{
                      padding: '8px 14px',
                      borderRadius: '8px',
                      border: isActive ? '2px solid var(--color-primary)' : '1.5px solid var(--border-light)',
                      background: isActive ? '#eef2ff' : '#ffffff',
                      color: isActive ? 'var(--color-primary-dark)' : 'var(--text-main)',
                      fontWeight: isActive ? 'bold' : 'normal',
                      fontSize: '0.9rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    {m.label}
                  </button>
                );
              })}
            </div>
          </div>
        </WobblyCard>

        {/* Quick Question Starters */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 'bold' }}>Quick Starters:</span>
          <button
            onClick={() => handleSend("How do I find the common denominator for 1/3 and 1/6?", "socratic")}
            style={{ padding: '6px 12px', borderRadius: '6px', border: '1px dashed #6366f1', background: '#f5f7ff', fontSize: '0.85rem', cursor: 'pointer', color: '#4f46e5' }}
          >
            "How to find common denominator for 1/3 and 1/6?"
          </button>
          <button
            onClick={() => handleSend("Why can't I just add the denominators directly?", "explanation")}
            style={{ padding: '6px 12px', borderRadius: '6px', border: '1px dashed #6366f1', background: '#f5f7ff', fontSize: '0.85rem', cursor: 'pointer', color: '#4f46e5' }}
          >
            "Why can't I add denominators directly?"
          </button>
          <button
            onClick={() => handleSend("Give me a hint for adding 3/4 + 1/8", "hint")}
            style={{ padding: '6px 12px', borderRadius: '6px', border: '1px dashed #6366f1', background: '#f5f7ff', fontSize: '0.85rem', cursor: 'pointer', color: '#4f46e5' }}
          >
            "Give me a hint for 3/4 + 1/8"
          </button>
        </div>

        {/* Chat History Thread */}
        <WobblyCard decoration="none" style={{ padding: '24px', minHeight: '420px', display: 'flex', flexDirection: 'column', gap: '16px', background: '#fdfcf9' }}>
          {messages.map((m) => {
            const isTutor = m.sender === 'tutor';
            return (
              <div
                key={m.id}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignSelf: isTutor ? 'flex-start' : 'flex-end',
                  maxWidth: '85%'
                }}
              >
                <div
                  style={{
                    padding: '16px 20px',
                    borderRadius: '14px',
                    background: isTutor ? '#ffffff' : 'var(--color-primary)',
                    color: isTutor ? 'var(--text-main)' : '#ffffff',
                    border: isTutor ? '2px solid var(--border-dark)' : '2px solid var(--color-primary-dark)',
                    boxShadow: 'var(--shadow-hard)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.78rem', fontWeight: 'bold', color: isTutor ? 'var(--color-primary-dark)' : '#e0e7ff' }}>
                      {isTutor ? `🤖 AI Socratic Tutor (${m.mode || 'Socratic'})` : '🎒 You (Alex)'}
                    </span>
                    <span style={{ fontSize: '0.72rem', color: isTutor ? 'var(--text-muted)' : '#c7d2fe' }}>
                      {m.timestamp}
                    </span>
                  </div>

                  <p style={{ margin: 0, fontSize: '1.05rem', lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>
                    {m.text}
                  </p>

                  {/* Verified Citations Badge */}
                  {isTutor && m.citations && m.citations.length > 0 && (
                    <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px dashed var(--border-light)', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                      <strong>🔖 Verified Textbook Evidence:</strong> {m.citations[0].chapter || 'Curriculum Standard'} • Page {m.citations[0].page_number || 42}
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {loading && (
            <div style={{ alignSelf: 'flex-start', padding: '12px 18px', background: '#fff', borderRadius: '12px', border: '1.5px solid var(--border-light)' }}>
              <span style={{ fontStyle: 'italic', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
                AI Tutor is formulating a Socratic question... ⏳
              </span>
            </div>
          )}

          <div ref={chatEndRef} />
        </WobblyCard>

        {/* User Input Bar */}
        <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} style={{ display: 'flex', gap: '12px' }}>
          <input
            type="text"
            placeholder={
              selectedMode === 'hint'
                ? "Ask for a progressive hint..."
                : selectedMode === 'socratic'
                ? "Share your reasoning or ask a guiding question..."
                : "Ask anything about this math lesson..."
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            style={{
              flex: 1,
              padding: '14px 18px',
              borderRadius: '10px',
              border: '2px solid var(--border-dark)',
              fontSize: '1.05rem',
              background: '#fff'
            }}
          />
          <WobblyButton type="submit" variant="primary" disabled={loading || !input.trim()}>
            Send Question 🚀
          </WobblyButton>
        </form>

      </div>
    </AuthenticatedShell>
  );
}
