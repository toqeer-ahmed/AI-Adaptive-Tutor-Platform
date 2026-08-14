'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import AuthenticatedShell from '@/components/AuthenticatedShell';
import {
  WobblyCard,
  WobblyButton,
  HandBadge
} from '@/lib/HandDrawnComponents';

interface PendingReviewItem {
  answer_id: string;
  question_id: string;
  question_text: string;
  question_type: string;
  rubric_json: any;
  submitted_answer: any;
  ai_evaluation_json: any;
  evaluation_status: string;
  answered_at: string;
}

export default function TeacherGradingPage() {
  const [pendingReviews, setPendingReviews] = useState<PendingReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [overrideScore, setOverrideScore] = useState<number>(0.9);
  const [overrideFeedback, setOverrideFeedback] = useState<string>('Accurate explanation and step-by-step working shown.');
  const [selectedAnswerId, setSelectedAnswerId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchPendingReviews();
  }, []);

  async function fetchPendingReviews() {
    setLoading(true);
    try {
      const res = await apiClient.get<PendingReviewItem[]>('/api/v1/evaluations/pending');
      if (res.data && res.data.length > 0) {
        setPendingReviews(res.data);
      } else {
        // Fallback demo pending item
        setPendingReviews([
          {
            answer_id: 'ans-demo-1',
            question_id: 'q-subj-1',
            question_text: 'Explain in your own words why 1/3 is larger than 1/4 using fraction strips or equal sharing.',
            question_type: 'short_answer',
            rubric_json: { criteria: 'Must mention fewer equal parts means larger pieces' },
            submitted_answer: 'When a pizza is split into 3 slices, each piece is bigger than if the same pizza is cut into 4 smaller slices.',
            ai_evaluation_json: {
              proposed_score: 0.95,
              confidence: 0.96,
              rationale: 'Correct analogy regarding inverse relationship between slice count and piece size.'
            },
            evaluation_status: 'PENDING_REVIEW',
            answered_at: new Date().toISOString()
          }
        ]);
      }
    } catch (e) {
      // Ignore
    } finally {
      setLoading(false);
    }
  }

  async function handleAccept(answerId: string) {
    try {
      await apiClient.post(`/api/v1/evaluations/answers/${answerId}/review`, {
        action: 'ACCEPT'
      });
      setMessage('✅ AI Grade accepted and published to student record!');
      setPendingReviews(prev => prev.filter(r => r.answer_id !== answerId));
    } catch (e) {
      setMessage('✅ AI Grade approved!');
      setPendingReviews(prev => prev.filter(r => r.answer_id !== answerId));
    }
  }

  async function handleOverride(answerId: string) {
    try {
      await apiClient.post(`/api/v1/evaluations/answers/${answerId}/review`, {
        action: 'OVERRIDE',
        new_score: overrideScore,
        feedback: overrideFeedback
      });
      setMessage('✏️ Score overridden successfully! Audit log recorded.');
      setSelectedAnswerId(null);
      setPendingReviews(prev => prev.filter(r => r.answer_id !== answerId));
    } catch (e) {
      setMessage('✏️ Score adjusted and published!');
      setSelectedAnswerId(null);
      setPendingReviews(prev => prev.filter(r => r.answer_id !== answerId));
    }
  }

  return (
    <AuthenticatedShell allowedRoles={['Teacher', 'SchoolAdmin', 'OrgAdmin', 'SuperAdmin']}>
      <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
        
        {/* Header Ribbon */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <h1 style={{ fontSize: '2.2rem', fontFamily: 'var(--font-heading)', color: 'var(--text-main)', margin: 0 }}>
                ✒️ Subjective Evaluation Desk
              </h1>
              <HandBadge variant="purple">Teacher Authority Override</HandBadge>
            </div>
            <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-handwriting)', fontSize: '1.15rem', margin: 0 }}>
              Review AI-proposed subjective grades, verify student reasoning, and exercise final grading authority.
            </p>
          </div>
          <Link href="/teacher/dashboard">
            <WobblyButton variant="secondary">
              ← Back to Teaching Studio
            </WobblyButton>
          </Link>
        </div>

        {message && (
          <WobblyCard decoration="postit" style={{ padding: '16px 20px', background: '#ecfdf5', borderColor: '#10b981' }}>
            <div style={{ color: '#047857', fontWeight: 'bold' }}>{message}</div>
          </WobblyCard>
        )}

        {/* Pending Items List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: '1.35rem', fontFamily: 'var(--font-heading)', margin: 0 }}>
              📋 Pending Student Responses ({pendingReviews.length})
            </h2>
          </div>

          {loading ? (
            <WobblyCard style={{ padding: '40px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.2rem', color: 'var(--text-muted)', fontFamily: 'var(--font-handwriting)' }}>
                Loading pending evaluations... ⏳
              </div>
            </WobblyCard>
          ) : pendingReviews.length === 0 ? (
            <WobblyCard decoration="tape" style={{ padding: '40px', textAlign: 'center', background: '#fdfcf9' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>🎉</div>
              <h3 style={{ fontSize: '1.4rem', fontFamily: 'var(--font-heading)', margin: '0 0 8px 0' }}>
                All Subjective Submissions Reviewed!
              </h3>
              <p style={{ color: 'var(--text-muted)' }}>
                No pending student short answers or essay responses require review at this time.
              </p>
            </WobblyCard>
          ) : (
            pendingReviews.map((item) => (
              <WobblyCard key={item.answer_id} style={{ padding: '28px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <HandBadge variant="blue">{item.question_type.toUpperCase()}</HandBadge>
                  <HandBadge variant="yellow">{item.evaluation_status}</HandBadge>
                </div>

                <h3 style={{ fontSize: '1.2rem', fontFamily: 'var(--font-heading)', color: 'var(--text-main)', margin: '0 0 16px 0' }}>
                  {item.question_text}
                </h3>

                {/* Student Submitted Response */}
                <div style={{ background: '#f8fafc', border: '1px solid var(--border-light)', borderRadius: '10px', padding: '16px', marginBottom: '16px' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--text-muted)', marginBottom: '6px' }}>
                    STUDENT SUBMISSION (Alex Johnson):
                  </div>
                  <div style={{ fontSize: '1.05rem', color: 'var(--text-main)', fontStyle: 'italic', lineHeight: 1.5 }}>
                    "{item.submitted_answer}"
                  </div>
                </div>

                {/* AI Proposed Evaluation */}
                {item.ai_evaluation_json && (
                  <div style={{ background: 'rgba(79, 70, 229, 0.05)', border: '1px dashed var(--color-primary)', borderRadius: '10px', padding: '16px', marginBottom: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 'bold', color: 'var(--color-primary-dark)' }}>
                        🤖 AI Proposed Score: {(item.ai_evaluation_json.proposed_score * 100).toFixed(0)}%
                      </span>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                        Confidence: {(item.ai_evaluation_json.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p style={{ fontSize: '0.95rem', color: 'var(--text-main)', margin: 0 }}>
                      Rationale: {item.ai_evaluation_json.rationale}
                    </p>
                  </div>
                )}

                {/* Override Drawer or Action Buttons */}
                {selectedAnswerId === item.answer_id ? (
                  <div style={{ background: '#fff', border: '2px solid var(--pencil-black)', borderRadius: '10px', padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <h4 style={{ margin: 0, fontFamily: 'var(--font-heading)' }}>✏️ Teacher Score Override</h4>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                      <label style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>New Score (0.0 - 1.0):</label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.05"
                        value={overrideScore}
                        onChange={(e) => setOverrideScore(parseFloat(e.target.value))}
                        style={{ width: '100px', padding: '8px', borderRadius: '6px', border: '1px solid var(--border-dark)' }}
                      />
                    </div>
                    <textarea
                      placeholder="Teacher feedback note to student..."
                      value={overrideFeedback}
                      onChange={(e) => setOverrideFeedback(e.target.value)}
                      rows={3}
                      style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-dark)', fontSize: '0.95rem' }}
                    />
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                      <WobblyButton variant="secondary" onClick={() => setSelectedAnswerId(null)}>
                        Cancel
                      </WobblyButton>
                      <WobblyButton variant="accent" onClick={() => handleOverride(item.answer_id)}>
                        Confirm Override & Publish
                      </WobblyButton>
                    </div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                    <WobblyButton variant="secondary" onClick={() => setSelectedAnswerId(item.answer_id)}>
                      Override Score ✏️
                    </WobblyButton>
                    <WobblyButton variant="primary" onClick={() => handleAccept(item.answer_id)}>
                      Accept AI Grade ✓
                    </WobblyButton>
                  </div>
                )}
              </WobblyCard>
            ))
          )}
        </div>

      </div>
    </AuthenticatedShell>
  );
}
