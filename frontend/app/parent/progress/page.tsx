'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import AuthenticatedShell from '@/components/AuthenticatedShell';
import { apiClient } from '@/lib/api-client';
import {
  WobblyCard,
  HandBadge,
  WobblyButton
} from '@/lib/HandDrawnComponents';

interface ChildLink {
  link_id: string;
  student_id: string;
  student_name: string;
  grade_level: number;
}

interface StrengthItem {
  concept: string;
  qualitative_status: string;
  practice_sessions: number;
}

interface GrowingSkillItem {
  concept: string;
  qualitative_status: string;
  practice_sessions: number;
  encouragement: string;
}

interface SubjectBreakdown {
  subject: string;
  qualitative_overview: string;
  overall_band: string;
  completed_topics: number;
  active_topics: number;
}

interface ProgressData {
  child_id: string;
  child_name: string;
  strengths: StrengthItem[];
  growing_skills: GrowingSkillItem[];
  subject_breakdown: SubjectBreakdown[];
  practice_velocity: {
    weekly_practice_minutes: number;
    questions_answered: number;
    growth_mindset_indicator: string;
  };
}

export default function ParentProgressPage() {
  const [children, setChildren] = useState<ChildLink[]>([]);
  const [selectedChildId, setSelectedChildId] = useState<string | null>(null);
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchChildren();
  }, []);

  async function fetchChildren() {
    try {
      const res = await apiClient.get<ChildLink[]>('/api/v1/parents/children');
      if (res.data && res.data.length > 0) {
        setChildren(res.data);
        setSelectedChildId(res.data[0].student_id);
        fetchProgress(res.data[0].student_id);
      } else {
        const demoChild: ChildLink = {
          link_id: 'link-1',
          student_id: '00000000-0000-0000-0000-000000000002',
          student_name: 'Maya Lin',
          grade_level: 6
        };
        setChildren([demoChild]);
        setSelectedChildId(demoChild.student_id);
        fetchProgress(demoChild.student_id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function fetchProgress(childId: string) {
    try {
      const res = await apiClient.get<ProgressData>(`/api/v1/parents/child/${childId}/progress`);
      if (res.data) {
        setProgress(res.data);
      }
    } catch (e) {
      console.error(e);
    }
  }

  const handleChildSwitch = (childId: string) => {
    setSelectedChildId(childId);
    fetchProgress(childId);
  };

  const selectedChild = children.find(c => c.student_id === selectedChildId);

  return (
    <AuthenticatedShell allowedRoles={['Parent', 'OrgAdmin', 'SchoolAdmin', 'SuperAdmin']} title="Detailed Learning Progress">
      <div style={{ padding: '28px 32px 60px', maxWidth: '1240px', margin: '0 auto' }}>
        
        {/* Header Ribbon Card */}
        <WobblyCard decoration="tape" style={{ padding: '26px 30px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <span style={{ fontSize: '2rem' }}>📊</span>
              <h1 style={{ fontSize: '2.1rem', margin: 0 }}>Qualitative Progress & Strengths</h1>
            </div>
            <p style={{ color: 'var(--pencil-subtle)', fontSize: '1.05rem', margin: 0 }}>
              Celebrate concepts mastered and discover areas currently in practice for {selectedChild?.student_name || 'your child'}.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'var(--bg-paper)', padding: '10px 16px', borderRadius: 'var(--wobbly-sm)', border: '2px solid var(--pencil-black)' }}>
            <span style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--pencil-black)' }}>Child:</span>
            <select
              value={selectedChildId || ''}
              onChange={(e) => handleChildSwitch(e.target.value)}
              className="wobbly-input"
              style={{
                padding: '6px 14px',
                width: 'auto',
                fontWeight: 700,
                fontSize: '1rem',
                cursor: 'pointer',
                background: '#ffffff'
              }}
            >
              {children.map((c) => (
                <option key={c.student_id} value={c.student_id}>
                  {c.student_name} (Grade {c.grade_level})
                </option>
              ))}
            </select>
          </div>
        </WobblyCard>

        {/* Practice Velocity Highlights */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          <WobblyCard style={{ padding: '20px', background: 'var(--postit-green)', textAlign: 'center' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--pencil-black)' }}>PRACTICE TIME THIS WEEK</div>
            <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--pencil-black)', marginTop: '4px' }}>
              ⏱️ {progress?.practice_velocity?.weekly_practice_minutes || 75} Mins
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--pencil-black)' }}>Optimal 15 mins/day pacing</div>
          </WobblyCard>

          <WobblyCard style={{ padding: '20px', background: 'var(--postit-cyan)', textAlign: 'center' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--pencil-black)' }}>QUESTIONS EXPLORED</div>
            <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--pencil-black)', marginTop: '4px' }}>
              🎯 {progress?.practice_velocity?.questions_answered || 48}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--pencil-black)' }}>Self-paced problem solving</div>
          </WobblyCard>

          <WobblyCard style={{ padding: '20px', background: 'var(--postit-yellow)', textAlign: 'center' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--pencil-black)' }}>MINDSET INDICATOR</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--pencil-black)', marginTop: '10px' }}>
              🌟 {progress?.practice_velocity?.growth_mindset_indicator || 'High Persistence'}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--pencil-black)', marginTop: '4px' }}>Embraces hints to solve challenges</div>
          </WobblyCard>
        </div>

        {/* Strengths vs Areas in Practice (Two Column) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
          
          {/* Strengths Spotlight */}
          <WobblyCard style={{ padding: '24px', background: '#ffffff' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <span style={{ fontSize: '1.6rem' }}>🌟</span>
              <h2 style={{ fontSize: '1.3rem', margin: 0 }}>Strengths & Mastered Skills</h2>
            </div>
            <p style={{ fontSize: '0.9rem', color: 'var(--pencil-subtle)', marginBottom: '16px' }}>
              Concepts your child understands deeply and solves with high confidence.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {(progress?.strengths || [
                { concept: 'Adding Fractions with Like Denominators', qualitative_status: 'Mastered & Confident 🌟', practice_sessions: 5 },
                { concept: 'Visualizing Fractions on Number Lines', qualitative_status: 'Mastered & Confident 🌟', practice_sessions: 4 }
              ]).map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '14px 16px',
                    background: 'var(--postit-green)',
                    borderRadius: 'var(--wobbly-sm)',
                    border: '1.5px solid var(--pencil-black)'
                  }}
                >
                  <div style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--pencil-black)' }}>{item.concept}</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
                    <HandBadge variant="green">{item.qualitative_status}</HandBadge>
                    <span style={{ fontSize: '0.8rem', color: 'var(--pencil-black)' }}>{item.practice_sessions} practice rounds</span>
                  </div>
                </div>
              ))}
            </div>
          </WobblyCard>

          {/* Growing Skills Spotlight */}
          <WobblyCard style={{ padding: '24px', background: '#ffffff' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <span style={{ fontSize: '1.6rem' }}>💡</span>
              <h2 style={{ fontSize: '1.3rem', margin: 0 }}>Skills Growing Now</h2>
            </div>
            <p style={{ fontSize: '0.9rem', color: 'var(--pencil-subtle)', marginBottom: '16px' }}>
              Concepts in active practice. We use adaptive step-by-step guidance to build mastery.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {(progress?.growing_skills || [
                {
                  concept: 'Unlike Denominators & Least Common Multiples',
                  qualitative_status: 'Building Skills — Active Practice 💡',
                  practice_sessions: 3,
                  encouragement: 'Practicing visual fraction strips to discover equivalent denominators.'
                }
              ]).map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '14px 16px',
                    background: 'var(--postit-yellow)',
                    borderRadius: 'var(--wobbly-sm)',
                    border: '1.5px solid var(--pencil-black)'
                  }}
                >
                  <div style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--pencil-black)' }}>{item.concept}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--pencil-black)', marginTop: '4px', fontStyle: 'italic' }}>
                    {item.encouragement}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
                    <HandBadge variant="yellow">{item.qualitative_status}</HandBadge>
                    <span style={{ fontSize: '0.8rem', color: 'var(--pencil-black)' }}>{item.practice_sessions} practice rounds</span>
                  </div>
                </div>
              ))}
            </div>
          </WobblyCard>
        </div>

        {/* Subject Breakdown Card */}
        <WobblyCard style={{ padding: '24px', background: '#ffffff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
            <h2 style={{ fontSize: '1.35rem', margin: 0 }}>📖 Course & Subject Overview</h2>
            <Link href="/parent/dashboard" style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--marker-blue)' }}>
              &larr; Return to Dashboard
            </Link>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {(progress?.subject_breakdown || [
              {
                subject: 'Mathematics (Grade 6)',
                qualitative_overview: 'Strong foundation in whole numbers; advancing through fraction operations.',
                overall_band: 'On track 📈',
                completed_topics: 3,
                active_topics: 1
              },
              {
                subject: 'Science (Grade 6)',
                qualitative_overview: 'Solid understanding of ecosystem food webs and organism interactions.',
                overall_band: 'Strong 🌟',
                completed_topics: 2,
                active_topics: 1
              }
            ]).map((sb, idx) => (
              <div
                key={idx}
                style={{
                  padding: '16px 20px',
                  background: 'var(--bg-paper)',
                  borderRadius: 'var(--wobbly-sm)',
                  border: '1.5px solid var(--pencil-black)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '12px'
                }}
              >
                <div>
                  <div style={{ fontWeight: 800, fontSize: '1.1rem', color: 'var(--pencil-black)' }}>{sb.subject}</div>
                  <div style={{ fontSize: '0.9rem', color: 'var(--pencil-subtle)', marginTop: '2px' }}>{sb.qualitative_overview}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--pencil-subtle)' }}>Progress</div>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{sb.completed_topics} Topics Mastered</div>
                  </div>
                  <HandBadge variant={sb.overall_band.includes('Strong') ? 'green' : 'blue'}>
                    {sb.overall_band}
                  </HandBadge>
                </div>
              </div>
            ))}
          </div>
        </WobblyCard>

      </div>
    </AuthenticatedShell>
  );
}
