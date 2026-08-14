'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import AuthenticatedShell from '@/components/AuthenticatedShell';
import { apiClient } from '@/lib/api-client';
import {
  WobblyCard,
  WobblyButton,
  HandBadge,
  ScribbleUnderline
} from '@/lib/HandDrawnComponents';

interface PathNode {
  id: string;
  title: string;
  state: 'MASTERED' | 'IN_PROGRESS' | 'PRACTICE' | 'REMEDIATION' | 'CHALLENGE' | 'NOT_STARTED';
  difficulty: number;
  description: string;
  badgeLabel: string;
}

export default function StudentAdaptivePathPage() {
  const [learningNodes, setLearningNodes] = useState<PathNode[]>([
    {
      id: 'node-1',
      title: '1. Equal-Sized Parts & Unit Fractions',
      state: 'MASTERED',
      difficulty: 1,
      description: 'Understanding fractions as equal divisions of a whole with pizza models.',
      badgeLabel: 'Mastered 🌟'
    },
    {
      id: 'node-2',
      title: '2. Equivalent Fractions on a Number Line',
      state: 'MASTERED',
      difficulty: 2,
      description: 'Locating 1/2, 2/4, 3/6 at identical positions along a coordinate line.',
      badgeLabel: 'Mastered 🌟'
    },
    {
      id: 'node-3',
      title: '3. Adding Unlike Fractions with Common Denominators (LCM)',
      state: 'REMEDIATION',
      difficulty: 3,
      description: 'Finding least common denominators and avoiding adding denominators directly.',
      badgeLabel: 'Current Focus 💡'
    },
    {
      id: 'node-4',
      title: '4. Mixed Numbers & Improper Fraction Arithmetic',
      state: 'PRACTICE',
      difficulty: 4,
      description: 'Regrouping whole numbers when fraction sums exceed one whole.',
      badgeLabel: 'Up Next 🎯'
    },
    {
      id: 'node-5',
      title: '5. Multi-Step Real World Fraction Word Problems',
      state: 'CHALLENGE',
      difficulty: 5,
      description: 'Advanced enrichment challenge: multi-recipe baking scaling problems.',
      badgeLabel: 'Challenge 🚀'
    }
  ]);

  const [adaptiveDecision, setAdaptiveDecision] = useState<{
    decision: string;
    reason: string;
    recommended_difficulty: number;
  }>({
    decision: 'REMEDIATE',
    reason: 'Active misconception detected (adding denominators directly). Providing visual fraction bar models.',
    recommended_difficulty: 3
  });

  function getNodeStyle(state: string) {
    switch (state) {
      case 'MASTERED':
        return { bg: '#ecfdf5', border: '#10b981', icon: '🌟', badgeVariant: 'green' as const };
      case 'REMEDIATION':
        return { bg: '#fffbeb', border: '#f59e0b', icon: '💡', badgeVariant: 'yellow' as const };
      case 'PRACTICE':
      case 'IN_PROGRESS':
        return { bg: '#eef2ff', border: '#6366f1', icon: '📈', badgeVariant: 'blue' as const };
      case 'CHALLENGE':
        return { bg: '#fdf4ff', border: '#c026d3', icon: '🚀', badgeVariant: 'purple' as const };
      default:
        return { bg: '#f8fafc', border: '#94a3b8', icon: '🔒', badgeVariant: 'yellow' as const };
    }
  }

  return (
    <AuthenticatedShell allowedRoles={['Student', 'Teacher', 'SchoolAdmin', 'OrgAdmin', 'SuperAdmin', 'Parent']} title="Adaptive Learning Path">
      <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
        
        {/* Header Ribbon */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <h1 style={{ fontSize: '2.2rem', fontFamily: 'var(--font-heading)', color: 'var(--text-main)', margin: 0 }}>
                🧭 My Visual Learning Path
              </h1>
              <HandBadge variant="purple">Deterministic Engine</HandBadge>
            </div>
            <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-handwriting)', fontSize: '1.15rem', margin: 0 }}>
              Your personalized study roadmap. The backend adaptive engine adjusts steps based on your mastery.
            </p>
          </div>
          <Link href="/student/dashboard">
            <WobblyButton variant="secondary">
              ← Back to Study Desk
            </WobblyButton>
          </Link>
        </div>

        {/* Current Adaptive Recommendation Post-It */}
        <WobblyCard decoration="tape" style={{ padding: '26px', background: '#fff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '1.8rem' }}>🎯</span>
              <h2 style={{ fontSize: '1.35rem', fontFamily: 'var(--font-heading)', margin: 0, color: 'var(--text-main)' }}>
                Today's Prescribed Learning Step
              </h2>
            </div>
            <HandBadge variant="yellow">Action: {adaptiveDecision.decision}</HandBadge>
          </div>
          <p style={{ fontSize: '1.05rem', color: 'var(--text-main)', lineHeight: 1.5, margin: '0 0 16px 0' }}>
            {adaptiveDecision.reason}
          </p>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <Link href="/student/lesson">
              <WobblyButton variant="primary">
                Launch Lesson 1.1 📖
              </WobblyButton>
            </Link>
            <Link href="/student/tutor?mode=remediation">
              <WobblyButton variant="accent">
                Socratic Review with AI Tutor 🤖
              </WobblyButton>
            </Link>
            <Link href="/student/assessments">
              <WobblyButton variant="secondary">
                Practice Quiz ✏️
              </WobblyButton>
            </Link>
          </div>
        </WobblyCard>

        {/* Visual Path Node Stepper */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0px', position: 'relative' }}>
          <h2 style={{ fontSize: '1.4rem', fontFamily: 'var(--font-heading)', margin: '0 0 20px 0' }}>
            🗺️ Unit Roadmap: Rational Numbers & Fractions
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {learningNodes.map((node, idx) => {
              const style = getNodeStyle(node.state);
              const isCurrent = node.state === 'REMEDIATION' || node.state === 'IN_PROGRESS';

              return (
                <div key={node.id} style={{ display: 'flex', gap: '20px', alignItems: 'flex-start' }}>
                  {/* Vertical Connector Line */}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '48px' }}>
                    <div
                      style={{
                        width: '44px',
                        height: '44px',
                        borderRadius: '50%',
                        background: style.bg,
                        border: `3px solid ${style.border}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '1.3rem',
                        fontWeight: 'bold',
                        zIndex: 2
                      }}
                    >
                      {style.icon}
                    </div>
                    {idx < learningNodes.length - 1 && (
                      <div style={{ width: '4px', height: '60px', background: 'var(--border-dark)', margin: '4px 0' }} />
                    )}
                  </div>

                  {/* Node Content Card */}
                  <WobblyCard
                    decoration={isCurrent ? 'tack-red' : 'none'}
                    style={{
                      flex: 1,
                      padding: '20px 24px',
                      borderLeft: `6px solid ${style.border}`,
                      background: isCurrent ? '#ffffff' : '#fdfcf9'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <h3 style={{ fontSize: '1.2rem', fontFamily: 'var(--font-heading)', margin: 0, color: 'var(--text-main)' }}>
                        {node.title}
                      </h3>
                      <HandBadge variant={style.badgeVariant}>
                        {node.badgeLabel}
                      </HandBadge>
                    </div>
                    <p style={{ fontSize: '0.95rem', color: 'var(--text-muted)', lineHeight: 1.4, margin: '0 0 12px 0' }}>
                      {node.description}
                    </p>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                        Target Difficulty: Level {node.difficulty} of 5
                      </span>
                      <Link href={node.state === 'MASTERED' ? '/student/assessments' : '/student/lesson'}>
                        <span style={{ color: 'var(--color-primary)', fontWeight: 'bold', fontSize: '0.9rem', cursor: 'pointer' }}>
                          {node.state === 'MASTERED' ? 'Review Quiz →' : 'Enter Step →'}
                        </span>
                      </Link>
                    </div>
                  </WobblyCard>
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </AuthenticatedShell>
  );
}
