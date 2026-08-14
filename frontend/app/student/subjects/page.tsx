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

interface SubjectTopic {
  id: string;
  name: string;
  status: 'COMPLETED' | 'IN_PROGRESS' | 'RECOMMENDED' | 'LOCKED';
  concept_count: number;
  description: string;
}

interface SubjectChapter {
  id: string;
  name: string;
  topics: SubjectTopic[];
}

interface Subject {
  id: string;
  title: string;
  icon: string;
  grade: number;
  description: string;
  progress_status: string;
  chapters: SubjectChapter[];
}

export default function StudentSubjectsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('math-gr6');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCurriculumSubjects();
  }, []);

  async function fetchCurriculumSubjects() {
    setLoading(true);
    const defaultCatalog: Subject[] = [
      {
        id: 'math-gr6',
        title: 'Grade 6 Mathematics',
        icon: '📐',
        grade: 6,
        description: 'Master fraction arithmetic, decimal operations, proportional reasoning, and introductory algebraic expressions.',
        progress_status: 'On Track 📈',
        chapters: [
          {
            id: 'math-ch1',
            name: 'Unit 1: Rational Numbers & Fractions',
            topics: [
              {
                id: 'top-frac-add',
                name: 'Adding Unlike Fractions (LCM)',
                status: 'RECOMMENDED',
                concept_count: 3,
                description: 'Convert fractions to equivalent denominators before computing sums.'
              },
              {
                id: 'top-frac-mult',
                name: 'Multiplying Fractions by Whole Numbers',
                status: 'IN_PROGRESS',
                concept_count: 4,
                description: 'Repeated addition and area models for fraction multiplication.'
              },
              {
                id: 'top-dec-ops',
                name: 'Decimal Place Value Operations',
                status: 'LOCKED',
                concept_count: 3,
                description: 'Aligning decimals and computing multi-digit addition and subtraction.'
              }
            ]
          },
          {
            id: 'math-ch2',
            name: 'Unit 2: Expressions & Equations',
            topics: [
              {
                id: 'top-alg-var',
                name: 'Variables and Algebraic Expressions',
                status: 'LOCKED',
                concept_count: 4,
                description: 'Representing unknown values with variables like x and y.'
              }
            ]
          }
        ]
      },
      {
        id: 'sci-gr6',
        title: 'Grade 6 Life Science',
        icon: '🔬',
        grade: 6,
        description: 'Explore cell structures, photosynthesis, food webs, ecosystem balance, and environmental adaptations.',
        progress_status: 'Strong 🌟',
        chapters: [
          {
            id: 'sci-ch1',
            name: 'Unit 1: Cell Biology & Energy',
            topics: [
              {
                id: 'top-cells',
                name: 'Plant vs Animal Cell Organelles',
                status: 'COMPLETED',
                concept_count: 4,
                description: 'Identify the nucleus, cell wall, chloroplasts, and cell membrane.'
              },
              {
                id: 'top-photo',
                name: 'Photosynthesis & Respiration Cycles',
                status: 'RECOMMENDED',
                concept_count: 3,
                description: 'Understand how chloroplasts transform sunlight into glucose energy.'
              }
            ]
          }
        ]
      },
      {
        id: 'eng-gr6',
        title: 'Grade 6 English Language Arts',
        icon: '📚',
        grade: 6,
        description: 'Develop strong reading comprehension, literary analysis, evidence-based argument writing, and vocabulary mastery.',
        progress_status: 'On Track 📈',
        chapters: [
          {
            id: 'eng-ch1',
            name: 'Unit 1: Informational Text & Evidence',
            topics: [
              {
                id: 'top-cite',
                name: 'Citing Textual Evidence in Non-Fiction',
                status: 'IN_PROGRESS',
                concept_count: 3,
                description: 'Quoting and paraphrasing facts from articles to support central claims.'
              }
            ]
          }
        ]
      },
      {
        id: 'cs-gr6',
        title: 'Grade 6 Computer Science',
        icon: '💻',
        grade: 6,
        description: 'Learn computational problem-solving, algorithms, loops, conditionals, and block-based programming concepts.',
        progress_status: 'Getting There 💡',
        chapters: [
          {
            id: 'cs-ch1',
            name: 'Unit 1: Algorithms & Sequencing',
            topics: [
              {
                id: 'top-algo',
                name: 'Step-by-Step Algorithm Design',
                status: 'RECOMMENDED',
                concept_count: 2,
                description: 'Deconstruct everyday tasks into precise logical instruction sequences.'
              }
            ]
          }
        ]
      }
    ];

    try {
      const res = await apiClient.get<any[]>('/api/v1/curricula');
      if (res.data && res.data.length > 0) {
        // If backend has custom chapters for math, enhance the math catalog item
        const backendMath = res.data.find((c: any) => c.name.toLowerCase().includes('math'));
        if (backendMath && backendMath.versions && backendMath.versions[0]?.chapters?.length > 0) {
          defaultCatalog[0].chapters = backendMath.versions[0].chapters;
        }
      }
    } catch (e) {
      // Keep default rich catalog
    } finally {
      setSubjects(defaultCatalog);
      setSelectedSubjectId('math-gr6');
      setLoading(false);
    }
  }

  const activeSubject = subjects.find(s => s.id === selectedSubjectId) || subjects[0];

  function getStatusBadge(status: string) {
    switch (status) {
      case 'COMPLETED': return <HandBadge variant="green">COMPLETED 🌟</HandBadge>;
      case 'RECOMMENDED': return <HandBadge variant="yellow">RECOMMENDED 🚀</HandBadge>;
      case 'IN_PROGRESS': return <HandBadge variant="blue">IN PROGRESS 📈</HandBadge>;
      case 'LOCKED': return <HandBadge variant="purple">LOCKED 🔒</HandBadge>;
      default: return <HandBadge variant="yellow">{status}</HandBadge>;
    }
  }

  return (
    <AuthenticatedShell allowedRoles={['Student', 'OrgAdmin', 'SchoolAdmin', 'SuperAdmin']} title="My Subjects">
      <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
        
        {/* Header Ribbon */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <h1 style={{ fontSize: '2.2rem', fontFamily: 'var(--font-heading)', color: 'var(--text-main)', margin: 0 }}>
                📚 My Subjects & Curriculum Units
              </h1>
              <HandBadge variant="yellow">Grade 6 Standard</HandBadge>
            </div>
            <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-handwriting)', fontSize: '1.15rem', margin: 0 }}>
              Explore standards-aligned units, interactive lessons, and practice activities prescribed by your teachers.
            </p>
          </div>
          <Link href="/student/dashboard">
            <WobblyButton variant="secondary">
              ← Back to Study Desk
            </WobblyButton>
          </Link>
        </div>

        {/* Subject Selector Tabs */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
          {subjects.map((sub) => {
            const isSelected = sub.id === selectedSubjectId;
            return (
              <WobblyCard
                key={sub.id}
                decoration={isSelected ? 'tape' : 'none'}
                style={{
                  padding: '20px',
                  cursor: 'pointer',
                  border: isSelected ? '3px solid var(--color-primary)' : '2px solid var(--border-dark)',
                  background: isSelected ? '#ffffff' : '#fdfcf9',
                  transform: isSelected ? 'scale(1.02)' : 'scale(1)',
                  transition: 'all 0.2s ease'
                }}
                onClick={() => setSelectedSubjectId(sub.id)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                  <span style={{ fontSize: '2.2rem' }}>{sub.icon}</span>
                  <HandBadge variant={sub.progress_status.includes('Strong') ? 'green' : 'blue'}>
                    {sub.progress_status}
                  </HandBadge>
                </div>
                <h3 style={{ fontSize: '1.25rem', fontFamily: 'var(--font-heading)', margin: '0 0 6px 0', color: 'var(--text-main)' }}>
                  {sub.title}
                </h3>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>
                  {sub.description.slice(0, 75)}...
                </p>
              </WobblyCard>
            );
          })}
        </div>

        {/* Selected Subject Detail & Chapter Accordion */}
        {activeSubject && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <WobblyCard decoration="tack-blue" style={{ padding: '28px', background: '#fff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '2.4rem' }}>{activeSubject.icon}</span>
                  <div>
                    <h2 style={{ fontSize: '1.6rem', fontFamily: 'var(--font-heading)', margin: 0, color: 'var(--text-main)' }}>
                      {activeSubject.title}
                    </h2>
                    <span style={{ fontSize: '0.95rem', color: 'var(--text-muted)' }}>
                      Curriculum Version 1.0 • Oakridge Middle School
                    </span>
                  </div>
                </div>
                <Link href="/student/lesson">
                  <WobblyButton variant="primary">
                    Launch Next Lesson 🚀
                  </WobblyButton>
                </Link>
              </div>
              <p style={{ color: 'var(--text-main)', fontSize: '1.05rem', lineHeight: 1.5, margin: 0 }}>
                {activeSubject.description}
              </p>
            </WobblyCard>

            {/* Chapters and Topics */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {activeSubject.chapters?.map((ch, cIdx) => (
                <WobblyCard key={ch.id || cIdx} style={{ padding: '24px', borderLeft: '6px solid var(--color-primary)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 style={{ fontSize: '1.3rem', fontFamily: 'var(--font-heading)', margin: 0, color: 'var(--text-main)' }}>
                      📖 {ch.name}
                    </h3>
                    <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
                      {ch.topics.length} Learning Topics
                    </span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {ch.topics.map((top) => {
                      const isLocked = top.status === 'LOCKED';
                      return (
                        <div
                          key={top.id}
                          style={{
                            background: isLocked ? '#f8fafc' : '#ffffff',
                            border: '1.5px solid var(--border-light)',
                            borderRadius: '12px',
                            padding: '16px 20px',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            flexWrap: 'wrap',
                            gap: '12px',
                            opacity: isLocked ? 0.7 : 1
                          }}
                        >
                          <div style={{ maxWidth: '650px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                              <h4 style={{ fontSize: '1.1rem', fontFamily: 'var(--font-heading)', margin: 0, color: 'var(--text-main)' }}>
                                {top.name}
                              </h4>
                              {getStatusBadge(top.status)}
                            </div>
                            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>
                              {top.description}
                            </p>
                          </div>

                          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                            {!isLocked ? (
                              <>
                                <Link href={`/student/lesson?topic=${top.id}`}>
                                  <WobblyButton variant="primary">
                                    Start Lesson 📖
                                  </WobblyButton>
                                </Link>
                                <Link href="/student/assessments">
                                  <WobblyButton variant="secondary">
                                    Practice ✏️
                                  </WobblyButton>
                                </Link>
                              </>
                            ) : (
                              <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                🔒 Complete Unit 1 to unlock
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </WobblyCard>
              ))}
            </div>
          </div>
        )}

      </div>
    </AuthenticatedShell>
  );
}
