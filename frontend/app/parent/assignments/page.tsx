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

interface PendingAssignment {
  id: string;
  title: string;
  subject: string;
  due_date: string;
  estimated_time: string;
  status: string;
}

interface CompletedAssignment {
  id: string;
  title: string;
  subject: string;
  score_display: string;
  status: string;
  submitted_at: string;
  teacher_feedback: string;
}

interface AssignmentsData {
  child_id: string;
  child_name: string;
  pending_assignments: PendingAssignment[];
  completed_assignments: CompletedAssignment[];
}

export default function ParentAssignmentsPage() {
  const [children, setChildren] = useState<ChildLink[]>([]);
  const [selectedChildId, setSelectedChildId] = useState<string | null>(null);
  const [assignments, setAssignments] = useState<AssignmentsData | null>(null);
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
        fetchAssignments(res.data[0].student_id);
      } else {
        const demoChild: ChildLink = {
          link_id: 'link-1',
          student_id: '00000000-0000-0000-0000-000000000002',
          student_name: 'Maya Lin',
          grade_level: 6
        };
        setChildren([demoChild]);
        setSelectedChildId(demoChild.student_id);
        fetchAssignments(demoChild.student_id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function fetchAssignments(childId: string) {
    try {
      const res = await apiClient.get<AssignmentsData>(`/api/v1/parents/child/${childId}/assignments`);
      if (res.data) {
        setAssignments(res.data);
      }
    } catch (e) {
      console.error(e);
    }
  }

  const handleChildSwitch = (childId: string) => {
    setSelectedChildId(childId);
    fetchAssignments(childId);
  };

  const selectedChild = children.find(c => c.student_id === selectedChildId);

  return (
    <AuthenticatedShell allowedRoles={['Parent', 'OrgAdmin', 'SchoolAdmin', 'SuperAdmin']} title="Homework & Assignments Tracker">
      <div style={{ padding: '28px 32px 60px', maxWidth: '1240px', margin: '0 auto' }}>
        
        {/* Header Card */}
        <WobblyCard decoration="tape" style={{ padding: '26px 30px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <span style={{ fontSize: '2rem' }}>📝</span>
              <h1 style={{ fontSize: '2.1rem', margin: 0 }}>Assignments & Completed Work</h1>
            </div>
            <p style={{ color: 'var(--pencil-subtle)', fontSize: '1.05rem', margin: 0 }}>
              Track due dates, completed quizzes, and educator feedback for {selectedChild?.student_name || 'your child'}.
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

        {/* Pending & Upcoming Work */}
        <WobblyCard style={{ padding: '24px', marginBottom: '24px', background: '#ffffff' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <span style={{ fontSize: '1.5rem' }}>⏳</span>
            <h2 style={{ fontSize: '1.3rem', margin: 0 }}>Pending & Upcoming Assignments</h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {(assignments?.pending_assignments || [
              {
                id: '1',
                title: 'Fractions Unit 1 Mastery Check',
                subject: 'Mathematics',
                due_date: 'Tomorrow by 5:00 PM',
                estimated_time: '15 mins',
                status: 'Assigned by Teacher'
              },
              {
                id: '2',
                title: 'Ecosystem Food Webs Worksheet',
                subject: 'Science',
                due_date: 'Friday by 4:00 PM',
                estimated_time: '20 mins',
                status: 'Assigned by Teacher'
              }
            ]).map((p) => (
              <div
                key={p.id}
                style={{
                  padding: '16px 20px',
                  background: 'var(--postit-yellow)',
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
                  <div style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--pencil-black)' }}>{p.title}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--pencil-black)', marginTop: '2px' }}>
                    Subject: <strong>{p.subject}</strong> &bull; Est. Time: {p.estimated_time}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--marker-red)' }}>📅 {p.due_date}</span>
                  <HandBadge variant="yellow">{p.status}</HandBadge>
                </div>
              </div>
            ))}
          </div>
        </WobblyCard>

        {/* Completed Quizzes with Teacher Feedback */}
        <WobblyCard style={{ padding: '24px', background: '#ffffff' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <span style={{ fontSize: '1.5rem' }}>✅</span>
            <h2 style={{ fontSize: '1.3rem', margin: 0 }}>Completed Work & Teacher Feedback</h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {(assignments?.completed_assignments || [
              {
                id: 'c1',
                title: 'Grade 6 Fractions Practice Quiz #1',
                subject: 'Mathematics',
                score_display: '95%',
                status: 'Completed & Graded',
                submitted_at: 'August 14, 2026',
                teacher_feedback: 'Outstanding reasoning on the word problem slice comparison!'
              },
              {
                id: 'c2',
                title: 'Socratic Unit 1 Concept Check',
                subject: 'Mathematics',
                score_display: '100%',
                status: 'Completed & Graded',
                submitted_at: 'August 13, 2026',
                teacher_feedback: 'Clear mastery of like-denominator additions.'
              }
            ]).map((c) => (
              <div
                key={c.id}
                style={{
                  padding: '18px 20px',
                  background: 'var(--bg-paper)',
                  borderRadius: 'var(--wobbly-sm)',
                  border: '1.5px solid var(--pencil-black)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                  <div>
                    <div style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--pencil-black)' }}>{c.title}</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--pencil-subtle)' }}>
                      {c.subject} &bull; Submitted on {c.submitted_at}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <HandBadge variant="green">{c.score_display} Completed</HandBadge>
                  </div>
                </div>

                {c.teacher_feedback && (
                  <div
                    style={{
                      padding: '10px 14px',
                      background: 'var(--postit-green)',
                      borderRadius: 'var(--wobbly-sm)',
                      border: '1px solid var(--pencil-black)',
                      fontSize: '0.9rem',
                      color: 'var(--pencil-black)',
                      marginTop: '4px'
                    }}
                  >
                    <strong>Teacher Feedback:</strong> &ldquo;{c.teacher_feedback}&rdquo;
                  </div>
                )}
              </div>
            ))}
          </div>
        </WobblyCard>

      </div>
    </AuthenticatedShell>
  );
}
