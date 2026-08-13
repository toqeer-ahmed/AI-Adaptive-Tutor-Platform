'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface ConceptMastery {
  id: string;
  concept_id: string;
  mastery_score: number;
  confidence: number;
  attempt_count: number;
  correct_count: number;
  incorrect_count: number;
  status: string;
  last_practiced_at: string | null;
  next_review_due_at: string | null;
}

export default function StudentMasteryDashboard() {
  const [masteries, setMasteries] = useState<ConceptMastery[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMasteryData();
  }, []);

  async function fetchMasteryData() {
    // Fetch logged in user profile first
    const meRes = await apiClient.get<any>('/api/v1/auth/me');
    if (meRes.data) {
      const res = await apiClient.get<ConceptMastery[]>(`/api/v1/mastery/student/${meRes.data.id}`);
      if (res.data) {
        setMasteries(res.data);
      }
    }
    setLoading(false);
  }

  const masteredCount = masteries.filter(m => m.status === 'MASTERED').length;
  const inProgressCount = masteries.filter(m => m.status === 'IN_PROGRESS').length;
  const remediationCount = masteries.filter(m => m.status === 'NEEDS_REMEDIATION').length;

  function getStatusColor(status: string) {
    switch (status) {
      case 'MASTERED': return '#22c55e';
      case 'NEEDS_REMEDIATION': return '#ef4444';
      case 'IN_PROGRESS': return '#3b82f6';
      default: return '#94a3b8';
    }
  }

  return (
    <div style={{ padding: '32px', maxWidth: '1100px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '2rem', color: '#818cf8', marginBottom: '8px' }}>
          Student Knowledge Map & Mastery Dashboard
        </h1>
        <p style={{ color: '#94a3b8' }}>
          Deterministic, versioned concept mastery status and spaced repetition review schedule.
        </p>
      </header>

      {/* Overview Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px', marginBottom: '32px' }}>
        <div style={{ padding: '20px', background: '#0f172a', border: '1px solid #166534', borderRadius: '10px' }}>
          <div style={{ fontSize: '0.9rem', color: '#4ade80' }}>Concepts Mastered</div>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#22c55e' }}>{masteredCount}</div>
        </div>

        <div style={{ padding: '20px', background: '#0f172a', border: '1px solid #1e40af', borderRadius: '10px' }}>
          <div style={{ fontSize: '0.9rem', color: '#60a5fa' }}>In Progress</div>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#3b82f6' }}>{inProgressCount}</div>
        </div>

        <div style={{ padding: '20px', background: '#0f172a', border: '1px solid #991b1b', borderRadius: '10px' }}>
          <div style={{ fontSize: '0.9rem', color: '#f87171' }}>Needs Remediation</div>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#ef4444' }}>{remediationCount}</div>
        </div>
      </div>

      {/* Concept Grid */}
      <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
        <h2 style={{ fontSize: '1.3rem', marginBottom: '16px' }}>Concept Progress & Review Due Dates</h2>

        {loading ? (
          <p style={{ color: '#94a3b8' }}>Loading mastery data...</p>
        ) : masteries.length === 0 ? (
          <p style={{ color: '#94a3b8' }}>No assessment attempts recorded yet. Complete quizzes to build your knowledge map.</p>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {masteries.map((m) => {
              const scorePct = Math.round(m.mastery_score * 100);
              const confPct = Math.round(m.confidence * 100);

              return (
                <div key={m.id} style={{ padding: '16px', background: '#0f172a', borderRadius: '8px', border: '1px solid #334155' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <span style={{ fontWeight: 'bold', color: '#38bdf8' }}>Concept ID: {m.concept_id.slice(0, 8)}...</span>
                    <span style={{
                      fontSize: '0.75rem',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      backgroundColor: getStatusColor(m.status),
                      color: '#fff',
                      fontWeight: 'bold'
                    }}>
                      {m.status}
                    </span>
                  </div>

                  {/* Mastery Progress Bar */}
                  <div style={{ marginBottom: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>
                      <span>Mastery Score</span>
                      <span>{scorePct}%</span>
                    </div>
                    <div style={{ height: '8px', background: '#334155', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{ width: `${scorePct}%`, height: '100%', background: getStatusColor(m.status), transition: 'width 0.3s' }} />
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#94a3b8' }}>
                    <span>Confidence: {confPct}% ({m.attempt_count} attempts)</span>
                    <span>Next Review: {m.next_review_due_at ? new Date(m.next_review_due_at).toLocaleDateString() : 'N/A'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
