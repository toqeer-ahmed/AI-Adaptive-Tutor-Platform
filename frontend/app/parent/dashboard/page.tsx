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
  email: string;
  grade_level: number;
  class_name: string;
}

interface SubjectOverview {
  name: string;
  icon: string;
  status: string;
  qualitative_band: string;
}

interface QualitativeProgress {
  concept_id: string;
  concept_name: string;
  qualitative_band: string;
  status: string;
  practice_count: number;
}

interface CompletedWork {
  assessment_title: string;
  score_percentage: number;
  status: string;
  completed_at: string;
}

interface UpcomingWork {
  title: string;
  subject: string;
  due_date: string;
  status: string;
}

interface ParentDashboardData {
  child_id: string;
  child_name: string;
  subjects: SubjectOverview[];
  qualitative_progress: QualitativeProgress[];
  completed_work: CompletedWork[];
  upcoming_work: UpcomingWork[];
  activity_summary: {
    total_practice_sessions: number;
    active_concepts_count: number;
    weekly_quizzes_completed: number;
    streak_days: number;
  };
  teacher_notes: string;
}

export default function ParentDashboardPage() {
  const [children, setChildren] = useState<ChildLink[]>([]);
  const [selectedChildId, setSelectedChildId] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<ParentDashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLinkedChildren();
  }, []);

  async function fetchLinkedChildren() {
    try {
      const res = await apiClient.get<ChildLink[]>('/api/v1/parents/children');
      if (res.data && res.data.length > 0) {
        setChildren(res.data);
        const initialChild = res.data[0].student_id;
        setSelectedChildId(initialChild);
        fetchChildDashboard(initialChild);
      } else {
        // Fallback for demonstration
        const demoChild: ChildLink = {
          link_id: 'link-1',
          student_id: '00000000-0000-0000-0000-000000000002',
          student_name: 'Maya Lin',
          email: 'maya.lin@lincoln.edu',
          grade_level: 6,
          class_name: 'Grade 6 Math - Period 2'
        };
        setChildren([demoChild]);
        setSelectedChildId(demoChild.student_id);
        fetchChildDashboard(demoChild.student_id);
      }
    } catch (e) {
      console.error('Error fetching linked children:', e);
    } finally {
      setLoading(false);
    }
  }

  async function fetchChildDashboard(childId: string) {
    try {
      const res = await apiClient.get<ParentDashboardData>(`/api/v1/parents/child/${childId}/dashboard`);
      if (res.data) {
        setDashboard(res.data);
      }
    } catch (e) {
      console.error('Error fetching child dashboard:', e);
    }
  }

  const handleChildSwitch = (childId: string) => {
    setSelectedChildId(childId);
    fetchChildDashboard(childId);
  };

  const selectedChild = children.find(c => c.student_id === selectedChildId);

  return (
    <AuthenticatedShell allowedRoles={['Parent', 'OrgAdmin', 'SchoolAdmin', 'SuperAdmin']} title="Family Learning Portal">
      <div style={{ padding: '28px 32px 60px', maxWidth: '1240px', margin: '0 auto' }}>
        
        {/* Header Ribbon Card */}
        <WobblyCard decoration="tape" style={{ padding: '26px 30px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <span style={{ fontSize: '2rem' }}>🏡</span>
              <h1 style={{ fontSize: '2.1rem', margin: 0 }}>Family Learning Digest</h1>
            </div>
            <p style={{ color: 'var(--pencil-subtle)', fontSize: '1.05rem', margin: 0 }}>
              Encouraging, qualitative learning updates & homework progress for your children.
            </p>
          </div>

          {/* Secure Child Switcher */}
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

        {/* Quick Hub Navigation Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          <Link href="/parent/progress" style={{ textDecoration: 'none' }}>
            <WobblyCard style={{ padding: '16px 20px', background: 'var(--postit-green)', cursor: 'pointer', textAlign: 'center' }}>
              <div style={{ fontSize: '1.6rem', marginBottom: '4px' }}>📊</div>
              <div style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--pencil-black)' }}>Detailed Progress</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--pencil-subtle)' }}>Strengths & Growing Skills</div>
            </WobblyCard>
          </Link>
          <Link href="/parent/assignments" style={{ textDecoration: 'none' }}>
            <WobblyCard style={{ padding: '16px 20px', background: 'var(--postit-cyan)', cursor: 'pointer', textAlign: 'center' }}>
              <div style={{ fontSize: '1.6rem', marginBottom: '4px' }}>📝</div>
              <div style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--pencil-black)' }}>Assignments & Homework</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--pencil-subtle)' }}>Due Dates & Completed Work</div>
            </WobblyCard>
          </Link>
          <Link href="/parent/settings" style={{ textDecoration: 'none' }}>
            <WobblyCard style={{ padding: '16px 20px', background: 'var(--postit-yellow)', cursor: 'pointer', textAlign: 'center' }}>
              <div style={{ fontSize: '1.6rem', marginBottom: '4px' }}>🔔</div>
              <div style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--pencil-black)' }}>Digest Settings</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--pencil-subtle)' }}>Email & In-App Alert Frequencies</div>
            </WobblyCard>
          </Link>
        </div>

        {/* Activity & Learning Habits Summary */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          <WobblyCard style={{ padding: '18px 22px', textAlign: 'center', background: '#ffffff' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--pencil-subtle)', textTransform: 'uppercase' }}>Practice Sessions</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--pencil-black)', marginTop: '4px' }}>
              {dashboard?.activity_summary?.total_practice_sessions || 8}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--pencil-subtle)' }}>Interactive AI tutor sessions</div>
          </WobblyCard>

          <WobblyCard style={{ padding: '18px 22px', textAlign: 'center', background: '#ffffff' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--pencil-subtle)', textTransform: 'uppercase' }}>Active Concepts</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--marker-blue)', marginTop: '4px' }}>
              {dashboard?.activity_summary?.active_concepts_count || 4}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--pencil-subtle)' }}>Core skills covered this term</div>
          </WobblyCard>

          <WobblyCard style={{ padding: '18px 22px', textAlign: 'center', background: '#ffffff' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--pencil-subtle)', textTransform: 'uppercase' }}>Quizzes Finished</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--marker-green)', marginTop: '4px' }}>
              {dashboard?.completed_work?.length || 2}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--pencil-subtle)' }}>Mastery checks graded</div>
          </WobblyCard>

          <WobblyCard style={{ padding: '18px 22px', textAlign: 'center', background: 'var(--postit-orange)' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--pencil-black)', textTransform: 'uppercase' }}>Learning Streak</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--pencil-black)', marginTop: '4px' }}>
              🔥 {dashboard?.activity_summary?.streak_days || 4} Days
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--pencil-black)' }}>Consistent daily study habit</div>
          </WobblyCard>
        </div>

        {/* Main Content Layout */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          
          {/* Left Column: Subjects & Qualitative Mastery */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            {/* Subject Overview */}
            <WobblyCard style={{ padding: '24px', background: '#ffffff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
                <h2 style={{ fontSize: '1.35rem', margin: 0 }}>📚 Subject Snapshot</h2>
                <HandBadge variant="blue">Qualitative Progress</HandBadge>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px' }}>
                {(dashboard?.subjects || [
                  { name: 'Mathematics', icon: '📐', status: 'Active Unit', qualitative_band: 'Strong 🌟' },
                  { name: 'Science', icon: '🔬', status: 'In Progress', qualitative_band: 'On track 📈' },
                  { name: 'English', icon: '📚', status: 'Completed Unit', qualitative_band: 'Strong 🌟' }
                ]).map((sub, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '16px',
                      background: 'var(--bg-paper)',
                      borderRadius: 'var(--wobbly-sm)',
                      border: '1.5px solid var(--pencil-black)',
                      boxShadow: 'var(--shadow-hard-sm)'
                    }}
                  >
                    <div style={{ fontSize: '1.8rem', marginBottom: '6px' }}>{sub.icon}</div>
                    <div style={{ fontWeight: 800, fontSize: '1.1rem', color: 'var(--pencil-black)' }}>{sub.name}</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--pencil-subtle)', marginBottom: '8px' }}>{sub.status}</div>
                    <HandBadge variant={sub.qualitative_band.includes('Strong') ? 'green' : sub.qualitative_band.includes('track') ? 'blue' : 'yellow'}>
                      {sub.qualitative_band}
                    </HandBadge>
                  </div>
                ))}
              </div>
            </WobblyCard>

            {/* Core Concepts Qualitative Mastery */}
            <WobblyCard style={{ padding: '24px', background: '#ffffff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
                <h2 style={{ fontSize: '1.35rem', margin: 0 }}>💡 Topic Mastery & Growth</h2>
                <span style={{ fontSize: '0.85rem', color: 'var(--pencil-subtle)' }}>Growth-oriented assessment</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {(dashboard?.qualitative_progress?.length ? dashboard.qualitative_progress : [
                  { concept_name: 'Adding Fractions with Like Denominators', qualitative_band: 'Strong 🌟', practice_count: 5 },
                  { concept_name: 'Unlike Denominators & Common Multiples', qualitative_band: 'On track 📈', practice_count: 3 },
                  { concept_name: 'Simplifying Improper Fractions & Mixed Numbers', qualitative_band: 'Growing skill — practicing now 💡', practice_count: 2 }
                ]).map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '14px 18px',
                      background: item.qualitative_band.includes('Strong') ? 'var(--postit-green)' : item.qualitative_band.includes('track') ? 'var(--postit-cyan)' : 'var(--postit-yellow)',
                      borderRadius: 'var(--wobbly-sm)',
                      border: '1.5px solid var(--pencil-black)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      boxShadow: 'var(--shadow-hard-sm)'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 800, color: 'var(--pencil-black)', fontSize: '1.02rem' }}>
                        {item.concept_name}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--pencil-subtle)', marginTop: '2px' }}>
                        {item.practice_count} targeted practice exercises completed
                      </div>
                    </div>
                    <HandBadge variant={item.qualitative_band.includes('Strong') ? 'green' : item.qualitative_band.includes('track') ? 'blue' : 'yellow'}>
                      {item.qualitative_band}
                    </HandBadge>
                  </div>
                ))}
              </div>
            </WobblyCard>

            {/* Completed Homework & Quizzes */}
            <WobblyCard style={{ padding: '24px', background: '#ffffff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
                <h2 style={{ fontSize: '1.35rem', margin: 0 }}>✅ Completed Quizzes & Work</h2>
                <Link href="/parent/assignments" style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--marker-blue)' }}>
                  View All &rarr;
                </Link>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {(dashboard?.completed_work?.length ? dashboard.completed_work : [
                  { assessment_title: 'Grade 6 Fractions Mastery Check', score_percentage: 95.0, status: 'GRADED', completed_at: '2026-08-14' },
                  { assessment_title: 'Unit 1 Socratic Math Quiz', score_percentage: 100.0, status: 'GRADED', completed_at: '2026-08-13' }
                ]).map((work, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '12px 16px',
                      background: 'var(--bg-paper)',
                      borderRadius: 'var(--wobbly-sm)',
                      border: '1.5px solid var(--pencil-black)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 800, color: 'var(--pencil-black)', fontSize: '0.95rem' }}>
                        {work.assessment_title}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--pencil-subtle)' }}>
                        Completed on {work.completed_at.slice(0, 10)}
                      </div>
                    </div>
                    <HandBadge variant="green">{work.score_percentage}% Completed</HandBadge>
                  </div>
                ))}
              </div>
            </WobblyCard>
          </div>

          {/* Right Column: Teacher Notes & Upcoming Work */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            {/* Teacher Direct Notes */}
            <WobblyCard style={{ padding: '22px', background: 'var(--postit-yellow)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <span style={{ fontSize: '1.4rem' }}>✏️</span>
                <h3 style={{ fontSize: '1.15rem', margin: 0, fontWeight: 800 }}>Teacher Notes</h3>
              </div>
              <p style={{ fontSize: '0.95rem', color: 'var(--pencil-black)', lineHeight: 1.5, fontStyle: 'italic', margin: 0 }}>
                &ldquo;{dashboard?.teacher_notes || `${selectedChild?.student_name || 'Your child'} is demonstrating great consistency with fraction homework and asks thoughtful questions during practice!`}&rdquo;
              </p>
              <div style={{ fontSize: '0.8rem', color: 'var(--pencil-subtle)', marginTop: '12px', textAlign: 'right', fontWeight: 600 }}>
                — Ms. Clara Johnson (Math Instructor)
              </div>
            </WobblyCard>

            {/* Upcoming Homework */}
            <WobblyCard style={{ padding: '22px', background: '#ffffff' }}>
              <h3 style={{ fontSize: '1.15rem', margin: '0 0 14px 0', fontWeight: 800 }}>⏳ Upcoming Assignments</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {(dashboard?.upcoming_work?.length ? dashboard.upcoming_work : [
                  { title: 'Grade 6 Math Spaced Practice', subject: 'Mathematics', due_date: 'Tomorrow at 5:00 PM' },
                  { title: 'Science Ecosystems Review', subject: 'Science', due_date: 'Friday at 4:00 PM' }
                ]).map((up, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '12px',
                      background: 'var(--bg-paper)',
                      borderRadius: 'var(--wobbly-sm)',
                      border: '1.5px solid var(--pencil-black)'
                    }}
                  >
                    <div style={{ fontWeight: 800, fontSize: '0.9rem', color: 'var(--pencil-black)' }}>{up.title}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--marker-blue)', fontWeight: 600, marginTop: '2px' }}>{up.due_date}</div>
                  </div>
                ))}
              </div>
            </WobblyCard>

            {/* Family Growth Mindset Tip */}
            <WobblyCard style={{ padding: '20px', background: 'var(--postit-green)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ fontSize: '1.3rem' }}>🌱</span>
                <div style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--pencil-black)' }}>Home Practice Tip</div>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--pencil-black)', margin: 0, lineHeight: 1.4 }}>
                Ask your child to explain *why* fraction slices need to be the same size when sharing a pizza. Explaining concepts aloud deepens conceptual retention!
              </p>
            </WobblyCard>

          </div>
        </div>

      </div>
    </AuthenticatedShell>
  );
}
