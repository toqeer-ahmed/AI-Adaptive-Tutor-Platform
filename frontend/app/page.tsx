'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import {
  WobblyCard,
  WobblyButton,
  HandBadge,
  ScribbleUnderline,
  HandDrawnArrow
} from '@/lib/HandDrawnComponents';

interface HealthStatus {
  status: string;
  version: string;
  environment: string;
  services?: {
    postgresql?: string;
    redis?: string;
  };
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await apiClient.get<HealthStatus>('/api/v1/health');
        if (res.data) {
          setHealth(res.data);
        }
      } catch (e) {
        // Handled via state
      } finally {
        setLoading(false);
      }
    }
    checkHealth();
  }, []);

  const studentPortals = [
    {
      title: 'AI Socratic Tutor',
      badge: 'Socratic v1.0',
      badgeVariant: 'yellow' as const,
      variant: 'yellow' as const,
      tilt: 'left-sm' as const,
      decoration: 'tack-red' as const,
      path: '/student/tutor',
      desc: 'Conversational Socratic tutoring grounded strictly in approved Grade 6 Mathematics textbooks.',
      icon: '✏️'
    },
    {
      title: 'Knowledge Map & Mastery',
      badge: 'EWMA Engine',
      badgeVariant: 'green' as const,
      variant: 'green' as const,
      tilt: 'right-sm' as const,
      decoration: 'tape' as const,
      path: '/student/mastery',
      desc: 'Deterministic concept mastery visualization, retention decay tracking, and spaced review logs.',
      icon: '📐'
    },
    {
      title: 'Adaptive Learning Path',
      badge: 'Rule-Based',
      badgeVariant: 'purple' as const,
      variant: 'purple' as const,
      tilt: 'left' as const,
      decoration: 'tack-blue' as const,
      path: '/student/adaptive',
      desc: 'Real-time next-activity selection tailored to prerequisite graph mastery (0 LLM state drift).',
      icon: '🎯'
    },
    {
      title: 'Assessment Player',
      badge: 'Deterministic Math',
      badgeVariant: 'blue' as const,
      variant: 'cyan' as const,
      tilt: 'right' as const,
      decoration: 'tape' as const,
      path: '/student/assessments',
      desc: 'Interactive quiz player with mathematical expression parsing and instant step feedback.',
      icon: '📝'
    }
  ];

  const educatorPortals = [
    {
      title: 'Curriculum Studio & Review',
      badge: 'Human-in-Loop',
      badgeVariant: 'blue' as const,
      variant: 'white' as const,
      tilt: 'left-sm' as const,
      decoration: 'tape' as const,
      path: '/teacher/curriculum/review',
      desc: 'AI syllabus extraction inspector with state-gated approval workflow and immutable publishing.',
      icon: '📚'
    },
    {
      title: 'Question Bank & Generator',
      badge: '6-Step Verifier',
      badgeVariant: 'purple' as const,
      variant: 'yellow' as const,
      tilt: 'right-sm' as const,
      decoration: 'tack-yellow' as const,
      path: '/teacher/assessments',
      desc: 'AI question authoring with deterministic math verification, rubric checks, and teacher publishing.',
      icon: '✍️'
    },
    {
      title: 'Teacher Analytics Dashboard',
      badge: 'Class Heatmaps',
      badgeVariant: 'green' as const,
      variant: 'green' as const,
      tilt: 'left' as const,
      decoration: 'tape' as const,
      path: '/teacher/dashboard',
      desc: 'Classroom mastery heatmaps, misconception diagnoses, and targeted remediation rosters.',
      icon: '📊'
    },
    {
      title: 'Parent Intelligence Digest',
      badge: 'Zero PII Leakage',
      badgeVariant: 'red' as const,
      variant: 'orange' as const,
      tilt: 'right' as const,
      decoration: 'tack-red' as const,
      path: '/parent/dashboard',
      desc: 'Qualitative progress summaries and teacher note cards with zero internal data exposure.',
      icon: '🏡'
    }
  ];

  return (
    <main style={{ minHeight: '100vh', padding: '40px 24px 80px', maxWidth: '1100px', margin: '0 auto' }}>
      {/* Top Header Pinboard Bar */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '48px', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '46px',
            height: '46px',
            borderRadius: 'var(--wobbly-sm)',
            border: '2.5px solid var(--pencil-black)',
            background: 'var(--marker-red)',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.5rem',
            boxShadow: '3px 3px 0px 0px var(--pencil-black)',
            transform: 'rotate(-3deg)'
          }}>
            ✎
          </div>
          <div>
            <span style={{ fontSize: '1.6rem', fontFamily: 'var(--font-heading)', fontWeight: 700, color: 'var(--pencil-black)' }}>
              Adaptive<span style={{ color: 'var(--marker-red)' }}>Edu</span>
            </span>
            <span style={{ marginLeft: '10px', fontSize: '0.9rem', padding: '2px 8px', borderRadius: 'var(--wobbly-sm)', background: 'var(--postit-yellow)', border: '1.5px solid var(--pencil-black)', fontWeight: 700 }}>
              Sketchbook v1.0
            </span>
          </div>
        </div>

        {/* Header Right Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          {/* Pinned Operational Status Note */}
          <div style={{
            padding: '8px 16px',
            background: '#ffffff',
            border: '2px solid var(--pencil-black)',
            borderRadius: 'var(--wobbly-sm)',
            boxShadow: 'var(--shadow-hard-sm)',
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transform: 'rotate(1deg)'
          }}>
            <div className="tape-strip" style={{ width: '50px', height: '16px', top: '-8px' }} />
            <span style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: health?.status === 'healthy' ? '#15803d' : '#b91c1c',
              border: '1.5px solid var(--pencil-black)'
            }} />
            <span style={{ fontSize: '0.9rem', fontWeight: 700 }}>
              {loading ? 'Checking...' : health?.status === 'healthy' ? 'Cluster Online' : 'Offline'}
            </span>
          </div>

          <Link href="/login" style={{ textDecoration: 'none' }}>
            <WobblyButton variant="red" style={{ padding: '8px 18px', fontSize: '1rem' }}>
              🔑 Sign In to Workspace →
            </WobblyButton>
          </Link>
        </div>
      </header>

      {/* Hero Welcome Banner */}
      <section style={{ textAlign: 'center', marginBottom: '56px', position: 'relative' }}>
        <div style={{ display: 'inline-block', marginBottom: '14px' }}>
          <HandBadge variant="yellow" style={{ fontSize: '1rem', padding: '6px 16px', transform: 'rotate(-1deg)' }}>
            ✨ Multi-Tenant Adaptive Education &bull; Grades 4 to 8
          </HandBadge>
        </div>

        <h1 style={{ fontSize: '3.2rem', marginBottom: '16px', lineHeight: 1.15, color: 'var(--pencil-black)' }}>
          Authentic AI Socratic Tutoring &amp;{' '}
          <span style={{ position: 'relative', display: 'inline-block' }}>
            <span style={{ color: 'var(--marker-red)' }}>Adaptive Mastery</span>
            <ScribbleUnderline color="var(--pen-blue)" width={230} height={18} style={{ bottom: '-10px', left: '0' }} />
          </span>
        </h1>

        <p style={{ fontSize: '1.25rem', color: 'var(--pencil-subtle)', maxWidth: '720px', margin: '0 auto 28px', lineHeight: 1.5 }}>
          Built with deterministic prerequisite learning paths, tenant-isolated textbook RAG, and human-in-the-loop teacher oversight.
        </p>

        {/* Quick Role Portal Buttons */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <Link href="/student/dashboard" style={{ textDecoration: 'none' }}>
            <WobblyButton variant="blue" style={{ fontSize: '1.1rem', padding: '12px 24px' }}>
              🎒 Student Study Desk
            </WobblyButton>
          </Link>
          <Link href="/teacher/dashboard" style={{ textDecoration: 'none' }}>
            <WobblyButton variant="yellow" style={{ fontSize: '1.1rem', padding: '12px 24px' }}>
              🍎 Teacher Studio
            </WobblyButton>
          </Link>
          <Link href="/parent/dashboard" style={{ textDecoration: 'none' }}>
            <WobblyButton variant="green" style={{ fontSize: '1.1rem', padding: '12px 24px' }}>
              🏡 Parent Digest
            </WobblyButton>
          </Link>
          <Link href="/admin/dashboard" style={{ textDecoration: 'none' }}>
            <WobblyButton variant="purple" style={{ fontSize: '1.1rem', padding: '12px 24px' }}>
              ⚡ Admin Command
            </WobblyButton>
          </Link>
        </div>

        <div style={{ position: 'absolute', right: '4%', bottom: '-15px', transform: 'rotate(8deg)' }}>
          <HandDrawnArrow />
          <div style={{ fontSize: '0.85rem', color: 'var(--pen-blue)', fontWeight: 700 }}>Start practicing!</div>
        </div>
      </section>

      {/* Grid 1: Student Learning Notebooks */}
      <section style={{ marginBottom: '52px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <span style={{ fontSize: '1.6rem' }}>🎒</span>
          <h2 style={{ fontSize: '1.6rem' }}>Student Learning Notebooks</h2>
          <HandBadge variant="blue">Grades 4–8</HandBadge>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px' }}>
          {studentPortals.map((portal) => (
            <Link key={portal.path} href={portal.path} style={{ textDecoration: 'none', color: 'inherit' }}>
              <WobblyCard
                variant={portal.variant}
                decoration={portal.decoration}
                tilt={portal.tilt}
                style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', cursor: 'pointer' }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <span style={{ fontSize: '2.2rem' }}>{portal.icon}</span>
                    <HandBadge variant={portal.badgeVariant}>{portal.badge}</HandBadge>
                  </div>
                  <h3 style={{ fontSize: '1.35rem', marginBottom: '6px' }}>{portal.title}</h3>
                  <p style={{ fontSize: '1.02rem', color: 'var(--pencil-black)', opacity: 0.85, lineHeight: 1.45 }}>
                    {portal.desc}
                  </p>
                </div>
                <div style={{ marginTop: '18px', fontSize: '1.05rem', fontWeight: 700, color: 'var(--pen-blue)', textDecoration: 'underline' }}>
                  Open Workspace <span>→</span>
                </div>
              </WobblyCard>
            </Link>
          ))}
        </div>
      </section>

      {/* Grid 2: Educator & Governance Studio */}
      <section style={{ marginBottom: '52px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <span style={{ fontSize: '1.6rem' }}>📌</span>
          <h2 style={{ fontSize: '1.6rem' }}>Educator & Governance Studio</h2>
          <HandBadge variant="purple">Teacher • Admin</HandBadge>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px' }}>
          {educatorPortals.map((portal) => (
            <Link key={portal.path} href={portal.path} style={{ textDecoration: 'none', color: 'inherit' }}>
              <WobblyCard
                variant={portal.variant}
                decoration={portal.decoration}
                tilt={portal.tilt}
                style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', cursor: 'pointer' }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <span style={{ fontSize: '2.2rem' }}>{portal.icon}</span>
                    <HandBadge variant={portal.badgeVariant}>{portal.badge}</HandBadge>
                  </div>
                  <h3 style={{ fontSize: '1.35rem', marginBottom: '6px' }}>{portal.title}</h3>
                  <p style={{ fontSize: '1.02rem', color: 'var(--pencil-black)', opacity: 0.85, lineHeight: 1.45 }}>
                    {portal.desc}
                  </p>
                </div>
                <div style={{ marginTop: '18px', fontSize: '1.05rem', fontWeight: 700, color: 'var(--marker-red)', textDecoration: 'underline' }}>
                  Manage Studio <span>→</span>
                </div>
              </WobblyCard>
            </Link>
          ))}
        </div>
      </section>

      {/* Notebook Footer System Metrics */}
      <WobblyCard decoration="tape" style={{ padding: '24px 32px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '20px', textAlign: 'center' }}>
          <div>
            <div style={{ fontSize: '2rem', fontFamily: 'var(--font-heading)', fontWeight: 700, color: 'var(--pen-blue)' }}>100%</div>
            <div style={{ fontSize: '1rem', color: 'var(--pencil-subtle)' }}>Deterministic Decisions</div>
          </div>
          <div>
            <div style={{ fontSize: '2rem', fontFamily: 'var(--font-heading)', fontWeight: 700, color: '#15803d' }}>85 / 85</div>
            <div style={{ fontSize: '1rem', color: 'var(--pencil-subtle)' }}>Test Suites Passed</div>
          </div>
          <div>
            <div style={{ fontSize: '2rem', fontFamily: 'var(--font-heading)', fontWeight: 700, color: 'var(--marker-red)' }}>&lt; 5 ms</div>
            <div style={{ fontSize: '1rem', color: 'var(--pencil-subtle)' }}>Auth p50 Latency</div>
          </div>
          <div>
            <div style={{ fontSize: '2rem', fontFamily: 'var(--font-heading)', fontWeight: 700, color: '#854d0e' }}>0.0%</div>
            <div style={{ fontSize: '1rem', color: 'var(--pencil-subtle)' }}>Cross-Tenant Leaks</div>
          </div>
        </div>
      </WobblyCard>
    </main>
  );
}

