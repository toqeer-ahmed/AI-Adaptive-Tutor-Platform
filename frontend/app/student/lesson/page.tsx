'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import AuthenticatedShell from '@/components/AuthenticatedShell';
import {
  WobblyCard,
  WobblyButton,
  HandBadge,
  ScribbleUnderline
} from '@/lib/HandDrawnComponents';
import { apiClient } from '@/lib/api-client';

export default function StudentInteractiveLessonPage() {
  const [activeStep, setActiveStep] = useState<number>(1);
  const [selectedPracticeAnswer, setSelectedPracticeAnswer] = useState<string | null>(null);
  const [practiceFeedback, setPracticeFeedback] = useState<{ isCorrect: boolean; message: string } | null>(null);

  // Embedded AI Socratic Sidecar State
  const [tutorQuery, setTutorQuery] = useState('');
  const [tutorMode, setTutorMode] = useState<'hint' | 'explanation' | 'socratic'>('socratic');
  const [tutorMessages, setTutorMessages] = useState<Array<{ role: 'student' | 'tutor'; text: string; mode?: string }>>([
    {
      role: 'tutor',
      text: "Hi Alex! 👋 I'm your AI Socratic Tutor. Need a hint on finding common denominators, or want me to ask you a guiding question?",
      mode: 'socratic'
    }
  ]);
  const [isTutorLoading, setIsTutorLoading] = useState(false);

  function handlePracticeSubmit(choice: string) {
    setSelectedPracticeAnswer(choice);
    if (choice === '1/2') {
      setPracticeFeedback({
        isCorrect: true,
        message: '🌟 Spot on, Alex! 1/3 is equivalent to 2/6. Adding 2/6 + 1/6 gives 3/6, which simplifies to 1/2!'
      });
    } else if (choice === '2/9') {
      setPracticeFeedback({
        isCorrect: false,
        message: '💡 Remember: the denominator tells us the size of each slice. We cannot add 3 + 6 directly! Convert 1/3 into sixths first.'
      });
    } else {
      setPracticeFeedback({
        isCorrect: false,
        message: '💡 Look at the common denominator 6. Convert 1/3 into equivalent sixths: (1×2)/(3×2) = 2/6.'
      });
    }
  }

  async function handleSendTutorMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!tutorQuery.trim() || isTutorLoading) return;

    const userText = tutorQuery;
    setTutorMessages(prev => [...prev, { role: 'student', text: userText }]);
    setTutorQuery('');
    setIsTutorLoading(true);

    try {
      // Create session & execute turn
      const sessRes = await apiClient.post<any>('/api/v1/tutor/sessions', {
        concept_id: '00000000-0000-0000-0000-000000000010',
        curriculum_version_id: '00000000-0000-0000-0000-000000000001',
        mode: tutorMode
      });

      const sId = sessRes.data?.session_id || '00000000-0000-0000-0000-000000000099';
      const turnRes = await apiClient.post<any>('/api/v1/tutor/turn', {
        session_id: sId,
        student_message: userText,
        mode: tutorMode
      });

      if (turnRes.data) {
        setTutorMessages(prev => [...prev, { role: 'tutor', text: turnRes.data.tutor_response, mode: tutorMode }]);
      } else {
        // Safe fallback response
        setTutorMessages(prev => [
          ...prev,
          {
            role: 'tutor',
            text: tutorMode === 'hint'
              ? "💡 Hint: To find a common denominator for 3 and 6, ask yourself: what is the smallest multiple that both numbers divide into evenly?"
              : "Let's think step by step: what happens to the size of each piece when we slice 1/3 of a pizza into sixths?",
            mode: tutorMode
          }
        ]);
      }
    } catch (e) {
      setTutorMessages(prev => [
        ...prev,
        {
          role: 'tutor',
          text: "💡 Socratic Hint: Remember that finding equivalent fractions means multiplying the top and bottom numbers by the same factor!",
          mode: tutorMode
        }
      ]);
    } finally {
      setIsTutorLoading(false);
    }
  }

  return (
    <AuthenticatedShell allowedRoles={['Student', 'OrgAdmin', 'SchoolAdmin', 'SuperAdmin']} title="Interactive Lesson">
      <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
        
        {/* Lesson Breadcrumb & Title */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <Link href="/student/subjects" style={{ color: 'var(--text-muted)', fontSize: '0.95rem', textDecoration: 'none' }}>
                Grade 6 Mathematics
              </Link>
              <span style={{ color: 'var(--text-muted)' }}>&gt;</span>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>Unit 1: Fractions</span>
              <span style={{ color: 'var(--text-muted)' }}>&gt;</span>
              <span style={{ color: 'var(--color-primary-dark)', fontWeight: 'bold', fontSize: '0.95rem' }}>Lesson 1.1</span>
            </div>
            <h1 style={{ fontSize: '2.2rem', fontFamily: 'var(--font-heading)', color: 'var(--text-main)', margin: 0 }}>
              Adding Unlike Fractions with Common Denominators
            </h1>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <Link href="/student/subjects">
              <WobblyButton variant="secondary">
                ← All Topics
              </WobblyButton>
            </Link>
            <Link href="/student/assessments">
              <WobblyButton variant="accent">
                Practice Quiz ✏️
              </WobblyButton>
            </Link>
          </div>
        </div>

        {/* Main Grid: Chunked Lesson Body + AI Socratic Sidecar */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '24px', alignItems: 'start' }}>
          
          {/* Left Column: Pedagogical Chunked Lesson Experience */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            
            {/* Section 1: The Big Idea & Visual Model */}
            <WobblyCard decoration="tape" style={{ padding: '26px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                <span style={{ fontSize: '1.6rem' }}>🍕</span>
                <h2 style={{ fontSize: '1.35rem', fontFamily: 'var(--font-heading)', margin: 0, color: 'var(--text-main)' }}>
                  1. The Big Idea: Why Do We Need Common Denominators?
                </h2>
              </div>
              <p style={{ fontSize: '1.05rem', color: 'var(--text-main)', lineHeight: 1.6, margin: '0 0 16px 0' }}>
                Imagine having <strong>1 big third-slice</strong> of a pizza and <strong>1 smaller sixth-slice</strong>. You cannot simply say you have "2 pieces" because the slices are different sizes!
              </p>
              
              {/* Visual Model Box */}
              <div style={{ background: '#fdfcf9', border: '2px dashed var(--border-dark)', borderRadius: '12px', padding: '16px', textAlign: 'center', marginBottom: '14px' }}>
                <div style={{ fontSize: '0.95rem', fontWeight: 'bold', color: 'var(--color-primary-dark)', marginBottom: '8px' }}>
                  Visualizing 1/3 vs 2/6:
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', alignItems: 'center' }}>
                  <div style={{ border: '2px solid #000', borderRadius: '8px', padding: '10px 16px', background: '#fef3c7' }}>
                    <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>1 / 3</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>1 of 3 equal parts</div>
                  </div>
                  <span style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>=</span>
                  <div style={{ border: '2px solid #000', borderRadius: '8px', padding: '10px 16px', background: '#dcfce7' }}>
                    <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>2 / 6</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>2 of 6 equal parts</div>
                  </div>
                </div>
              </div>
              <div style={{ fontSize: '0.95rem', color: 'var(--text-muted)' }}>
                <strong>Key Rule:</strong> Denominators tell us the <em>size</em> of each piece. Always rename fractions so they share the <strong>Least Common Denominator (LCD)</strong> before adding.
              </div>
            </WobblyCard>

            {/* Section 2: Step-by-Step Worked Example */}
            <WobblyCard style={{ padding: '26px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                <span style={{ fontSize: '1.6rem' }}>✏️</span>
                <h2 style={{ fontSize: '1.35rem', fontFamily: 'var(--font-heading)', margin: 0, color: 'var(--text-main)' }}>
                  2. Step-by-Step Problem Walkthrough
                </h2>
              </div>
              <div style={{ background: '#f8fafc', padding: '14px 18px', borderRadius: '10px', marginBottom: '16px', fontWeight: 'bold', fontSize: '1.1rem' }}>
                Solve: <span style={{ color: 'var(--color-primary-dark)' }}>1/4 + 3/8 = ?</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ borderLeft: '4px solid var(--color-primary)', paddingLeft: '12px' }}>
                  <div style={{ fontWeight: 'bold', fontSize: '1rem' }}>Step 1: Find the LCM of denominators 4 and 8</div>
                  <div style={{ fontSize: '0.95rem', color: 'var(--text-muted)' }}>Multiples of 4: 4, <strong>8</strong>, 12... Multiples of 8: <strong>8</strong>, 16... Common denominator is <strong>8</strong>.</div>
                </div>

                <div style={{ borderLeft: '4px solid var(--color-secondary)', paddingLeft: '12px' }}>
                  <div style={{ fontWeight: 'bold', fontSize: '1rem' }}>Step 2: Rename into equivalent fractions</div>
                  <div style={{ fontSize: '0.95rem', color: 'var(--text-muted)' }}>Multiply 1/4 by 2/2 &rarr; <strong>2/8</strong>. (3/8 already has denominator 8).</div>
                </div>

                <div style={{ borderLeft: '4px solid var(--color-accent)', paddingLeft: '12px' }}>
                  <div style={{ fontWeight: 'bold', fontSize: '1rem' }}>Step 3: Add numerators only</div>
                  <div style={{ fontSize: '0.95rem', color: 'var(--text-muted)' }}>2/8 + 3/8 = <strong>5/8</strong> (in simplest form).</div>
                </div>
              </div>
            </WobblyCard>

            {/* Section 3: Check for Understanding (Interactive Practice) */}
            <WobblyCard decoration="tack-green" style={{ padding: '26px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                <span style={{ fontSize: '1.6rem' }}>🎯</span>
                <h2 style={{ fontSize: '1.35rem', fontFamily: 'var(--font-heading)', margin: 0, color: 'var(--text-main)' }}>
                  3. Quick Check for Understanding
                </h2>
              </div>
              <p style={{ fontSize: '1.05rem', color: 'var(--text-main)', margin: '0 0 16px 0' }}>
                What is <strong>1/3 + 1/6</strong> in simplest form?
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '16px' }}>
                {['2/9', '1/2', '3/6', '2/6'].map((opt) => (
                  <button
                    key={opt}
                    onClick={() => handlePracticeSubmit(opt)}
                    style={{
                      padding: '12px',
                      borderRadius: '8px',
                      border: selectedPracticeAnswer === opt ? '2px solid var(--color-primary)' : '2px solid var(--border-dark)',
                      background: selectedPracticeAnswer === opt ? '#eef2ff' : '#fff',
                      fontSize: '1.1rem',
                      fontWeight: 'bold',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    {opt}
                  </button>
                ))}
              </div>

              {practiceFeedback && (
                <div style={{
                  padding: '14px 18px',
                  borderRadius: '10px',
                  background: practiceFeedback.isCorrect ? '#ecfdf5' : '#fffbeb',
                  border: practiceFeedback.isCorrect ? '1.5px solid #10b981' : '1.5px solid #f59e0b',
                  color: practiceFeedback.isCorrect ? '#047857' : '#b45309',
                  fontSize: '0.98rem',
                  lineHeight: 1.4
                }}>
                  {practiceFeedback.message}
                </div>
              )}
            </WobblyCard>

          </div>

          {/* Right Column: Embedded AI Socratic Sidecar */}
          <WobblyCard decoration="tack-red" style={{ padding: '24px', background: '#fff', position: 'sticky', top: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.5rem' }}>🤖</span>
                <h3 style={{ fontSize: '1.25rem', fontFamily: 'var(--font-heading)', margin: 0, color: 'var(--text-main)' }}>
                  AI Socratic Tutor
                </h3>
              </div>
              <HandBadge variant="blue">Lesson Assistant</HandBadge>
            </div>

            {/* Mode Switcher */}
            <div style={{ display: 'flex', gap: '6px', marginBottom: '14px' }}>
              <button
                type="button"
                onClick={() => setTutorMode('socratic')}
                style={{
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontSize: '0.78rem',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  border: tutorMode === 'socratic' ? '1.5px solid var(--color-primary)' : '1px solid var(--border-light)',
                  background: tutorMode === 'socratic' ? '#eef2ff' : '#fff'
                }}
              >
                Socratic 💡
              </button>
              <button
                type="button"
                onClick={() => setTutorMode('hint')}
                style={{
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontSize: '0.78rem',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  border: tutorMode === 'hint' ? '1.5px solid var(--color-primary)' : '1px solid var(--border-light)',
                  background: tutorMode === 'hint' ? '#eef2ff' : '#fff'
                }}
              >
                Hint 🔍
              </button>
              <button
                type="button"
                onClick={() => setTutorMode('explanation')}
                style={{
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontSize: '0.78rem',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  border: tutorMode === 'explanation' ? '1.5px solid var(--color-primary)' : '1px solid var(--border-light)',
                  background: tutorMode === 'explanation' ? '#eef2ff' : '#fff'
                }}
              >
                Explain 📖
              </button>
            </div>

            {/* Chat Dialog Stream */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
              maxHeight: '360px',
              overflowY: 'auto',
              paddingRight: '6px',
              marginBottom: '14px'
            }}>
              {tutorMessages.map((m, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '10px 14px',
                    borderRadius: '10px',
                    fontSize: '0.92rem',
                    lineHeight: 1.4,
                    alignSelf: m.role === 'student' ? 'flex-end' : 'flex-start',
                    background: m.role === 'student' ? '#eef2ff' : '#f8fafc',
                    border: m.role === 'student' ? '1px solid #c7d2fe' : '1px solid var(--border-light)',
                    maxWidth: '90%'
                  }}
                >
                  <div style={{ fontSize: '0.72rem', fontWeight: 'bold', color: 'var(--text-muted)', marginBottom: '2px' }}>
                    {m.role === 'student' ? 'You' : 'AI Socratic Tutor'}
                  </div>
                  {m.text}
                </div>
              ))}
              {isTutorLoading && (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                  AI Tutor is thinking... ⏳
                </div>
              )}
            </div>

            {/* Message Input Box */}
            <form onSubmit={handleSendTutorMessage} style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                placeholder={tutorMode === 'hint' ? 'Ask for a hint...' : 'Ask a question...'}
                value={tutorQuery}
                onChange={(e) => setTutorQuery(e.target.value)}
                style={{
                  flex: 1,
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1.5px solid var(--border-dark)',
                  fontSize: '0.9rem'
                }}
              />
              <button
                type="submit"
                disabled={isTutorLoading || !tutorQuery.trim()}
                style={{
                  padding: '10px 14px',
                  background: 'var(--color-primary)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 'bold',
                  cursor: isTutorLoading ? 'not-allowed' : 'pointer'
                }}
              >
                Ask 🚀
              </button>
            </form>
          </WobblyCard>

        </div>

      </div>
    </AuthenticatedShell>
  );
}
