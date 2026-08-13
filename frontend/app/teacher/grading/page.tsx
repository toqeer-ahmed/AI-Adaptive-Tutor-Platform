'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

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
  const [overrideFeedback, setOverrideFeedback] = useState<string>('Accurate explanation and work shown.');
  const [selectedAnswerId, setSelectedAnswerId] = useState<string | null>(null);

  useEffect(() => {
    fetchPendingReviews();
  }, []);

  async function fetchPendingReviews() {
    const res = await apiClient.get<PendingReviewItem[]>('/api/v1/evaluations/pending');
    if (res.data) {
      setPendingReviews(res.data);
    }
    setLoading(false);
  }

  async function handleAccept(answerId: string) {
    const res = await apiClient.post(`/api/v1/evaluations/answers/${answerId}/review`, {
      action: 'ACCEPT'
    });
    if (!res.error) {
      alert('✅ AI Grade accepted and published to student!');
      fetchPendingReviews();
    }
  }

  async function handleOverride(answerId: string) {
    const res = await apiClient.post(`/api/v1/evaluations/answers/${answerId}/review`, {
      action: 'OVERRIDE',
      new_score: overrideScore,
      feedback: overrideFeedback
    });
    if (!res.error) {
      alert('✏️ Score overridden successfully! Audit log created.');
      setSelectedAnswerId(null);
      fetchPendingReviews();
    }
  }

  return (
    <div style={{ padding: '32px', maxWidth: '1000px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '2rem', color: '#38bdf8', marginBottom: '8px' }}>
          Teacher Subjective Grading & Review Workspace
        </h1>
        <p style={{ color: '#94a3b8' }}>
          Review AI-proposed scores, inspect rubric criteria, accept proposals, or override grades with explicit audit logging.
        </p>
      </header>

      {/* Pending Reviews List */}
      <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
        <h2 style={{ fontSize: '1.3rem', marginBottom: '16px' }}>Pending Teacher Reviews</h2>

        {loading ? (
          <p style={{ color: '#94a3b8' }}>Loading pending reviews...</p>
        ) : pendingReviews.length === 0 ? (
          <div style={{ padding: '20px', background: '#0f172a', borderRadius: '8px', textAlign: 'center', color: '#94a3b8' }}>
            ✅ All student subjective submissions have been reviewed and graded!
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {pendingReviews.map((item) => {
              const aiEval = item.ai_evaluation_json || {};
              const confPct = Math.round((aiEval.confidence || 0.85) * 100);

              return (
                <div key={item.answer_id} style={{ padding: '20px', background: '#0f172a', borderRadius: '10px', border: '1px solid #334155' }}>
                  <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '4px' }}>
                    Type: {item.question_type.toUpperCase()} | Answered: {new Date(item.answered_at).toLocaleTimeString()}
                  </div>

                  <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#f8fafc', marginBottom: '12px' }}>
                    Q: {item.question_text}
                  </div>

                  <div style={{ padding: '12px', background: '#1e293b', borderRadius: '6px', marginBottom: '12px', borderLeft: '3px solid #38bdf8' }}>
                    <div style={{ fontSize: '0.8rem', color: '#38bdf8', fontWeight: 'bold', marginBottom: '2px' }}>
                      Student Submission:
                    </div>
                    <div style={{ fontSize: '0.95rem', color: '#f8fafc' }}>
                      "{String(item.submitted_answer)}"
                    </div>
                  </div>

                  {/* AI Evaluation Proposal Box */}
                  <div style={{ padding: '16px', background: '#1e1b4b', borderRadius: '8px', border: '1px solid #6366f1', marginBottom: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#a5b4fc' }}>
                        🤖 AI Evaluation Proposal
                      </span>
                      <span style={{ fontSize: '0.8rem', color: '#34d399', fontWeight: 'bold' }}>
                        {confPct}% Confidence
                      </span>
                    </div>

                    <div style={{ fontSize: '0.85rem', color: '#cbd5e1', marginBottom: '4px' }}>
                      <strong>Proposed Score:</strong> {aiEval.score != null ? `${aiEval.score * 100}%` : 'N/A'}
                    </div>

                    <div style={{ fontSize: '0.85rem', color: '#cbd5e1', marginBottom: '8px' }}>
                      <strong>Feedback:</strong> "{aiEval.feedback || 'Good effort.'}"
                    </div>

                    {aiEval.rubric_criteria_scores && (
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                        Rubric Criteria: {JSON.stringify(aiEval.rubric_criteria_scores)}
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <button
                      onClick={() => handleAccept(item.answer_id)}
                      style={{
                        padding: '10px 18px',
                        backgroundColor: '#16a34a',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '6px',
                        fontWeight: 'bold',
                        cursor: 'pointer'
                      }}
                    >
                      ✅ Accept AI Grade
                    </button>

                    <button
                      onClick={() => setSelectedAnswerId(selectedAnswerId === item.answer_id ? null : item.answer_id)}
                      style={{
                        padding: '10px 18px',
                        backgroundColor: '#ca8a04',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '6px',
                        fontWeight: 'bold',
                        cursor: 'pointer'
                      }}
                    >
                      ✏️ Override Score
                    </button>
                  </div>

                  {/* Override Form */}
                  {selectedAnswerId === item.answer_id && (
                    <div style={{ marginTop: '16px', padding: '16px', background: '#1e293b', borderRadius: '8px', border: '1px solid #eab308' }}>
                      <h4 style={{ fontSize: '0.95rem', color: '#fef08a', marginBottom: '12px' }}>Teacher Grade Override</h4>
                      <div style={{ marginBottom: '10px' }}>
                        <label style={{ fontSize: '0.85rem', display: 'block', marginBottom: '4px' }}>New Score (0.0 to 1.0):</label>
                        <input
                          type="number"
                          step="0.05"
                          min="0"
                          max="1"
                          value={overrideScore}
                          onChange={(e) => setOverrideScore(parseFloat(e.target.value))}
                          style={{ padding: '8px', borderRadius: '4px', border: '1px solid #475569', background: '#0f172a', color: '#fff', width: '120px' }}
                        />
                      </div>
                      <div style={{ marginBottom: '12px' }}>
                        <label style={{ fontSize: '0.85rem', display: 'block', marginBottom: '4px' }}>Feedback Reason:</label>
                        <input
                          type="text"
                          value={overrideFeedback}
                          onChange={(e) => setOverrideFeedback(e.target.value)}
                          style={{ padding: '8px', borderRadius: '4px', border: '1px solid #475569', background: '#0f172a', color: '#fff', width: '100%' }}
                        />
                      </div>
                      <button
                        onClick={() => handleOverride(item.answer_id)}
                        style={{ padding: '8px 16px', backgroundColor: '#eab308', color: '#000', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}
                      >
                        Submit Override & Log Audit Event
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
