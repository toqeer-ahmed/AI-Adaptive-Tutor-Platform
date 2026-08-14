'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import {
  WobblyCard,
  HandBadge
} from '@/lib/HandDrawnComponents';

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
    <div style={{ padding: '32px 24px 60px', maxWidth: '1150px', margin: '0 auto' }}>
      {/* Breadcrumb Navigation */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <Link href="/" style={{ color: 'var(--pen-blue)', textDecoration: 'none', fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>←</span> Back to Study Desk
        </Link>
        <HandBadge variant="green">Parent Intelligence Digest</HandBadge>
      </div>

      {/* Header Corkboard Card */}
      <WobblyCard decoration="tape" style={{ padding: '26px 30px', marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <span style={{ fontSize: '1.8rem' }}>🏡</span>
            <h1 style={{ fontSize: '2.1rem' }}>
              Parent & Guardian Learning Digest
            </h1>
          </div>
          <p style={{ color: 'var(--pencil-subtle)', fontSize: '1.05rem' }}>
            Qualitative learning progress, quiz completions, and teacher notes for <strong style={{ color: 'var(--pencil-black)' }}>Alex Johnson (Grade 6)</strong>
          </p>
        </div>

        {children.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--pencil-black)' }}>Student Profile:</span>
            <select
              value={selectedChildId || ''}
              onChange={(e) => {
                setSelectedChildId(e.target.value);
                fetchChildDashboard(e.target.value);
              }}
              className="wobbly-input"
              style={{
                padding: '6px 12px',
                width: 'auto',
                fontWeight: 700,
                fontSize: '0.95rem'
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
      </WobblyCard>

      {/* Main Content Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Left Column: Qualitative Progress & Completed Quizzes */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Qualitative Progress */}
          <WobblyCard style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <h2 style={{ fontSize: '1.35rem' }}>
                📊 Qualitative Mastery Overview
              </h2>
              <HandBadge variant="blue">Zero Internal PII</HandBadge>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[
                { title: 'Adding Fractions with Common Denominators', band: 'Strong 🌟', variant: 'green' as const, badgeVar: 'green' as const },
                { title: 'Unlike Denominators & Equivalent Fractions', band: 'On track 📈', variant: 'cyan' as const, badgeVar: 'blue' as const },
                { title: 'Simplifying Mixed Numbers', band: 'Getting there 💡', variant: 'yellow' as const, badgeVar: 'yellow' as const }
              ].map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '16px 18px',
                    background: item.variant === 'green' ? 'var(--postit-green)' : item.variant === 'cyan' ? 'var(--postit-cyan)' : 'var(--postit-yellow)',
                    borderRadius: 'var(--wobbly-sm)',
                    border: '1.5px solid var(--pencil-black)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    boxShadow: 'var(--shadow-hard-sm)'
                  }}
                >
                  <div style={{ fontWeight: 700, color: 'var(--pencil-black)', fontSize: '1.05rem' }}>
                    {item.title}
                  </div>
                  <HandBadge variant={item.badgeVar} style={{ fontSize: '0.9rem' }}>
                    {item.band}
                  </HandBadge>
                </div>
              ))}
            </div>
          </WobblyCard>

          {/* Completed Work */}
          <WobblyCard style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '1.35rem', marginBottom: '18px' }}>
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
                    background: '#ffffff',
                    borderRadius: 'var(--wobbly-sm)',
                    border: '1.5px solid var(--pencil-black)',
                    boxShadow: 'var(--shadow-hard-sm)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, color: 'var(--pencil-black)', fontSize: '1.05rem' }}>{w.title}</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--pencil-subtle)', marginTop: '2px' }}>Completed: {w.date}</div>
                  </div>
                  <div style={{ fontSize: '1.4rem', fontFamily: 'var(--font-heading)', fontWeight: 700, color: '#15803d' }}>{w.score}</div>
                </div>
              ))}
            </div>
          </WobblyCard>
        </div>

        {/* Right Column: Teacher Notes & Engagement Metrics */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Teacher Notes Post-it */}
          <WobblyCard variant="yellow" decoration="tape" tilt="left-sm" style={{ padding: '22px' }}>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '12px' }}>
              💬 Teacher Note
            </h2>
            <div style={{ color: 'var(--pencil-black)', fontSize: '1.05rem', lineHeight: 1.5, fontStyle: 'italic' }}>
              &ldquo;Alex has shown excellent persistence when finding least common multiples. Keep encouraging daily 10-minute Socratic practice sessions!&rdquo;
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--pencil-subtle)', marginTop: '12px', textAlign: 'right', fontWeight: 700 }}>
              — Mrs. Davis (Grade 6 Mathematics)
            </div>
          </WobblyCard>

          {/* Activity Metrics Pin Card */}
          <WobblyCard variant="purple" decoration="tack-blue" tilt="right-sm" style={{ padding: '22px' }}>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '16px' }}>
              📈 Engagement Summary
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ padding: '12px 14px', background: '#ffffff', borderRadius: 'var(--wobbly-sm)', border: '1.5px solid var(--pencil-black)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.95rem', color: 'var(--pencil-subtle)' }}>Practice Sessions</span>
                <span style={{ fontWeight: 700, color: '#7e22ce', fontSize: '1.2rem' }}>14</span>
              </div>

              <div style={{ padding: '12px 14px', background: '#ffffff', borderRadius: 'var(--wobbly-sm)', border: '1.5px solid var(--pencil-black)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.95rem', color: 'var(--pencil-subtle)' }}>Active Math Objectives</span>
                <span style={{ fontWeight: 700, color: 'var(--pen-blue)', fontSize: '1.2rem' }}>4</span>
              </div>

              <div style={{ padding: '12px 14px', background: '#ffffff', borderRadius: 'var(--wobbly-sm)', border: '1.5px solid var(--pencil-black)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.95rem', color: 'var(--pencil-subtle)' }}>Spaced Review Interval</span>
                <span style={{ fontWeight: 700, color: '#15803d', fontSize: '1.1rem' }}>On Schedule</span>
              </div>
            </div>
          </WobblyCard>
        </div>
      </div>
    </div>
  );
}


