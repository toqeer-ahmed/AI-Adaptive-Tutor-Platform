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
    // Default class ID demo
    const res = await apiClient.get<ClassAnalyticsData>('/api/v1/analytics/class/00000000-0000-0000-0000-000000000003');
    if (res.data) {
      setAnalytics(res.data);
    }
    setLoading(false);
  }

  return (
    <div style={{ padding: '32px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      {/* Header */}
      <header style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '2.2rem', color: '#38bdf8', marginBottom: '4px' }}>
            🍎 Teacher Command Dashboard
          </h1>
          <p style={{ color: '#94a3b8' }}>
            Grade 6 Mathematics • Class Workflow, Assessment Generation, & Concept Mastery Analytics
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <Link href="/teacher/assessments" style={{ textDecoration: 'none' }}>
            <button style={{ padding: '10px 18px', backgroundColor: '#6366f1', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>
              ✨ Question Generator
            </button>
          </Link>
          <Link href="/teacher/grading" style={{ textDecoration: 'none' }}>
            <button style={{ padding: '10px 18px', backgroundColor: '#eab308', color: '#000', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>
              ✏️ Subjective Grading
            </button>
          </Link>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px', borderBottom: '1px solid #334155', paddingBottom: '12px' }}>
        {[
          { key: 'analytics', label: '📊 Class Analytics & Heatmap' },
          { key: 'curriculum', label: '📖 Curriculum Management' },
          { key: 'assessments', label: '📝 Question Bank & Quizzes' },
          { key: 'grading', label: '✏️ Grade Review & Overrides' }
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            style={{
              padding: '10px 20px',
              backgroundColor: activeTab === tab.key ? '#38bdf8' : '#1e293b',
              color: activeTab === tab.key ? '#000' : '#f8fafc',
              border: '1px solid #334155',
              borderRadius: '8px',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: ANALYTICS & HEATMAP */}
      {activeTab === 'analytics' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Summary Stat Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '16px' }}>
            <div style={{ padding: '20px', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }}>
              <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '4px' }}>Class Average Mastery</div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#38bdf8' }}>
                {analytics ? `${Math.round(analytics.class_average_mastery * 100)}%` : '78%'}
              </div>
            </div>

            <div style={{ padding: '20px', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }}>
              <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '4px' }}>Completion Rate</div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#34d399' }}>
                {analytics ? `${Math.round(analytics.completion_rate * 100)}%` : '92%'}
              </div>
            </div>

            <div style={{ padding: '20px', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }}>
              <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '4px' }}>Needing Remediation</div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#f87171' }}>
                {analytics ? analytics.students_needing_remediation.length : 2}
              </div>
            </div>

            <div style={{ padding: '20px', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }}>
              <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '4px' }}>Ready for Challenge</div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#a78bfa' }}>
                {analytics ? analytics.students_ready_for_challenge.length : 4}
              </div>
            </div>
          </div>

          {/* Concept Mastery Heatmap & Misconception Trends */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
            <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
              <h2 style={{ fontSize: '1.3rem', color: '#38bdf8', marginBottom: '16px' }}>🔥 Concept Mastery Heatmap</h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {[
                  { name: 'Adding Fractions (Unlike Denominators)', score: 0.68, band: 'On track' },
                  { name: 'Common Denominator Identification', score: 0.88, band: 'Strong' },
                  { name: 'Simplifying Fractions', score: 0.35, band: 'Needs Remediation' },
                  { name: 'Mixed Numbers Addition', score: 0.72, band: 'On track' }
                ].map((item, idx) => (
                  <div key={idx} style={{ padding: '16px', background: '#0f172a', borderRadius: '8px', borderLeft: `4px solid ${item.score < 0.4 ? '#f87171' : item.score >= 0.75 ? '#34d399' : '#fbbf24'}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 'bold', color: '#f8fafc' }}>{item.name}</span>
                      <span style={{ fontWeight: 'bold', color: item.score < 0.4 ? '#f87171' : '#34d399' }}>
                        {Math.round(item.score * 100)}% Raw Mastery
                      </span>
                    </div>

                    <div style={{ width: '100%', height: '8px', backgroundColor: '#334155', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{ width: `${item.score * 100}%`, height: '100%', backgroundColor: item.score < 0.4 ? '#f87171' : item.score >= 0.75 ? '#34d399' : '#fbbf24' }} />
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Misconception Trends */}
            <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
              <h2 style={{ fontSize: '1.3rem', color: '#fbbf24', marginBottom: '16px' }}>💡 Misconception Trends</h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ padding: '14px', background: '#0f172a', borderRadius: '8px', borderLeft: '3px solid #f87171' }}>
                  <div style={{ fontSize: '0.8rem', color: '#f87171', fontWeight: 'bold' }}>CODE: ADD_DENOMINATORS_DIRECTLY</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 'bold', color: '#f8fafc', margin: '2px 0' }}>Adds Denominators Directly</div>
                  <div style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>Occurrences in Class: 3 Students</div>
                </div>

                <div style={{ padding: '14px', background: '#0f172a', borderRadius: '8px', borderLeft: '3px solid #fbbf24' }}>
                  <div style={{ fontSize: '0.8rem', color: '#fbbf24', fontWeight: 'bold' }}>CODE: IGNORES_UNLIKE_DENOMINATORS</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 'bold', color: '#f8fafc', margin: '2px 0' }}>Ignores Unlike Denominators</div>
                  <div style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>Occurrences in Class: 1 Student</div>
                </div>
              </div>
            </section>
          </div>
        </div>
      )}

      {/* TAB 2: CURRICULUM MANAGEMENT */}
      {activeTab === 'curriculum' && (
        <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '1.3rem', color: '#38bdf8', marginBottom: '16px' }}>📖 Curriculum Document Management</h2>
          <p style={{ color: '#94a3b8', marginBottom: '20px' }}>
            Upload syllabus documents, extract structured AI drafts, review, edit, approve, and publish versioned curriculum.
          </p>

          <div style={{ display: 'flex', gap: '16px', marginBottom: '20px' }}>
            <Link href="/teacher/curriculum/review" style={{ textDecoration: 'none' }}>
              <button style={{ padding: '12px 20px', backgroundColor: '#38bdf8', color: '#000', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>
                📄 Open AI Curriculum Review Inspector
              </button>
            </Link>
          </div>
        </section>
      )}

      {/* TAB 3: ASSESSMENTS */}
      {activeTab === 'assessments' && (
        <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '1.3rem', color: '#a78bfa', marginBottom: '16px' }}>📝 Question Bank & Quiz Builder</h2>
          <p style={{ color: '#94a3b8', marginBottom: '20px' }}>
            Generate AI questions with deterministic math verification, edit rubrics, and publish quizzes.
          </p>

          <Link href="/teacher/assessments" style={{ textDecoration: 'none' }}>
            <button style={{ padding: '12px 20px', backgroundColor: '#6366f1', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>
              ✨ Open Question Generator Workspace
            </button>
          </Link>
        </section>
      )}

      {/* TAB 4: GRADING */}
      {activeTab === 'grading' && (
        <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '1.3rem', color: '#fbbf24', marginBottom: '16px' }}>✏️ Subjective Grade Review Workspace</h2>
          <p style={{ color: '#94a3b8', marginBottom: '20px' }}>
            Review AI evaluation proposals, accept grades, or submit overrides with audit logs.
          </p>

          <Link href="/teacher/grading" style={{ textDecoration: 'none' }}>
            <button style={{ padding: '12px 20px', backgroundColor: '#eab308', color: '#000', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>
              ✏️ Open Subjective Grading Workspace
            </button>
          </Link>
        </section>
      )}
    </div>
  );
}
