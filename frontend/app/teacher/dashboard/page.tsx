'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';

interface ClassAnalyticsData {
  class_id: string;
  class_name: string;
  student_count: number;
  class_average_mastery: number;
  concept_heatmap: Array<{ concept_id: string; average_mastery: number; student_count: number }>;
  students_needing_remediation: Array<{ student_id: string; name: string; mastery_score: number }>;
  students_ready_for_challenge: Array<{ student_id: string; name: string; mastery_score: number }>;
  misconception_trends: Array<{ code: string; name: string; count: number }>;
  completion_rate: number;
}

export default function TeacherDashboardPage() {
  const [activeTab, setActiveTab] = useState<'analytics' | 'curriculum' | 'assessments' | 'grading'>('analytics');
  const [analytics, setAnalytics] = useState<ClassAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClassAnalytics();
  }, []);

  async function fetchClassAnalytics() {
    try {
      const res = await apiClient.get<ClassAnalyticsData>('/api/v1/analytics/class/00000000-0000-0000-0000-000000000003');
      if (res.data) {
        setAnalytics(res.data);
      }
    } catch (e) {
      // Fallback
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: '32px 24px 60px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Top Header */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <Link href="/" style={{ color: 'var(--text-muted)', textDecoration: 'none', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>←</span> Back to Portals
        </Link>
        <div style={{ display: 'flex', gap: '10px' }}>
          <span className="badge badge-purple">Teacher Command Studio</span>
          <span className="badge badge-cyan">Section 6-A</span>
        </div>
      </div>

      <header className="glass-panel" style={{ padding: '28px', marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <span style={{ fontSize: '1.6rem' }}>🍎</span>
            <h1 style={{ fontSize: '1.9rem', color: '#f8fafc' }}>
              Teacher Command Dashboard
            </h1>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            Grade 6 Mathematics • Real-time Concept Mastery Heatmaps, Misconception Diagnosis, & Question Authoring
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <Link href="/teacher/assessments" className="btn-primary" style={{ padding: '10px 18px', fontSize: '0.88rem' }}>
            ✨ Question Generator
          </Link>
          <Link href="/teacher/grading" className="btn-secondary" style={{ padding: '10px 18px', fontSize: '0.88rem' }}>
            ✏️ Grade Review
          </Link>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '28px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '14px', overflowX: 'auto' }}>
        {[
          { key: 'analytics', label: '📊 Class Mastery Heatmap', icon: '📊' },
          { key: 'curriculum', label: '📖 Curriculum Studio', icon: '📖' },
          { key: 'assessments', label: '📝 Question Bank & Quizzes', icon: '📝' },
          { key: 'grading', label: '✏️ Grade Review & Overrides', icon: '✏️' }
        ].map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              style={{
                padding: '10px 20px',
                background: isActive ? 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)' : 'rgba(15, 23, 42, 0.6)',
                color: '#ffffff',
                border: `1px solid ${isActive ? 'rgba(129, 140, 248, 0.5)' : 'var(--border-subtle)'}`,
                borderRadius: 'var(--radius-sm)',
                fontWeight: 600,
                fontSize: '0.9rem',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap'
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* TAB 1: ANALYTICS & HEATMAP */}
      {activeTab === 'analytics' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
          {/* 4 Summary Stat Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '18px' }}>
            <div className="glass-panel" style={{ padding: '22px', borderLeft: '4px solid #38bdf8' }}>
              <div style={{ fontSize: '0.82rem', color: '#38bdf8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Class Average Mastery
              </div>
              <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#f8fafc', margin: '6px 0 2px' }}>
                {analytics ? `${Math.round(analytics.class_average_mastery * 100)}%` : '78%'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-subtle)' }}>
                Target: &ge; 75% cohort benchmark
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '22px', borderLeft: '4px solid #10b981' }}>
              <div style={{ fontSize: '0.82rem', color: '#34d399', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Quiz Completion Rate
              </div>
              <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#f8fafc', margin: '6px 0 2px' }}>
                {analytics ? `${Math.round(analytics.completion_rate * 100)}%` : '92%'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-subtle)' }}>
                24 of 26 active students
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '22px', borderLeft: '4px solid #f43f5e' }}>
              <div style={{ fontSize: '0.82rem', color: '#f43f5e', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Target Remediation
              </div>
              <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#f8fafc', margin: '6px 0 2px' }}>
                {analytics ? analytics.students_needing_remediation.length : 2}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-subtle)' }}>
                Mastery score &lt; 40% threshold
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '22px', borderLeft: '4px solid #c084fc' }}>
              <div style={{ fontSize: '0.82rem', color: '#c084fc', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Ready for Challenge
              </div>
              <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#f8fafc', margin: '6px 0 2px' }}>
                {analytics ? analytics.students_ready_for_challenge.length : 4}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-subtle)' }}>
                Mastery score &ge; 85% with high stability
              </div>
            </div>
          </div>

          {/* Heatmap & Misconception Columns */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
            {/* Concept Heatmap */}
            <section className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h2 style={{ fontSize: '1.25rem', color: '#38bdf8' }}>🔥 Concept Mastery Heatmap</h2>
                <span className="badge badge-cyan">4 Target Concepts</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {[
                  { name: 'Adding Fractions (Unlike Denominators)', score: 0.68, band: 'On track' },
                  { name: 'Common Denominator Identification', score: 0.88, band: 'Strong' },
                  { name: 'Simplifying Fractions', score: 0.35, band: 'Needs Remediation' },
                  { name: 'Mixed Numbers Addition', score: 0.72, band: 'On track' }
                ].map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '16px',
                      background: 'rgba(15, 23, 42, 0.7)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                      borderLeft: `4px solid ${item.score < 0.4 ? '#f43f5e' : item.score >= 0.75 ? '#10b981' : '#f59e0b'}`
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.95rem' }}>{item.name}</span>
                      <span style={{ fontWeight: 700, fontSize: '0.9rem', color: item.score < 0.4 ? '#f87171' : item.score >= 0.75 ? '#34d399' : '#fbbf24' }}>
                        {Math.round(item.score * 100)}% Average
                      </span>
                    </div>

                    <div style={{ width: '100%', height: '8px', backgroundColor: 'rgba(255, 255, 255, 0.08)', borderRadius: '9999px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${item.score * 100}%`,
                          height: '100%',
                          background: item.score < 0.4 ? 'linear-gradient(90deg, #f59e0b, #f43f5e)' : item.score >= 0.75 ? 'linear-gradient(90deg, #10b981, #34d399)' : 'linear-gradient(90deg, #38bdf8, #818cf8)',
                          borderRadius: '9999px'
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Misconception Diagnosis */}
            <section className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h2 style={{ fontSize: '1.25rem', color: '#fbbf24' }}>💡 Detected Misconceptions</h2>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.7)', borderRadius: 'var(--radius-sm)', borderLeft: '3px solid #f43f5e', border: '1px solid var(--border-subtle)', borderLeftColor: '#f43f5e' }}>
                  <div style={{ fontSize: '0.72rem', color: '#f43f5e', fontWeight: 700, letterSpacing: '0.04em' }}>CODE: ADD_DENOMINATORS_DIRECTLY</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', margin: '4px 0' }}>Adds Denominators Directly</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Found in 3 student submissions (e.g. 1/3 + 1/3 = 2/6)</div>
                </div>

                <div style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.7)', borderRadius: 'var(--radius-sm)', borderLeft: '3px solid #fbbf24', border: '1px solid var(--border-subtle)', borderLeftColor: '#fbbf24' }}>
                  <div style={{ fontSize: '0.72rem', color: '#fbbf24', fontWeight: 700, letterSpacing: '0.04em' }}>CODE: IGNORES_UNLIKE_DENOMINATORS</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', margin: '4px 0' }}>Ignores Unlike Denominators</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Found in 1 student submission (e.g. 1/2 + 1/4 = 2/4)</div>
                </div>
              </div>
            </section>
          </div>
        </div>
      )}

      {/* TAB 2: CURRICULUM */}
      {activeTab === 'curriculum' && (
        <section className="glass-panel" style={{ padding: '32px' }}>
          <h2 style={{ fontSize: '1.4rem', color: '#38bdf8', marginBottom: '12px' }}>📖 Curriculum Document Management</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px', lineHeight: 1.5, maxWidth: '700px' }}>
            Upload syllabus documents, extract structured AI drafts, review, edit, approve, and publish versioned curriculum with strict immutable version control.
          </p>

          <Link href="/teacher/curriculum/review" className="btn-primary">
            📄 Open AI Curriculum Review Inspector →
          </Link>
        </section>
      )}

      {/* TAB 3: ASSESSMENTS */}
      {activeTab === 'assessments' && (
        <section className="glass-panel" style={{ padding: '32px' }}>
          <h2 style={{ fontSize: '1.4rem', color: '#c084fc', marginBottom: '12px' }}>📝 Question Bank & Quiz Builder</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px', lineHeight: 1.5, maxWidth: '700px' }}>
            Generate AI questions with deterministic math verification, edit rubrics, and publish quizzes.
          </p>

          <Link href="/teacher/assessments" className="btn-primary">
            ✨ Open Question Generator Workspace →
          </Link>
        </section>
      )}

      {/* TAB 4: GRADING */}
      {activeTab === 'grading' && (
        <section className="glass-panel" style={{ padding: '32px' }}>
          <h2 style={{ fontSize: '1.4rem', color: '#fbbf24', marginBottom: '12px' }}>✏️ Subjective Grade Review Workspace</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px', lineHeight: 1.5, maxWidth: '700px' }}>
            Review AI evaluation proposals, accept grades, or submit teacher overrides with complete audit logs.
          </p>

          <Link href="/teacher/grading" className="btn-primary">
            ✏️ Open Subjective Grading Workspace →
          </Link>
        </section>
      )}
    </div>
  );
}

