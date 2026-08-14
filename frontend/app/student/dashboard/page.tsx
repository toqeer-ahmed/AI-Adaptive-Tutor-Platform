'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import AuthenticatedShell from '@/components/AuthenticatedShell';
import { useAuth } from '@/lib/auth-context';
import { apiClient } from '@/lib/api-client';
import {
  WobblyCard,
  WobblyButton,
  HandBadge,
  ScribbleUnderline
} from '@/lib/HandDrawnComponents';

interface AdaptiveDecision {
  action: string;
  reason: string;
  recommended_concept_id: string;
  recommended_concept_name: string;
  recommended_difficulty: string;
}

interface AssessmentItem {
  id: string;
  title: string;
  assessment_type: string;
  status: 'pending' | 'due_soon' | 'completed';
  due_date: string;
}

export default function StudentDashboardPage() {
  const { user } = useAuth();
  const [decision, setDecision] = useState<AdaptiveDecision | null>(null);
  const [loadingDecision, setLoadingDecision] = useState(true);

  useEffect(() => {
    fetchAdaptiveRecommendation();
  }, [user]);

  async function fetchAdaptiveRecommendation() {
    try {
      const studentId = user?.id || '00000000-0000-0000-0000-000000000002';
      const res = await apiClient.post<AdaptiveDecision>('/api/v1/adaptive/decide', {
        student_id: studentId,
        recent_performance: 0.85
      });
      if (res.data) {
        setDecision(res.data);
      }
    } catch (e) {
      // Demo fallback
      setDecision({
        action: 'PRACTICE',
        reason: 'Optimal review interval reached for Adding Fractions with Common Denominators.',
        recommended_concept_id: '00000000-0000-0000-0000-000000000010',
        recommended_concept_name: 'Adding Fractions with Common Denominators',
        recommended_difficulty: 'MEDIUM'
      });
    } finally {
      setLoadingDecision(false);
    }
  }

  return (
    <AuthenticatedShell allowedRoles={['Student', 'OrgAdmin', 'SchoolAdmin', 'SuperAdmin']} title="My Study Desk">
      <div style={{ padding: '28px 32px 60px', maxWidth: '1200px', margin: '0 auto' }}>
        {/* Welcome Header Post-it */}
        <WobblyCard decoration="tape" style={{ padding: '26px 30px', marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <span style={{ fontSize: '2rem' }}>🎒</span>
              <h1 style={{ fontSize: '2.2rem' }}>
                Hi, {user?.full_name?.split(' ')[0] || 'Alex'}! Ready to Learn?
              </h1>
            </div>
            <p style={{ color: 'var(--pencil-subtle)', fontSize: '1.05rem' }}>
              Grade 6 Mathematics &bull; Section A &bull; Oakridge Middle School
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <HandBadge variant="yellow">Daily Goal: 3 / 4 Concepts</HandBadge>
            <HandBadge variant="green">Streak: 5 Days 🔥</HandBadge>
          </div>
        </WobblyCard>

        {/* Top Grid: Continue Learning Banner + Ask AI Socratic Tutor */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '24px', marginBottom: '28px' }}>
          {/* Section A: Continue Learning (Adaptive Recommendation) */}
          <WobblyCard variant="yellow" decoration="tack-red" tilt="left-sm" style={{ padding: '28px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.4rem' }}>🚀</span>
                <h2 style={{ fontSize: '1.4rem' }}>
                  Continue Learning
                </h2>
              </div>
              <HandBadge variant="blue">Adaptive Engine</HandBadge>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '0.88rem', color: 'var(--pencil-subtle)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Recommended Next Step
              </div>
              <div style={{ fontSize: '1.35rem', fontFamily: 'var(--font-heading)', fontWeight: 700, color: 'var(--pencil-black)', marginTop: '4px' }}>
                {decision?.recommended_concept_name || 'Adding Fractions with Common Denominators'}
              </div>
              <p style={{ color: 'var(--pencil-subtle)', fontSize: '0.95rem', marginTop: '6px', lineHeight: 1.4 }}>
                {decision?.reason || 'You are making steady progress! Complete 3 guided practice problems to build confidence.'}
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
              <Link href="/student/lesson" style={{ textDecoration: 'none' }}>
                <WobblyButton variant="red" style={{ fontSize: '1.05rem', padding: '10px 20px' }}>
                  Launch Lesson 📖
                </WobblyButton>
              </Link>
              <Link href="/student/assessments" style={{ textDecoration: 'none' }}>
                <WobblyButton variant="secondary" style={{ fontSize: '1.05rem', padding: '10px 16px' }}>
                  Practice Quiz ✏️
                </WobblyButton>
              </Link>
              <Link href="/student/adaptive" style={{ color: 'var(--pen-blue)', fontSize: '0.95rem', fontWeight: 700, textDecoration: 'none' }}>
                View Learning Path →
              </Link>
            </div>
          </WobblyCard>

          {/* Section E: Ask AI Socratic Tutor */}
          <WobblyCard variant="cyan" decoration="tack-blue" tilt="right-sm" style={{ padding: '28px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '1.4rem' }}>🤖</span>
                  <h2 style={{ fontSize: '1.4rem' }}>
                    AI Socratic Tutor
                  </h2>
                </div>
                <HandBadge variant="purple">Child Safe</HandBadge>
              </div>

              <p style={{ fontSize: '1rem', color: 'var(--pencil-black)', lineHeight: 1.5, marginBottom: '16px' }}>
                Stuck on a tricky math problem? Ask your AI Tutor! It guides you step-by-step with hints instead of just giving answers.
              </p>
            </div>

            <Link href="/student/tutor" style={{ textDecoration: 'none' }}>
              <WobblyButton variant="blue" style={{ width: '100%', fontSize: '1.05rem', padding: '10px' }}>
                💬 Chat with AI Tutor
              </WobblyButton>
            </Link>
          </WobblyCard>
        </div>

        {/* Section B: My Enrolled Subjects */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '1.5rem' }}>
              📚 My Enrolled Subjects
            </h2>
            <Link href="/student/subjects" style={{ fontSize: '0.95rem', color: 'var(--pen-blue)', fontWeight: 700, textDecoration: 'none' }}>
              Browse All Units &amp; Topics →
            </Link>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '18px' }}>
            {[
              { name: 'Mathematics 6', topic: 'Fractions & Mixed Numbers', color: 'yellow' as const, icon: '📐', progress: 'On track 📈' },
              { name: 'Earth Science', topic: 'Solar System & Atmosphere', color: 'green' as const, icon: '🌍', progress: 'Strong 🌟' },
              { name: 'Language Arts', topic: 'Context Clues & Inferences', color: 'purple' as const, icon: '📖', progress: 'Strong 🌟' },
              { name: 'Computer Science', topic: 'Loops & Conditional Logic', color: 'orange' as const, icon: '💻', progress: 'Getting there 💡' }
            ].map((sub, idx) => (
              <Link key={idx} href="/student/subjects" style={{ textDecoration: 'none' }}>
                <WobblyCard variant={sub.color} style={{ padding: '20px', cursor: 'pointer', height: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <span style={{ fontSize: '1.8rem' }}>{sub.icon}</span>
                    <HandBadge variant={sub.progress.includes('Strong') ? 'green' : sub.progress.includes('On track') ? 'blue' : 'yellow'} style={{ fontSize: '0.8rem' }}>
                      {sub.progress}
                    </HandBadge>
                  </div>
                  <div style={{ fontFamily: 'var(--font-heading)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--pencil-black)' }}>
                    {sub.name}
                  </div>
                  <div style={{ fontSize: '0.88rem', color: 'var(--pencil-subtle)', marginTop: '4px' }}>
                    {sub.topic}
                  </div>
                </WobblyCard>
              </Link>
            ))}
          </div>
        </div>

        {/* Bottom Grid: Assignments & Qualitative Progress */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px' }}>
          {/* Section C: Assignments & Practice */}
          <WobblyCard style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.35rem' }}>
                📝 Practice &amp; Assignments
              </h2>
              <Link href="/student/assessments" style={{ color: 'var(--pen-blue)', fontSize: '0.9rem', fontWeight: 700, textDecoration: 'none' }}>
                View All →
              </Link>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[
                { title: 'Fractions Diagnostic Quiz (Section 3.2)', type: 'Adaptive Checkpoint', due: 'Tomorrow, 5:00 PM', status: 'due_soon', tag: 'Due Soon ⏰', var: 'yellow' as const },
                { title: 'Simplifying Mixed Fractions Practice', type: 'Spaced Review', due: 'Friday', status: 'pending', tag: 'Recommended 💡', var: 'blue' as const },
                { title: 'Equivalent Fractions Mastery Check', type: 'Mastery Quiz', due: 'Completed Yesterday', status: 'completed', tag: 'Mastered 🌟', var: 'green' as const }
              ].map((ass, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '14px 16px',
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
                    <div style={{ fontWeight: 700, color: 'var(--pencil-black)', fontSize: '1.02rem' }}>
                      {ass.title}
                    </div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--pencil-subtle)', marginTop: '2px' }}>
                      {ass.type} &bull; {ass.due}
                    </div>
                  </div>
                  <HandBadge variant={ass.var} style={{ fontSize: '0.82rem' }}>
                    {ass.tag}
                  </HandBadge>
                </div>
              ))}
            </div>
          </WobblyCard>

          {/* Section F: Qualitative Progress (Zero Raw Numbers) */}
          <WobblyCard variant="green" decoration="tape" tilt="right-sm" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.35rem' }}>
                📊 Learning Progress
              </h2>
              <Link href="/student/mastery" style={{ color: 'var(--pen-blue)', fontSize: '0.9rem', fontWeight: 700, textDecoration: 'none' }}>
                Knowledge Map →
              </Link>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[
                { concept: 'Adding Fractions (Same Denominator)', status: 'Strong 🌟', badgeVar: 'green' as const, note: 'Ready for challenge problems!' },
                { concept: 'Finding Least Common Denominators', status: 'On track 📈', badgeVar: 'blue' as const, note: 'Practice 2 more questions' },
                { concept: 'Converting Improper Fractions', status: 'Getting there 💡', badgeVar: 'yellow' as const, note: 'Review with Socratic tutor' }
              ].map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '12px 14px',
                    background: '#ffffff',
                    borderRadius: 'var(--wobbly-sm)',
                    border: '1.5px solid var(--pencil-black)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--pencil-black)' }}>
                      {item.concept}
                    </span>
                    <HandBadge variant={item.badgeVar} style={{ fontSize: '0.8rem' }}>
                      {item.status}
                    </HandBadge>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--pencil-subtle)' }}>
                    {item.note}
                  </div>
                </div>
              ))}
            </div>
          </WobblyCard>
        </div>
      </div>
    </AuthenticatedShell>
  );
}
