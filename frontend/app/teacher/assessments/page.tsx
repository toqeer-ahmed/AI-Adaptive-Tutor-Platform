'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface QuestionItem {
  id: string;
  question_type: string;
  question_text: string;
  options: string[] | null;
  correct_answer: any;
  validation_status: string;
}

export default function TeacherAssessmentPage() {
  const [questions, setQuestions] = useState<QuestionItem[]>([]);
  const [selectedQIds, setSelectedQIds] = useState<string[]>([]);
  const [quizTitle, setQuizTitle] = useState('Grade 6 Fractions & Decimals Quiz');
  const [isGenerating, setIsGenerating] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchQuestions();
  }, []);

  async function fetchQuestions() {
    const res = await apiClient.get<QuestionItem[]>('/api/v1/questions');
    if (res.data) {
      setQuestions(res.data);
    }
  }

  async function handleGenerateQuestions() {
    setIsGenerating(true);
    setMessage(null);

    // Fetch concept id from curricula list
    const currRes = await apiClient.get<any[]>('/api/v1/curricula');
    let conceptId = '00000000-0000-0000-0000-000000000000';
    if (currRes.data && currRes.data.length > 0 && currRes.data[0].versions.length > 0) {
      const vRes = await apiClient.get<any>(`/api/v1/curricula/versions/${currRes.data[0].versions[0].id}`);
      if (vRes.data && vRes.data.chapters.length > 0 && vRes.data.chapters[0].topics.length > 0 && vRes.data.chapters[0].topics[0].concepts.length > 0) {
        conceptId = vRes.data.chapters[0].topics[0].concepts[0].id;
      }
    }

    const res = await apiClient.post<QuestionItem[]>('/api/v1/questions/generate', {
      concept_id: conceptId,
      count: 10,
      provider: 'mock'
    });

    setIsGenerating(false);

    if (res.error) {
      setMessage(`Generation Error: ${res.error.message}`);
    } else if (res.data) {
      setMessage(`Generated ${res.data.length} questions! Valid items set to 'PROPOSED' state.`);
      fetchQuestions();
    }
  }

  async function handleApprove(qId: string) {
    const res = await apiClient.post(`/api/v1/questions/${qId}/approve`, {});
    if (res.data) {
      setMessage('Question approved!');
      fetchQuestions();
    }
  }

  async function handleReject(qId: string) {
    const res = await apiClient.post(`/api/v1/questions/${qId}/reject`, {});
    if (res.data) {
      setMessage('Question rejected!');
      fetchQuestions();
    }
  }

  async function handleCreateQuiz() {
    if (selectedQIds.length === 0) return;
    const res = await apiClient.post('/api/v1/assessments', {
      title: quizTitle,
      question_ids: selectedQIds,
      assessment_type: 'QUIZ',
      max_attempts: 2
    });
    if (res.error) {
      setMessage(`Quiz Creation Error: ${res.error.message}`);
    } else {
      setMessage(`Quiz '${quizTitle}' created successfully with ${selectedQIds.length} approved questions!`);
      setSelectedQIds([]);
    }
  }

  function toggleQuestionSelection(qId: string) {
    setSelectedQIds(prev => prev.includes(qId) ? prev.filter(id => id !== qId) : [...prev, qId]);
  }

  return (
    <div style={{ padding: '32px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '2rem', color: '#818cf8', marginBottom: '8px' }}>
          Question Bank & Quiz Builder
        </h1>
        <p style={{ color: '#94a3b8' }}>
          Generate AI questions, verify deterministic math answers, approve proposed items, and create student quizzes.
        </p>
      </header>

      {message && (
        <div style={{ padding: '12px', borderRadius: '8px', backgroundColor: '#1e293b', border: '1px solid #6366f1', marginBottom: '20px' }}>
          {message}
        </div>
      )}

      {/* Top Action Controls */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '28px' }}>
        <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '12px' }}>✨ AI Question Generator</h2>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '16px' }}>
            Generates 10 items for a concept. Uses deterministic computation verification for math answers.
          </p>
          <button
            onClick={handleGenerateQuestions}
            disabled={isGenerating}
            style={{ padding: '10px 20px', background: isGenerating ? '#475569' : '#6366f1', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            {isGenerating ? 'Generating...' : '✨ Generate 10 Questions'}
          </button>
        </section>

        <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '12px' }}>📝 Create Assessment / Quiz</h2>
          <div style={{ display: 'flex', gap: '12px' }}>
            <input
              type="text"
              placeholder="Quiz Title"
              value={quizTitle}
              onChange={(e) => setQuizTitle(e.target.value)}
              style={{ flex: 1, padding: '8px', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }}
            />
            <button
              onClick={handleCreateQuiz}
              disabled={selectedQIds.length === 0}
              style={{ padding: '10px 16px', background: selectedQIds.length > 0 ? '#10b981' : '#475569', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: selectedQIds.length > 0 ? 'pointer' : 'not-allowed' }}
            >
              Build Quiz ({selectedQIds.length})
            </button>
          </div>
        </section>
      </div>

      {/* Question Bank Items List */}
      <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
        <h2 style={{ fontSize: '1.3rem', marginBottom: '16px' }}>Question Bank Items</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {questions.map((q) => (
            <div key={q.id} style={{ padding: '14px', background: '#0f172a', borderRadius: '8px', borderLeft: `4px solid ${q.validation_status === 'APPROVED' ? '#22c55e' : q.validation_status === 'REJECTED' ? '#ef4444' : '#f59e0b'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', padding: '2px 6px', borderRadius: '4px', background: '#334155', color: '#38bdf8', fontWeight: 'bold', marginRight: '8px' }}>
                    {q.question_type.toUpperCase()}
                  </span>
                  <span style={{ fontSize: '0.75rem', padding: '2px 6px', borderRadius: '4px', background: q.validation_status === 'APPROVED' ? '#15803d' : '#b45309', color: '#fff', fontWeight: 'bold' }}>
                    {q.validation_status}
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  {q.validation_status !== 'APPROVED' && (
                    <button onClick={() => handleApprove(q.id)} style={{ padding: '4px 10px', fontSize: '0.75rem', background: '#10b981', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                      Approve
                    </button>
                  )}
                  {q.validation_status !== 'REJECTED' && (
                    <button onClick={() => handleReject(q.id)} style={{ padding: '4px 10px', fontSize: '0.75rem', background: '#ef4444', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                      Reject
                    </button>
                  )}
                  {q.validation_status === 'APPROVED' && (
                    <input
                      type="checkbox"
                      checked={selectedQIds.includes(q.id)}
                      onChange={() => toggleQuestionSelection(q.id)}
                      style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                    />
                  )}
                </div>
              </div>

              <div style={{ fontSize: '1rem', fontWeight: 'bold', marginBottom: '6px' }}>
                {q.question_text}
              </div>

              {q.options && (
                <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
                  Options: {q.options.join(', ')}
                </div>
              )}

              <div style={{ fontSize: '0.85rem', color: '#34d399' }}>
                Correct Answer: {JSON.stringify(q.correct_answer)}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
