'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface AdaptiveDecision {
  decision: string;
  target_concept_id: string;
  recommended_difficulty: number;
  reason: string;
  priority_level: number;
}

export default function StudentAdaptivePage() {
  const [conceptId, setConceptId] = useState<string>('00000000-0000-0000-0000-000000000000');
  const [versionId, setVersionId] = useState<string>('00000000-0000-0000-0000-000000000000');

  const [isLoading, setIsLoading] = useState(false);
  const [decision, setDecision] = useState<AdaptiveDecision | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchInitialIds();
  }, []);

  async function fetchInitialIds() {
    const currRes = await apiClient.get<any[]>('/api/v1/curricula');
    if (currRes.data && currRes.data.length > 0 && currRes.data[0].versions.length > 0) {
      const vId = currRes.data[0].versions[0].id;
      setVersionId(vId);
      const vRes = await apiClient.get<any>(`/api/v1/curricula/versions/${vId}`);
      if (vRes.data && vRes.data.chapters.length > 0 && vRes.data.chapters[0].topics.length > 0 && vRes.data.chapters[0].topics[0].concepts.length > 0) {
        setConceptId(vRes.data.chapters[0].topics[0].concepts[0].id);
      }
    }
  }

  async function handleGetDecision() {
    setIsLoading(true);
    setError(null);

    const res = await apiClient.post<AdaptiveDecision>('/api/v1/adaptive/decide', {
      concept_id: conceptId,
      curriculum_version_id: versionId
    });

    setIsLoading(false);

    if (res.error) {
      setError(`Decision Error: ${res.error.message}`);
    } else if (res.data) {
      setDecision(res.data);
    }
  }

  function getDecisionBadgeColor(dec: string) {
    switch (dec) {
      case 'CHALLENGE': return '#a855f7';
      case 'PROGRESS': return '#3b82f6';
      case 'REINFORCE': return '#f59e0b';
      case 'REMEDIATE': return '#ef4444';
      case 'SPACED_REVIEW': return '#10b981';
      case 'PREREQUISITE_REMEDIATION': return '#f97316';
      default: return '#64748b';
    }
  }

  return (
    <div style={{ padding: '32px', maxWidth: '900px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '2rem', color: '#818cf8', marginBottom: '8px' }}>
          Adaptive Learning Portal
        </h1>
        <p style={{ color: '#94a3b8' }}>
          Rule-based deterministic decision engine determining your next activity level without LLM hallucination.
        </p>
      </header>

      {error && (
        <div style={{ padding: '12px', borderRadius: '8px', backgroundColor: '#450a0a', border: '1px solid #ef4444', marginBottom: '20px', color: '#f87171' }}>
          {error}
        </div>
      )}

      {/* Action Control */}
      <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px', marginBottom: '28px', textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.3rem', marginBottom: '12px' }}>What should I learn next?</h2>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '20px' }}>
          Evaluates your concept mastery, confidence, prerequisite trees, and spaced repetition schedule.
        </p>

        <button
          onClick={handleGetDecision}
          disabled={isLoading}
          style={{
            padding: '14px 28px',
            backgroundColor: isLoading ? '#475569' : '#6366f1',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 'bold',
            fontSize: '1.1rem',
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
        >
          {isLoading ? 'Evaluating Adaptive Rules...' : '🎯 Get Next Adaptive Recommendation'}
        </button>
      </section>

      {/* Decision Card Output */}
      {decision && (
        <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '28px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <span style={{
              fontSize: '1rem',
              padding: '6px 14px',
              borderRadius: '6px',
              backgroundColor: getDecisionBadgeColor(decision.decision),
              color: '#fff',
              fontWeight: 'bold'
            }}>
              DECISION: {decision.decision}
            </span>

            <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
              Priority Level: #{decision.priority_level}
            </span>
          </div>

          <div style={{ fontSize: '1.2rem', color: '#38bdf8', marginBottom: '12px', fontWeight: 'bold' }}>
            Target Difficulty Level: {'⭐'.repeat(decision.recommended_difficulty)} (Level {decision.recommended_difficulty}/5)
          </div>

          <p style={{ fontSize: '1rem', color: '#cbd5e1', lineHeight: '1.5', background: '#0f172a', padding: '14px', borderRadius: '8px', marginBottom: '16px' }}>
            <strong>Reasoning:</strong> {decision.reason}
          </p>

          <span style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', textAlign: 'center' }}>
            ⚡ Decision made deterministically by AdaptiveDecisionEngine (0 LLM API calls).
          </span>
        </section>
      )}
    </div>
  );
}
