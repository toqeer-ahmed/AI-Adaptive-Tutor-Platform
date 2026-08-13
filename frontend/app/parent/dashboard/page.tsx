'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface ChildLink {
  link_id: string;
  student_id: string;
  student_name: string;
  email: string;
}

interface ParentDashboardData {
  child_id: string;
  child_name: string;
  qualitative_progress: Array<{ concept_id: string; qualitative_band: string; status: string; practice_count: number }>;
  completed_work: Array<{ assessment_title: string; score_percentage: number; status: string; completed_at: string }>;
  upcoming_work: Array<{ title: string; due_date: string; status: string }>;
  activity_summary: { total_practice_sessions: number; active_concepts_count: number };
  teacher_notes: string;
}

export default function ParentDashboardPage() {
  const [children, setChildren] = useState<ChildLink[]>([]);
  const [selectedChildId, setSelectedChildId] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<ParentDashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLinkedChildren();
  }, []);

  async function fetchLinkedChildren() {
    const res = await apiClient.get<ChildLink[]>('/api/v1/parents/children');
    if (res.data && res.data.length > 0) {
      setChildren(res.data);
      setSelectedChildId(res.data[0].student_id);
      fetchChildDashboard(res.data[0].student_id);
    } else {
      // Mock child ID for demo
      const demoChildId = '00000000-0000-0000-0000-000000000002';
      setSelectedChildId(demoChildId);
      fetchChildDashboard(demoChildId);
    }
    setLoading(false);
  }

  async function fetchChildDashboard(childId: string) {
    const res = await apiClient.get<ParentDashboardData>(`/api/v1/parents/child/${childId}/dashboard`);
    if (res.data) {
      setDashboard(res.data);
    }
  }

  return (
    <div style={{ padding: '32px', maxWidth: '1100px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      {/* Header & Child Selector */}
      <header style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '2rem', color: '#10b981', marginBottom: '4px' }}>
            🏡 Parent & Guardian Learning Portal
          </h1>
          <p style={{ color: '#94a3b8' }}>
            Qualitative progress, activity summaries, completed quizzes, and teacher updates.
          </p>
        </div>

        {children.length > 0 && (
          <div>
            <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginRight: '8px' }}>Child:</label>
            <select
              value={selectedChildId || ''}
              onChange={(e) => {
                setSelectedChildId(e.target.value);
                fetchChildDashboard(e.target.value);
              }}
              style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #334155', backgroundColor: '#1e293b', color: '#fff', fontWeight: 'bold' }}
            >
              {children.map((c) => (
                <option key={c.student_id} value={c.student_id}>
                  {c.student_name}
                </option>
              ))}
            </select>
          </div>
        )}
      </header>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Left Column: Qualitative Progress & Activity Summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Qualitative Progress */}
          <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
            <h2 style={{ fontSize: '1.3rem', color: '#34d399', marginBottom: '16px' }}>
              📊 Qualitative Learning Progress
            </h2>

            {loading ? (
              <p style={{ color: '#94a3b8' }}>Loading progress...</p>
            ) : !dashboard || dashboard.qualitative_progress.length === 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ padding: '16px', background: '#0f172a', borderRadius: '8px', borderLeft: '4px solid #34d399' }}>
                  <div style={{ fontWeight: 'bold', color: '#f8fafc' }}>Adding Fractions with Common Denominators</div>
                  <div style={{ fontSize: '0.9rem', color: '#34d399', fontWeight: 'bold', marginTop: '4px' }}>Strong 🌟</div>
                </div>

                <div style={{ padding: '16px', background: '#0f172a', borderRadius: '8px', borderLeft: '4px solid #38bdf8' }}>
                  <div style={{ fontWeight: 'bold', color: '#f8fafc' }}>Unlike Denominators & Equivalent Fractions</div>
                  <div style={{ fontSize: '0.9rem', color: '#38bdf8', fontWeight: 'bold', marginTop: '4px' }}>On track 📈</div>
                </div>

                <div style={{ padding: '16px', background: '#0f172a', borderRadius: '8px', borderLeft: '4px solid #fbbf24' }}>
                  <div style={{ fontWeight: 'bold', color: '#f8fafc' }}>Simplifying Mixed Numbers</div>
                  <div style={{ fontSize: '0.9rem', color: '#fbbf24', fontWeight: 'bold', marginTop: '4px' }}>Getting there 💡</div>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {dashboard.qualitative_progress.map((q, idx) => (
                  <div key={idx} style={{ padding: '16px', background: '#0f172a', borderRadius: '8px' }}>
                    <div style={{ fontWeight: 'bold', color: '#f8fafc' }}>Mathematics Concept</div>
                    <div style={{ fontSize: '0.9rem', color: '#34d399', fontWeight: 'bold', marginTop: '4px' }}>
                      {q.qualitative_band}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Completed Work & Scores */}
          <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
            <h2 style={{ fontSize: '1.3rem', color: '#38bdf8', marginBottom: '16px' }}>📝 Recent Completed Work</h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {(!dashboard || dashboard.completed_work.length === 0) ? (
                <div style={{ padding: '16px', background: '#0f172a', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 'bold', color: '#f8fafc' }}>Fractions Diagnostic Quiz</div>
                    <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Completed Yesterday</div>
                  </div>
                  <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#34d399' }}>90%</span>
                </div>
              ) : (
                dashboard.completed_work.map((w, idx) => (
                  <div key={idx} style={{ padding: '16px', background: '#0f172a', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontWeight: 'bold', color: '#f8fafc' }}>{w.assessment_title}</div>
                      <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{new Date(w.completed_at).toLocaleDateString()}</div>
                    </div>
                    <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#34d399' }}>{w.score_percentage}%</span>
                  </div>
                ))
              )}
            </div>
          </section>
        </div>

        {/* Right Column: Teacher Notes & Activity Summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Teacher Notes */}
          <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
            <h2 style={{ fontSize: '1.2rem', color: '#fbbf24', marginBottom: '12px' }}>💬 Teacher Feedback</h2>
            <div style={{ padding: '14px', background: '#0f172a', borderRadius: '8px', borderLeft: '3px solid #fbbf24', fontSize: '0.9rem', color: '#cbd5e1', lineHeight: '1.5' }}>
              "{dashboard ? dashboard.teacher_notes : 'Alex is demonstrating great consistency in fraction homework!'}"
            </div>
          </section>

          {/* Activity Summary Stats */}
          <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
            <h2 style={{ fontSize: '1.2rem', color: '#a78bfa', marginBottom: '12px' }}>📈 Activity Summary</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ padding: '12px', background: '#0f172a', borderRadius: '6px', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Practice Sessions:</span>
                <span style={{ fontWeight: 'bold', color: '#a78bfa' }}>{dashboard?.activity_summary.total_practice_sessions || 14}</span>
              </div>

              <div style={{ padding: '12px', background: '#0f172a', borderRadius: '6px', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Active Objectives:</span>
                <span style={{ fontWeight: 'bold', color: '#38bdf8' }}>{dashboard?.activity_summary.active_concepts_count || 4}</span>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
