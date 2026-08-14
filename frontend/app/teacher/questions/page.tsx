'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import AuthenticatedShell from '@/components/AuthenticatedShell';
import { apiClient } from '@/lib/api-client';
import {
  WobblyCard,
  WobblyButton,
  HandBadge,
  ScribbleUnderline
} from '@/lib/HandDrawnComponents';

interface QuestionItem {
  id: string;
  question_type: string;
  difficulty: number;
  question_text: string;
  options: string[];
  correct_answer: any;
  explanation: string;
  generation_method: 'MANUAL' | 'AI_GENERATED';
  validation_status: 'PROPOSED' | 'APPROVED' | 'REJECTED';
  concept_name: string;
}

export default function TeacherQuestionBankPage() {
  const [questions, setQuestions] = useState<QuestionItem[]>([
    {
      id: 'q-101',
      question_type: 'mcq',
      difficulty: 3,
      question_text: 'What is 1/3 + 1/6 in simplest form?',
      options: ['1/2', '2/9', '3/6', '2/6'],
      correct_answer: '1/2',
      explanation: 'Convert 1/3 to 2/6 using LCD 6. 2/6 + 1/6 = 3/6 = 1/2.',
      generation_method: 'MANUAL',
      validation_status: 'APPROVED',
      concept_name: 'Adding Fractions with Unlike Denominators'
    },
    {
      id: 'q-102',
      question_type: 'mcq',
      difficulty: 4,
      question_text: 'Sarah poured 3/4 cup of milk and added 2/8 cup of water. What is the total volume in cups?',
      options: ['1 cup', '5/12 cup', '5/8 cup', '6/8 cup'],
      correct_answer: '1 cup',
      explanation: 'Convert 3/4 to 6/8. 6/8 + 2/8 = 8/8 = 1 whole cup.',
      generation_method: 'AI_GENERATED',
      validation_status: 'PROPOSED',
      concept_name: 'Adding Fractions with Unlike Denominators'
    },
    {
      id: 'q-103',
      question_type: 'numeric',
      difficulty: 2,
      question_text: 'Find the Least Common Multiple (LCM) of the numbers 4 and 6.',
      options: [],
      correct_answer: '12',
      explanation: 'Multiples of 4: 4, 8, 12. Multiples of 6: 6, 12. Smallest common multiple is 12.',
      generation_method: 'AI_GENERATED',
      validation_status: 'APPROVED',
      concept_name: 'Least Common Denominators (LCM)'
    }
  ]);

  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationTopic, setGenerationTopic] = useState('Adding Unlike Fractions (LCM)');
  const [generationDifficulty, setGenerationDifficulty] = useState(3);
  const [showGenModal, setShowGenModal] = useState(false);

  async function handleApprove(qId: string) {
    try {
      await apiClient.post(`/api/v1/questions/${qId}/approve`, {});
    } catch (e) {
      // Local update
    }
    setQuestions(prev => prev.map(q => q.id === qId ? { ...q, validation_status: 'APPROVED' } : q));
  }

  async function handleReject(qId: string) {
    try {
      await apiClient.post(`/api/v1/questions/${qId}/reject`, {});
    } catch (e) {
      // Local update
    }
    setQuestions(prev => prev.map(q => q.id === qId ? { ...q, validation_status: 'REJECTED' } : q));
  }

  async function handleAIGenerateQuestion() {
    setIsGenerating(true);
    try {
      const res = await apiClient.post<any>('/api/v1/questions/generate', {
        concept_id: '00000000-0000-0000-0000-000000000010',
        difficulty: generationDifficulty,
        question_type: 'mcq'
      });

      if (res.data) {
        const newQ: QuestionItem = {
          id: res.data.id || `q-ai-${Date.now()}`,
          question_type: res.data.question_type || 'mcq',
          difficulty: generationDifficulty,
          question_text: res.data.question_text || `A recipe requires 2/5 cup sugar and 3/10 cup flour. How much total mixture in cups?`,
          options: res.data.options || ['7/10', '5/15', '1/2', '4/5'],
          correct_answer: res.data.correct_answer || '7/10',
          explanation: res.data.explanation || '2/5 is equivalent to 4/10. 4/10 + 3/10 = 7/10.',
          generation_method: 'AI_GENERATED',
          validation_status: 'PROPOSED',
          concept_name: generationTopic
        };
        setQuestions(prev => [newQ, ...prev]);
        setShowGenModal(false);
      }
    } catch (e) {
      // Simulated generation
      const newQ: QuestionItem = {
        id: `q-ai-${Date.now()}`,
        question_type: 'mcq',
        difficulty: generationDifficulty,
        question_text: `A recipe requires 2/5 cup sugar and 3/10 cup flour. What is the total mixture in cups?`,
        options: ['7/10', '5/15', '1/2', '4/5'],
        correct_answer: '7/10',
        explanation: 'Convert 2/5 to 4/10 using common denominator 10. 4/10 + 3/10 = 7/10.',
        generation_method: 'AI_GENERATED',
        validation_status: 'PROPOSED',
        concept_name: generationTopic
      };
      setQuestions(prev => [newQ, ...prev]);
      setShowGenModal(false);
    } finally {
      setIsGenerating(false);
    }
  }

  const filteredQuestions = questions.filter(q => {
    if (filterType !== 'all' && q.question_type !== filterType) return false;
    if (filterStatus !== 'all' && q.validation_status !== filterStatus) return false;
    return true;
  });

  return (
    <AuthenticatedShell allowedRoles={['Teacher', 'OrgAdmin', 'SchoolAdmin', 'SuperAdmin']} title="Question Bank & AI Studio">
      <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
        
        {/* Header Ribbon */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <h1 style={{ fontSize: '2.2rem', fontFamily: 'var(--font-heading)', color: 'var(--text-main)', margin: 0 }}>
                📑 Question Bank &amp; AI Authoring Studio
              </h1>
              <HandBadge variant="purple">Human-in-the-Loop Governance</HandBadge>
            </div>
            <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-handwriting)', fontSize: '1.15rem', margin: 0 }}>
              Browse curated questions, generate new items with AI assistance, and review/approve answer keys before assigning.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <Link href="/teacher/dashboard">
              <WobblyButton variant="secondary">
                ← Dashboard
              </WobblyButton>
            </Link>
            <WobblyButton variant="primary" onClick={() => setShowGenModal(true)}>
              🤖 AI Question Generator
            </WobblyButton>
          </div>
        </div>

        {/* AI Generation Modal Post-It */}
        {showGenModal && (
          <WobblyCard decoration="tape" style={{ padding: '26px', background: '#fff', border: '3px solid var(--color-primary)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.6rem' }}>✨</span>
                <h3 style={{ fontSize: '1.3rem', fontFamily: 'var(--font-heading)', margin: 0 }}>
                  Generate Standards-Aligned Assessment Question
                </h3>
              </div>
              <button
                onClick={() => setShowGenModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '1.3rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.88rem', fontWeight: 'bold', marginBottom: '6px' }}>
                  Target Concept / Topic:
                </label>
                <select
                  value={generationTopic}
                  onChange={(e) => setGenerationTopic(e.target.value)}
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1.5px solid var(--border-dark)' }}
                >
                  <option value="Adding Unlike Fractions (LCM)">Adding Unlike Fractions (LCM)</option>
                  <option value="Equivalent Fractions on a Number Line">Equivalent Fractions on a Number Line</option>
                  <option value="Mixed Numbers Arithmetic">Mixed Numbers Arithmetic</option>
                  <option value="Fraction Multiplication Area Models">Fraction Multiplication Area Models</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.88rem', fontWeight: 'bold', marginBottom: '6px' }}>
                  Difficulty Level (1 = Foundations, 5 = Challenge):
                </label>
                <select
                  value={generationDifficulty}
                  onChange={(e) => setGenerationDifficulty(Number(e.target.value))}
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1.5px solid var(--border-dark)' }}
                >
                  <option value={1}>Level 1 — Basic Conceptual Identification</option>
                  <option value={2}>Level 2 — Single-Step Numerical</option>
                  <option value={3}>Level 3 — Standard Multi-Step (Grade 6 Core)</option>
                  <option value={4}>Level 4 — Word Problem Application</option>
                  <option value={5}>Level 5 — Advanced Multi-Step Proof</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <WobblyButton variant="secondary" onClick={() => setShowGenModal(false)}>
                Cancel
              </WobblyButton>
              <WobblyButton variant="accent" onClick={handleAIGenerateQuestion} disabled={isGenerating}>
                {isGenerating ? 'Generating Question with Rubric... ⏳' : 'Generate Proposed Question 🚀'}
              </WobblyButton>
            </div>
          </WobblyCard>
        )}

        {/* Filter Controls Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 'bold', color: 'var(--text-muted)' }}>Filter Status:</span>
            {['all', 'PROPOSED', 'APPROVED', 'REJECTED'].map(st => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  fontSize: '0.85rem',
                  fontWeight: filterStatus === st ? 'bold' : 'normal',
                  border: filterStatus === st ? '2px solid var(--color-primary)' : '1px solid var(--border-light)',
                  background: filterStatus === st ? '#eef2ff' : '#fff',
                  cursor: 'pointer'
                }}
              >
                {st === 'all' ? 'All Items' : st}
              </button>
            ))}
          </div>

          <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Showing {filteredQuestions.length} Questions
          </span>
        </div>

        {/* Question Cards List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {filteredQuestions.map((q) => {
            const isProposed = q.validation_status === 'PROPOSED';
            return (
              <WobblyCard
                key={q.id}
                decoration={isProposed ? 'tack-red' : 'none'}
                style={{
                  padding: '24px',
                  background: '#fff',
                  borderLeft: isProposed ? '6px solid #f59e0b' : '6px solid #10b981'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--color-primary-dark)' }}>
                      #{q.id}
                    </span>
                    <HandBadge variant="blue">{q.concept_name}</HandBadge>
                    <HandBadge variant="yellow">Difficulty: Level {q.difficulty}</HandBadge>
                    {q.generation_method === 'AI_GENERATED' && (
                      <span style={{ background: '#f3e8ff', color: '#7e22ce', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold' }}>
                        🤖 AI Generated Proposal
                      </span>
                    )}
                  </div>

                  <HandBadge variant={q.validation_status === 'APPROVED' ? 'green' : q.validation_status === 'PROPOSED' ? 'yellow' : 'red'}>
                    {q.validation_status}
                  </HandBadge>
                </div>

                <p style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'var(--text-main)', margin: '0 0 12px 0' }}>
                  {q.question_text}
                </p>

                {q.options.length > 0 && (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '8px', marginBottom: '14px' }}>
                    {q.options.map((opt, oIdx) => (
                      <div
                        key={oIdx}
                        style={{
                          padding: '8px 12px',
                          borderRadius: '6px',
                          border: opt === q.correct_answer ? '2px solid #10b981' : '1px solid var(--border-light)',
                          background: opt === q.correct_answer ? '#ecfdf5' : '#f8fafc',
                          fontWeight: opt === q.correct_answer ? 'bold' : 'normal',
                          fontSize: '0.92rem'
                        }}
                      >
                        {String.fromCharCode(65 + oIdx)}. {opt} {opt === q.correct_answer && '✓ (Correct)'}
                      </div>
                    ))}
                  </div>
                )}

                <div style={{ background: '#f8fafc', padding: '10px 14px', borderRadius: '8px', fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '14px' }}>
                  <strong>Rubric & Explanation:</strong> {q.explanation}
                </div>

                {/* Human-in-the-Loop Governance Action Bar */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', alignItems: 'center' }}>
                  {isProposed ? (
                    <>
                      <span style={{ fontSize: '0.85rem', color: '#b45309', fontWeight: 'bold', marginRight: '8px' }}>
                        ⚠️ Requires Teacher Review before Student Availability
                      </span>
                      <WobblyButton variant="secondary" onClick={() => handleReject(q.id)}>
                        Reject ❌
                      </WobblyButton>
                      <WobblyButton variant="primary" onClick={() => handleApprove(q.id)}>
                        Approve Question ✅
                      </WobblyButton>
                    </>
                  ) : (
                    <span style={{ fontSize: '0.85rem', color: '#047857', fontWeight: 'bold' }}>
                      ✓ Verified &amp; Ready for Assessment Assignment
                    </span>
                  )}
                </div>
              </WobblyCard>
            );
          })}
        </div>

      </div>
    </AuthenticatedShell>
  );
}
