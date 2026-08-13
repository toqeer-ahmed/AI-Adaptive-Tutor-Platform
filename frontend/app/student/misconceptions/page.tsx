'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface StudentMisconceptionItem {
  id: string;
  concept_id: string;
  misconception_code: string;
  name: string;
  description: string;
  remediation_strategy: string;
  confidence: number;
  status: string;
  evidence_count: number;
  detected_at: string;
  resolved_at: string | null;
}

export default function StudentMisconceptionPage() {
  const [misconceptions, setMisconceptions] = useState<StudentMisconceptionItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMisconceptionData();
  }, []);

  async function fetchMisconceptionData() {
    const meRes = await apiClient.get<any>('/api/v1/auth/me');
    if (meRes.data) {
      const res = await apiClient.get<StudentMisconceptionItem[]>(`/api/v1/misconceptions/student/${meRes.data.id}`);
      if (res.data) {
        setMisconceptions(res.data);
      }
    }
    setLoading(false);
  }

  function getStatusBadge(status: string) {
    switch (status) {
      case 'RESOLVED': return { label: 'RESOLVED 🟢', bg: '#15803d' };
      case 'PERSISTENT': return { label: 'PERSISTENT 🔴', bg: '#b91c1c' };
      case 'DETECTED': return { label: 'DETECTED 🟡', bg: '#b45309' };
      default: return { label: status, bg: '#475569' };
    }
  }

  return (
    <div style={{ padding: '32px', maxWidth: '1000px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '2rem', color: '#818cf8', marginBottom: '8px' }}>
          Misconception Remediation Inspector
        </h1>
        <p style={{ color: '#94a3b8' }}>
          Controlled taxonomy classification, error pattern evidence, confidence validation, and targeted remediation strategies.
        </p>
      </header>

      {/* Misconceptions Grid */}
      <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
        <h2 style={{ fontSize: '1.3rem', marginBottom: '16px' }}>Detected Student Misconceptions</h2>

        {loading ? (
          <p style={{ color: '#94a3b8' }}>Analyzing error evidence...</p>
        ) : misconceptions.length === 0 ? (
          <div style={{ padding: '20px', background: '#0f172a', borderRadius: '8px', textAlign: 'center', color: '#94a3b8' }}>
            🎉 No active misconceptions detected! Keep practicing assessment questions.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {misconceptions.map((m) => {
              const badge = getStatusBadge(m.status);
              const confPct = Math.round(m.confidence * 100);

              return (
                <div key={m.id} style={{ padding: '20px', background: '#0f172a', borderRadius: '10px', borderLeft: `4px solid ${badge.bg}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div>
                      <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', background: '#334155', color: '#38bdf8', fontWeight: 'bold', marginRight: '8px' }}>
                        CODE: {m.misconception_code}
                      </span>
                      <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#f8fafc' }}>
                        {m.name}
                      </span>
                    </div>

                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.8rem', color: '#34d399', fontWeight: 'bold' }}>
                        {confPct}% Confidence
                      </span>
                      <span style={{ fontSize: '0.75rem', padding: '4px 10px', borderRadius: '4px', backgroundColor: badge.bg, color: '#fff', fontWeight: 'bold' }}>
                        {badge.label}
                      </span>
                    </div>
                  </div>

                  <p style={{ fontSize: '0.9rem', color: '#cbd5e1', marginBottom: '12px' }}>
                    {m.description}
                  </p>

                  <div style={{ padding: '12px', background: '#1e293b', borderRadius: '6px', border: '1px solid #334155', marginBottom: '8px' }}>
                    <div style={{ fontSize: '0.8rem', color: '#fbbf24', fontWeight: 'bold', marginBottom: '2px' }}>
                      💡 Targeted Remediation Strategy:
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
                      {m.remediation_strategy || 'Review foundational fraction concepts step-by-step.'}
                    </div>
                  </div>

                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
                    <span>Evidence Instances: {m.evidence_count}</span>
                    <span>Detected At: {new Date(m.detected_at).toLocaleDateString()}</span>
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
