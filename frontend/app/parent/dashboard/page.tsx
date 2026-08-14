'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
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
    try {
      const res = await apiClient.get<ChildLink[]>('/api/v1/parents/children');
      if (res.data && res.data.length > 0) {
        setChildren(res.data);
        setSelectedChildId(res.data[0].student_id);
        fetchChildDashboard(res.data[0].student_id);
      } else {
        const demoChildId = '00000000-0000-0000-0000-000000000002';
        setSelectedChildId(demoChildId);
        fetchChildDashboard(demoChildId);
      }
    } catch (e) {
      const demoChildId = '00000000-0000-0000-0000-000000000002';
      setSelectedChildId(demoChildId);
      fetchChildDashboard(demoChildId);
    } finally {
      setLoading(false);
    }
  }

  async function fetchChildDashboard(childId: string) {
    try {
      const res = await apiClient.get<ParentDashboardData>(`/api/v1/parents/child/${childId}/dashboard`);
      if (res.data) {
        setDashboard(res.data);
      }
    } catch (e) {
      // Demo fallback
    }
  }

  return (
    <div style={{ padding: '32px 24px 60px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Breadcrumb Navigation */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <Link href="/" style={{ color: 'var(--text-muted)', textDecoration: 'none', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>←</span> Back to Portals
        </Link>
        <span className="badge badge-emerald">Parent Intelligence Digest</span>
      </div>

      <header className="glass-panel" style={{ padding: '28px', marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <span style={{ fontSize: '1.6rem' }}>🏡</span>
            <h1 style={{ fontSize: '1.9rem', color: '#f8fafc' }}>
              Parent Learning Digest
            </h1>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            Qualitative learning progress, quiz completions, and teacher notes for <strong style={{ color: '#f8fafc' }}>Alex Johnson (Grade 6)</strong>
          </p>
        </div>

        {children.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Student Profile:</span>
            <select
              value={selectedChildId || ''}
              onChange={(e) => {
                setSelectedChildId(e.target.value);
                fetchChildDashboard(e.target.value);
              }}
              style={{
                padding: '8px 14px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                backgroundColor: 'rgba(15, 23, 42, 0.8)',
                color: '#ffffff',
                fontWeight: 600,
                fontSize: '0.88rem'
              }}
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

      {/* Main Content Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Left Column: Qualitative Progress & Completed Quizzes */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Qualitative Progress */}
          <section className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <h2 style={{ fontSize: '1.25rem', color: '#34d399' }}>
                📊 Qualitative Mastery Overview
              </h2>
              <span className="badge badge-cyan">Zero Raw Internal PII</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[
                { title: 'Adding Fractions with Common Denominators', band: 'Strong 🌟', color: '#10b981', badgeClass: 'badge-emerald' },
                { title: 'Unlike Denominators & Equivalent Fractions', band: 'On track 📈', color: '#38bdf8', badgeClass: 'badge-cyan' },
                { title: 'Simplifying Mixed Numbers', band: 'Getting there 💡', color: '#f59e0b', badgeClass: 'badge-amber' }
              ].map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '18px',
                    background: 'rgba(15, 23, 42, 0.7)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    borderLeft: `4px solid ${item.color}`,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.95rem' }}>
                    {item.title}
                  </div>
                  <span className={`badge ${item.badgeClass}`} style={{ fontSize: '0.82rem' }}>
                    {item.band}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {/* Completed Work */}
          <section className="glass-panel" style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '1.25rem', color: '#38bdf8', marginBottom: '18px' }}>
              📝 Recent Completed Assessments
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[
                { title: 'Fractions Diagnostic Quiz (Section 3.2)', date: 'Yesterday', score: '90%', status: 'Passed' },
                { title: 'Adding Like Fractions Checkpoint', date: '3 days ago', score: '100%', status: 'Mastered' }
              ].map((w, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '16px 20px',
                    background: 'rgba(15, 23, 42, 0.7)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.95rem' }}>{w.title}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>Completed: {w.date}</div>
                  </div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#34d399' }}>{w.score}</div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Right Column: Teacher Notes & Engagement Metrics */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Teacher Notes Card */}
          <section className="glass-panel" style={{ padding: '22px', borderLeft: '4px solid #f59e0b' }}>
            <h2 style={{ fontSize: '1.15rem', color: '#fbbf24', marginBottom: '12px' }}>
              💬 Teacher Note
            </h2>
            <div style={{ color: '#cbd5e1', fontSize: '0.9rem', lineHeight: 1.6, fontStyle: 'italic' }}>
              &ldquo;Alex has shown excellent persistence when finding least common multiples. Keep encouraging daily 10-minute Socratic practice sessions!&rdquo;
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '12px', textAlign: 'right' }}>
              — Mrs. Davis (Grade 6 Mathematics)
            </div>
          </section>

          {/* Activity Metrics */}
          <section className="glass-panel" style={{ padding: '22px' }}>
            <h2 style={{ fontSize: '1.15rem', color: '#c084fc', marginBottom: '16px' }}>
              📈 Engagement Summary
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ padding: '14px', background: 'rgba(15, 23, 42, 0.7)', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>Practice Sessions</span>
                <span style={{ fontWeight: 800, color: '#c084fc', fontSize: '1.1rem' }}>14</span>
              </div>

              <div style={{ padding: '14px', background: 'rgba(15, 23, 42, 0.7)', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>Active Math Objectives</span>
                <span style={{ fontWeight: 800, color: '#38bdf8', fontSize: '1.1rem' }}>4</span>
              </div>

              <div style={{ padding: '14px', background: 'rgba(15, 23, 42, 0.7)', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>Spaced Review Interval</span>
                <span style={{ fontWeight: 800, color: '#34d399', fontSize: '1.1rem' }}>On Schedule</span>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

