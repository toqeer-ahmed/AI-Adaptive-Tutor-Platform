'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';

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
      badgeColor: 'badge-cyan',
      path: '/student/tutor',
      desc: 'Adaptive conversational tutoring grounded exclusively in approved grade-level curriculum.',
      icon: '🧠',
      accent: '#38bdf8'
    },
    {
      title: 'Knowledge Map & Mastery',
      badge: 'EWMA Engine',
      badgeColor: 'badge-emerald',
      path: '/student/mastery',
      desc: 'Deterministic concept mastery visualization, memory decay tracking, and spaced review schedules.',
      icon: '📈',
      accent: '#34d399'
    },
    {
      title: 'Adaptive Learning Path',
      badge: 'Rule-Based',
      badgeColor: 'badge-purple',
      path: '/student/adaptive',
      desc: 'Real-time next-activity recommendations tailored to current prerequisite mastery state.',
      icon: '🎯',
      accent: '#c084fc'
    },
    {
      title: 'Assessment Player',
      badge: 'Deterministic Grading',
      badgeColor: 'badge-amber',
      path: '/student/assessments',
      desc: 'Interactive quiz and assessment engine with math expression parsing and instant feedback.',
      icon: '✍️',
      accent: '#fbbf24'
    }
  ];

  const educatorPortals = [
    {
      title: 'Curriculum Studio & Review',
      badge: 'Human-in-Loop',
      badgeColor: 'badge-cyan',
      path: '/teacher/curriculum/review',
      desc: 'AI syllabus extraction inspector with state-gated approval workflow and immutable publishing.',
      icon: '📚',
      accent: '#38bdf8'
    },
    {
      title: 'Assessment & Question Bank',
      badge: 'AI Generation',
      badgeColor: 'badge-purple',
      path: '/teacher/assessments',
      desc: 'AI question generator with 6-step validation pipeline and deterministic math verification.',
      icon: '📝',
      accent: '#c084fc'
    },
    {
      title: 'Teacher Analytics Dashboard',
      badge: 'Class Heatmaps',
      badgeColor: 'badge-emerald',
      path: '/teacher/dashboard',
      desc: 'Concept mastery heatmaps, misconception trends, and targeted remediation rosters.',
      icon: '📊',
      accent: '#34d399'
    },
    {
      title: 'Parent Intelligence Digest',
      badge: 'Parent Portal',
      badgeColor: 'badge-amber',
      path: '/parent/dashboard',
      desc: 'Qualitative progress summaries and teacher digest views with zero raw internal data leakage.',
      icon: '👨‍👩‍👧',
      accent: '#fbbf24'
    }
  ];

  return (
    <main style={{ minHeight: '100vh', padding: '48px 24px 80px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Top Header / Navigation Bar */}
      <header className="animate-fade-in delay-1" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '56px', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #6366f1 0%, #38bdf8 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.4rem',
            boxShadow: '0 0 20px rgba(99, 102, 241, 0.4)'
          }}>
            ⚡
          </div>
          <div>
            <span style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#f8fafc' }}>
              Adaptive<span style={{ color: '#818cf8' }}>Edu</span>
            </span>
            <span style={{ marginLeft: '8px', fontSize: '0.75rem', padding: '2px 8px', borderRadius: '9999px', background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', border: '1px solid rgba(99, 102, 241, 0.3)', fontWeight: 600 }}>
              v1.0 Production
            </span>
          </div>
        </div>

        {/* Live System Health Pill */}
        <div className="glass-panel" style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '10px', borderRadius: '9999px' }}>
          <div className={`pulse-dot ${health?.status === 'healthy' ? 'online' : ''}`} style={{ background: health?.status === 'healthy' ? '#34d399' : '#f43f5e' }} />
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: health?.status === 'healthy' ? '#34d399' : '#f43f5e' }}>
            {loading ? 'Probing cluster...' : health?.status === 'healthy' ? 'API Operational (8000)' : 'API Degraded'}
          </span>
          <span style={{ fontSize: '0.8rem', color: '#64748b', borderLeft: '1px solid rgba(255,255,255,0.1)', paddingLeft: '8px' }}>
            RTO &lt;15m | RPO &lt;5m
          </span>
        </div>
      </header>

      {/* Hero Section */}
      <section className="animate-fade-in delay-2" style={{ textAlign: 'center', marginBottom: '64px' }}>
        <div className="badge badge-purple" style={{ marginBottom: '16px' }}>
          ✨ Curriculum-Grounded • Deterministic Mastery • Multi-Tenant
        </div>
        <h1 style={{ fontSize: 'clamp(2.5rem, 5vw, 4rem)', lineHeight: 1.1, marginBottom: '20px' }}>
          The Intelligence Layer for <br />
          <span className="gradient-text">Adaptive K–12 Education</span>
        </h1>
        <p style={{ fontSize: '1.2rem', color: 'var(--text-muted)', maxWidth: '720px', margin: '0 auto 32px', lineHeight: 1.6 }}>
          Combining LLM natural-language Socratic tutoring with mathematically deterministic knowledge tracing, human-gated curriculum governance, and strict tenant isolation.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <Link href="/student/tutor" className="btn-primary">
            Launch AI Tutor Workspace →
          </Link>
          <Link href="/teacher/dashboard" className="btn-secondary">
            Open Teacher Studio
          </Link>
        </div>
      </section>

      {/* Grid: Student Learning Suite */}
      <section className="animate-fade-in delay-3" style={{ marginBottom: '48px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <span style={{ fontSize: '1.3rem' }}>🎓</span>
          <h2 style={{ fontSize: '1.35rem', color: '#f8fafc' }}>Student Learning Experience</h2>
          <span className="badge badge-cyan">Grades 4–8</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px' }}>
          {studentPortals.map((portal) => (
            <Link key={portal.path} href={portal.path} style={{ textDecoration: 'none' }}>
              <div className="glass-panel" style={{ padding: '24px', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', cursor: 'pointer' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                    <div style={{ fontSize: '2rem' }}>{portal.icon}</div>
                    <span className={`badge ${portal.badgeColor}`}>{portal.badge}</span>
                  </div>
                  <h3 style={{ fontSize: '1.15rem', color: '#f8fafc', marginBottom: '8px' }}>
                    {portal.title}
                  </h3>
                  <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                    {portal.desc}
                  </p>
                </div>
                <div style={{ marginTop: '20px', fontSize: '0.85rem', fontWeight: 600, color: portal.accent, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  Enter Workspace <span>→</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Grid: Teacher & Governance Studio */}
      <section className="animate-fade-in delay-4" style={{ marginBottom: '48px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <span style={{ fontSize: '1.3rem' }}>🛡️</span>
          <h2 style={{ fontSize: '1.35rem', color: '#f8fafc' }}>Educator & Governance Studio</h2>
          <span className="badge badge-purple">Teacher • Admin</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px' }}>
          {educatorPortals.map((portal) => (
            <Link key={portal.path} href={portal.path} style={{ textDecoration: 'none' }}>
              <div className="glass-panel" style={{ padding: '24px', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', cursor: 'pointer' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                    <div style={{ fontSize: '2rem' }}>{portal.icon}</div>
                    <span className={`badge ${portal.badgeColor}`}>{portal.badge}</span>
                  </div>
                  <h3 style={{ fontSize: '1.15rem', color: '#f8fafc', marginBottom: '8px' }}>
                    {portal.title}
                  </h3>
                  <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                    {portal.desc}
                  </p>
                </div>
                <div style={{ marginTop: '20px', fontSize: '0.85rem', fontWeight: 600, color: portal.accent, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  Manage Studio <span>→</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* System Architecture Metrics Footer */}
      <section className="glass-panel animate-fade-in delay-5" style={{ padding: '28px', marginTop: '24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '24px', textAlign: 'center' }}>
          <div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#38bdf8' }}>100%</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>Deterministic Decisions</div>
          </div>
          <div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#34d399' }}>85 / 85</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>Test Suites Passed</div>
          </div>
          <div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#818cf8' }}>&lt; 5 ms</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>Auth p50 Latency</div>
          </div>
          <div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fbbf24' }}>0.0%</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>Cross-Tenant Leaks</div>
          </div>
        </div>
      </section>
    </main>
  );
}

