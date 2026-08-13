'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface Question {
  id: string;
  question_type: string;
  question_text: string;
  options: string[] | null;
}

interface Assessment {
  id: string;
  title: string;
  assessment_type: string;
  max_attempts: number;
  questions: Question[];
}

interface AttemptResult {
  attempt_id: string;
  status: string;
  score: number;
  max_score: number;
  percentage: number;
}

export default function StudentAssessmentPage() {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [activeAssessment, setActiveAssessment] = useState<Assessment | null>(null);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [attemptResult, setAttemptResult] = useState<AttemptResult | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchAssessments();
  }, []);

  async function fetchAssessments() {
    const res = await apiClient.get<Assessment[]>('/api/v1/assessments');
    if (res.data) {
      setAssessments(res.data);
    }
  }

  async function handleStartAssessment(ass: Assessment) {
    setActiveAssessment(ass);
    setAttemptResult(null);
    setAnswers({});
    setMessage(null);

    const res = await apiClient.post<{ attempt_id: string }>(`/api/v1/assessments/${ass.id}/start`, {});
    if (res.error) {
      setMessage(`Start Error: ${res.error.message}`);
    } else if (res.data) {
      setAttemptId(res.data.attempt_id);
    }
  }

  async function handleAnswerSubmit(questionId: string, value: any) {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
    if (!attemptId) return;

    await apiClient.post(`/api/v1/attempts/${attemptId}/answer`, {
      question_id: questionId,
      submitted_answer: value
    });
  }

  async function handleFinishAssessment() {
    if (!attemptId) return;
    const res = await apiClient.post<AttemptResult>(`/api/v1/attempts/${attemptId}/submit`, {});
    if (res.error) {
      setMessage(`Submit Error: ${res.error.message}`);
    } else if (res.data) {
      setAttemptResult(res.data);
      setAttemptId(null);
    }
  }

  return (
    <div style={{ padding: '32px', maxWidth: '900px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '2rem', color: '#818cf8', marginBottom: '8px' }}>
          Student Assessment Player
        </h1>
        <p style={{ color: '#94a3b8' }}>
          Complete quizzes and assignments with instant deterministic grading and attempt tracking.
        </p>
      </header>

      {message && (
        <div style={{ padding: '12px', borderRadius: '8px', backgroundColor: '#1e293b', border: '1px solid #6366f1', marginBottom: '20px' }}>
          {message}
        </div>
      )}

      {/* Available Assessments List */}
      {!activeAssessment && (
        <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '1.3rem', marginBottom: '16px' }}>Assigned Quizzes</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {assessments.map((ass) => (
              <div key={ass.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px', background: '#0f172a', borderRadius: '8px' }}>
                <div>
                  <div style={{ fontWeight: 'bold', color: '#38bdf8', fontSize: '1.1rem' }}>{ass.title}</div>
                  <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                    Type: {ass.assessment_type} • Questions: {ass.questions.length} • Max Attempts: {ass.max_attempts}
                  </div>
                </div>
                <button
                  onClick={() => handleStartAssessment(ass)}
                  style={{ padding: '10px 20px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}
                >
                  Start Assessment
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Active Assessment Player */}
      {activeAssessment && attemptId && !attemptResult && (
        <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '1.4rem', color: '#38bdf8', marginBottom: '20px' }}>
            {activeAssessment.title}
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {activeAssessment.questions.map((q, idx) => (
              <div key={q.id} style={{ padding: '16px', background: '#0f172a', borderRadius: '8px', borderLeft: '4px solid #6366f1' }}>
                <div style={{ fontWeight: 'bold', marginBottom: '12px', fontSize: '1.05rem' }}>
                  Q{idx + 1}. {q.question_text}
                </div>

                {/* Question Type Options */}
                {q.question_type === 'mcq' && q.options && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {q.options.map((opt) => (
                      <label key={opt} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', background: '#1e293b', padding: '8px 12px', borderRadius: '6px' }}>
                        <input
                          type="radio"
                          name={`q_${q.id}`}
                          value={opt}
                          checked={answers[q.id] === opt}
                          onChange={(e) => handleAnswerSubmit(q.id, e.target.value)}
                        />
                        {opt}
                      </label>
                    ))}
                  </div>
                )}

                {q.question_type === 'numeric' && (
                  <input
                    type="text"
                    placeholder="Enter numeric answer (e.g. 12 or 3/4)"
                    value={answers[q.id] || ''}
                    onChange={(e) => handleAnswerSubmit(q.id, e.target.value)}
                    style={{ width: '100%', padding: '10px', background: '#1e293b', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }}
                  />
                )}
              </div>
            ))}

            <button
              onClick={handleFinishAssessment}
              style={{ padding: '14px', background: '#10b981', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 'bold', fontSize: '1.1rem', cursor: 'pointer' }}
            >
              Submit Assessment & View Score
            </button>
          </div>
        </section>
      )}

      {/* Score Card Result */}
      {attemptResult && (
        <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '32px', textAlign: 'center' }}>
          <h2 style={{ fontSize: '1.8rem', color: '#34d399', marginBottom: '12px' }}>
            🎉 Assessment Submitted!
          </h2>
          <div style={{ fontSize: '3rem', fontWeight: 'bold', color: '#38bdf8', marginBottom: '12px' }}>
            {attemptResult.score} / {attemptResult.max_score} ({attemptResult.percentage.toFixed(1)}%)
          </div>
          <p style={{ color: '#94a3b8', marginBottom: '24px' }}>
            Your answers have been deterministically evaluated against approved curriculum rules.
          </p>
          <button
            onClick={() => setActiveAssessment(null)}
            style={{ padding: '10px 24px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            Return to Assessments
          </button>
        </section>
      )}
    </div>
  );
}
