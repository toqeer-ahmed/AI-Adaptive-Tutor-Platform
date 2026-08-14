'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import AuthenticatedShell from '@/components/AuthenticatedShell';
import {
  WobblyCard,
  WobblyButton,
  HandBadge
} from '@/lib/HandDrawnComponents';

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
    try {
      const meRes = await apiClient.get<any>('/api/v1/auth/me');
      if (meRes.data) {
        const res = await apiClient.get<StudentMisconceptionItem[]>(`/api/v1/misconceptions/student/${meRes.data.id}`);
        if (res.data && res.data.length > 0) {
          setMisconceptions(res.data);
        } else {
          // Demo fallback items
          setMisconceptions([
            {
              id: 'misc-1',
              concept_id: 'fractions-addition',
              misconception_code: 'ADD_DENOMINATORS_DIRECTLY',
              name: 'Adding Denominators Directly',
              description: 'Student computes 1/4 + 2/4 = 3/8 by adding denominators together instead of keeping the common denominator.',
              remediation_strategy: 'Use visual fraction bar models and pizza slicing examples to demonstrate why parts remain constant.',
              confidence: 0.94,
              status: 'DETECTED',
              evidence_count: 2,
              detected_at: new Date().toISOString(),
              resolved_at: null
            },
            {
              id: 'misc-2',
              concept_id: 'decimals-place-value',
              misconception_code: 'LONGER_DECIMAL_IS_LARGER',
              name: 'Longer Decimal Means Greater Value',
              description: 'Believing 0.125 > 0.5 because 125 has more digits than 5.',
              remediation_strategy: 'Align decimals on a place-value grid with trailing zeros (0.500 vs 0.125).',
              confidence: 0.88,
              status: 'RESOLVED',
              evidence_count: 3,
              detected_at: new Date(Date.now() - 86400000 * 3).toISOString(),
              resolved_at: new Date().toISOString()
            }
          ]);
        }
      }
    } catch (e) {
      // Ignore
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthenticatedShell allowedRoles={['Student', 'Teacher', 'SchoolAdmin', 'OrgAdmin', 'SuperAdmin', 'Parent']}>
      <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
        
        {/* Header Ribbon */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <h1 style={{ fontSize: '2.2rem', fontFamily: 'var(--font-heading)', color: 'var(--text-main)', margin: 0 }}>
                💡 Diagnostic Learning Insights
              </h1>
              <HandBadge variant="yellow">Targeted Remediation</HandBadge>
            </div>
            <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-handwriting)', fontSize: '1.15rem', margin: 0 }}>
              Identified thinking patterns, error explanations, and personalized recovery steps.
            </p>
          </div>
          <Link href="/student/dashboard">
            <WobblyButton variant="secondary">
              ← Back to Study Desk
            </WobblyButton>
          </Link>
        </div>

        {loading ? (
          <WobblyCard style={{ padding: '40px', textAlign: 'center' }}>
            <div style={{ fontSize: '1.2rem', color: 'var(--text-muted)', fontFamily: 'var(--font-handwriting)' }}>
              Analyzing student misconception history... ⏳
            </div>
          </WobblyCard>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {misconceptions.map((item, idx) => {
              const isResolved = item.status === 'RESOLVED';
              return (
                <WobblyCard
                  key={item.id}
                  decoration={idx === 0 ? 'tape' : 'none'}
                  style={{
                    padding: '28px',
                    borderLeft: isResolved ? '6px solid var(--color-secondary)' : '6px solid var(--color-accent)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <HandBadge variant={isResolved ? 'green' : 'yellow'}>
                        {isResolved ? 'RESOLVED 🟢' : 'ACTIVE MISCONCEPTION 🟡'}
                      </HandBadge>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                        Code: {item.misconception_code}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Confidence: {(item.confidence * 100).toFixed(0)}% • Evidence: {item.evidence_count} attempts
                    </span>
                  </div>

                  <h3 style={{ fontSize: '1.3rem', fontFamily: 'var(--font-heading)', color: 'var(--text-main)', margin: '0 0 8px 0' }}>
                    {item.name}
                  </h3>

                  <p style={{ fontSize: '1rem', color: 'var(--text-muted)', lineHeight: 1.5, margin: '0 0 16px 0' }}>
                    {item.description}
                  </p>

                  <div style={{ background: 'rgba(245, 158, 11, 0.08)', border: '1px dashed #f59e0b', borderRadius: '10px', padding: '16px', marginBottom: '16px' }}>
                    <div style={{ fontWeight: 'bold', color: '#b45309', marginBottom: '4px', fontSize: '0.95rem' }}>
                      🎯 Targeted Remediation Strategy:
                    </div>
                    <div style={{ fontSize: '0.95rem', color: 'var(--text-main)', lineHeight: 1.4 }}>
                      {item.remediation_strategy}
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                    <Link href={`/student/tutor?mode=remediation&concept=${item.concept_id}`}>
                      <WobblyButton variant="accent">
                        Practice Socratic Recovery with AI Tutor 🤖
                      </WobblyButton>
                    </Link>
                  </div>
                </WobblyCard>
              );
            })}
          </div>
        )}

      </div>
    </AuthenticatedShell>
  );
}
