'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';

interface HealthStatus {
  status: string;
  version: string;
  environment: string;
  services?: {
    postgresql: string;
    redis: string;
  };
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function checkHealth() {
      const res = await apiClient.get<HealthStatus>('/api/v1/health');
      if (res.data) {
        setHealth(res.data);
      }
      setLoading(false);
    }
    checkHealth();
  }, []);

  const navLinks = [
    { title: '🤖 AI Instructor Chat Workspace', path: '/student/tutor', desc: 'Grade 6 grounded Socratic & hint tutoring' },
    { title: '📊 Student Knowledge Map', path: '/student/mastery', desc: 'Deterministic concept mastery & review schedule' },
    { title: '🎯 Adaptive Learning Portal', path: '/student/adaptive', desc: 'Rule-based next activity recommendations' },
    { title: '📝 Teacher Quiz & Question Builder', path: '/teacher/assessments', desc: 'AI question generator & verification' },
    { title: '✍️ Student Assessment Player', path: '/student/assessments', desc: 'Quiz player with deterministic scoring' },
    { title: '🔍 Curriculum RAG Search', path: '/student/rag', desc: 'Pre-retrieval tenant-isolated hybrid vector search' },
    { title: '📄 Curriculum Human Review', path: '/teacher/curriculum/review', desc: 'Teacher review inspector for AI extractions' }
  ];

  return (
    <main style={{ padding: '40px', maxWidth: '1000px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      <header style={{ marginBottom: '32px', textAlign: 'center' }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '8px', color: '#818cf8' }}>
          AI Adaptive Education Platform
        </h1>
        <p style={{ fontSize: '1.1rem', color: '#94a3b8' }}>
          Production-Grade Multi-Tenant Learning System (Grades 4–8)
        </p>
      </header>

      {/* Navigation Portal Hub */}
      <section style={{ marginBottom: '40px' }}>
        <h2 style={{ fontSize: '1.4rem', color: '#38bdf8', marginBottom: '16px' }}>🚀 Feature Portals</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          {navLinks.map((link) => (
            <Link key={link.path} href={link.path} style={{ textDecoration: 'none' }}>
              <div style={{
                padding: '18px',
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '10px',
                cursor: 'pointer',
                transition: 'border-color 0.2s'
              }}>
                <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#f8fafc', marginBottom: '4px' }}>
                  {link.title}
                </div>
                <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                  {link.desc}
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* System Health Status */}
      <section style={{
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '12px',
        padding: '24px'
      }}>
        <h2 style={{ fontSize: '1.3rem', marginBottom: '16px', color: '#f8fafc' }}>
          System Health Status
        </h2>
        {loading ? (
          <p style={{ color: '#94a3b8' }}>Checking backend health...</p>
        ) : health ? (
          <div>
            <p style={{ marginBottom: '8px' }}>
              <strong>API Status:</strong>{' '}
              <span style={{ color: health.status === 'healthy' ? '#4ade80' : '#f87171' }}>
                {health.status.toUpperCase()}
              </span>
            </p>
            <p style={{ marginBottom: '8px' }}>
              <strong>Environment:</strong> {health.environment}
            </p>
            <p style={{ marginBottom: '12px' }}>
              <strong>Version:</strong> {health.version}
            </p>
            {health.services && (
              <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #334155' }}>
                <p style={{ marginBottom: '4px' }}>
                  PostgreSQL: <span style={{ color: health.services.postgresql === 'reachable' ? '#4ade80' : '#f87171' }}>{health.services.postgresql}</span>
                </p>
                <p>
                  Redis: <span style={{ color: health.services.redis === 'reachable' ? '#4ade80' : '#f87171' }}>{health.services.redis}</span>
                </p>
              </div>
            )}
          </div>
        ) : (
          <p style={{ color: '#f87171' }}>Backend API unreachable at http://localhost:8000</p>
        )}
      </section>
    </main>
  );
}
