'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';

interface QualitativeConcept {
  id: string;
  concept_id: string;
  qualitative_band: string;
  status: string;
  attempt_count: number;
  next_review_due_at: string | null;
}

export default function StudentDashboardPage() {
  const [concepts, setConcepts] = useState<QualitativeConcept[]>([]);
  const [adaptiveRec, setAdaptiveRec] = useState<string>('REINFORCE: Practice adding fractions with common denominators.');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStudentDashboardData();
  }, []);

  async function fetchStudentDashboardData() {
    const meRes = await apiClient.get<any>('/api/v1/auth/me');
    if (meRes.data) {
      const masteryRes = await apiClient.get<QualitativeConcept[]>(`/api/v1/mastery/student/${meRes.data.id}`);
      if (masteryRes.data) {
        setConcepts(masteryRes.data);
      }

      const recRes = await apiClient.post<any>('/api/v1/adaptive/recommend', {
        concept_id: '00000000-0000-0000-0000-000000000004',
        curriculum_version_id: '00000000-0000-0000-0000-000000000001'
      });
      if (recRes.data) {
        setAdaptiveRec(`${recRes.data.decision}: ${recRes.data.reasoning}`);
      }
    }
    setLoading(false);
  }

  return (
    <div style={{ padding: '32px', maxWidth: '1100px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      {/* Welcome Banner */}
      <header style={{
        background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
        borderRadius: '16px',
        padding: '32px',
        marginBottom: '32px',
        boxShadow: '0 10px 25px -5px rgba(79, 70, 229, 0.4)'
      }}>
        <h1 style={{ fontSize: '2.2rem', marginBottom: '8px', fontWeight: 'bold' }}>
          👋 Welcome Back, Alex!
        </h1>
        <p style={{ fontSize: '1.1rem', opacity: 0.9 }}>
          Grade 6 Mathematics • Multi-Tenant Adaptive Tutor Platform
        </p>
      </header>

      {/* Grid Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Left Column: Continue Learning & Assigned Work */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Continue Learning */}
          <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.3rem', color: '#38bdf8' }}>🚀 Continue Learning</h2>
              <span style={{ fontSize: '0.8rem', padding: '4px 10px', background: '#0284c7', borderRadius: '12px', fontWeight: 'bold' }}>Active Objective</span>
            </div>

            <div style={{ padding: '20px', background: '#0f172a', borderRadius: '10px', marginBottom: '16px', borderLeft: '4px solid #38bdf8' }}>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '4px' }}>Adding Fractions with Unlike Denominators</h3>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '12px' }}>
                Curriculum Standard: Grade 6 • Math • Chapter 3 Fractions
              </p>
              <div style={{ fontSize: '0.9rem', color: '#fbbf24', background: '#1e1b4b', padding: '10px', borderRadius: '6px' }}>
                💡 Recommendation: {adaptiveRec}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <Link href="/student/adaptive" style={{ textDecoration: 'none' }}>
                <button style={{ padding: '12px 20px', backgroundColor: '#6366f1', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>
                  🎯 Start Adaptive Session
                </button>
              </Link>
              <Link href="/student/tutor" style={{ textDecoration: 'none' }}>
                <button style={{ padding: '12px 20px', backgroundColor: '#334155', color: '#f8fafc', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>
                  🤖 Ask AI Instructor
                </button>
              </Link>
            </div>
          </section>

          {/* Assigned Work & Upcoming Assessments */}
          <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
            <h2 style={{ fontSize: '1.3rem', color: '#a855f7', marginBottom: '16px' }}>📌 Assigned Work & Quizzes</h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ padding: '16px', background: '#0f172a', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 'bold', color: '#f8fafc' }}>Fractions & Decimals Diagnostic Quiz</div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Due: Tomorrow at 5:00 PM • 10 Questions</div>
                </div>
                <Link href="/student/assessments" style={{ textDecoration: 'none' }}>
                  <button style={{ padding: '8px 16px', backgroundColor: '#10b981', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}>
                    Start Quiz
                  </button>
                </Link>
              </div>

              <div style={{ padding: '16px', background: '#0f172a', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 'bold', color: '#f8fafc' }}>Spaced Review Practice Activity</div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Due: In 3 days • Spaced Repetition</div>
                </div>
                <Link href="/student/adaptive" style={{ textDecoration: 'none' }}>
                  <button style={{ padding: '8px 16px', backgroundColor: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}>
                    Practice
                  </button>
                </Link>
              </div>
            </div>
          </section>
        </div>

        {/* Right Column: Qualitative Progress & Misconception Badges */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Qualitative Progress */}
          <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
            <h2 style={{ fontSize: '1.2rem', color: '#34d399', marginBottom: '16px' }}>📊 Your Learning Progress</h2>

            {loading ? (
              <p style={{ color: '#94a3b8' }}>Loading progress...</p>
            ) : concepts.length === 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ padding: '14px', background: '#0f172a', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>Adding Fractions</div>
                  <div style={{ fontSize: '0.85rem', color: '#34d399', fontWeight: 'bold', marginTop: '4px' }}>On track 📈</div>
                </div>

                <div style={{ padding: '14px', background: '#0f172a', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>Common Denominator</div>
                  <div style={{ fontSize: '0.85rem', color: '#a7f3d0', fontWeight: 'bold', marginTop: '4px' }}>Strong 🌟</div>
                </div>

                <div style={{ padding: '14px', background: '#0f172a', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>Simplifying Fractions</div>
                  <div style={{ fontSize: '0.85rem', color: '#fbbf24', fontWeight: 'bold', marginTop: '4px' }}>Getting there 💡</div>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {concepts.map((c) => (
                  <div key={c.id} style={{ padding: '14px', background: '#0f172a', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>Concept Item</div>
                    <div style={{ fontSize: '0.85rem', color: '#34d399', fontWeight: 'bold', marginTop: '4px' }}>
                      {c.qualitative_band}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Quick Nav Shortcuts */}
          <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
            <h2 style={{ fontSize: '1.2rem', color: '#f43f5e', marginBottom: '12px' }}>🔍 Quick Tools</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Link href="/student/rag" style={{ textDecoration: 'none', color: '#38bdf8', fontSize: '0.9rem' }}>
                🔍 Curriculum RAG Search
              </Link>
              <Link href="/student/misconceptions" style={{ textDecoration: 'none', color: '#fbbf24', fontSize: '0.9rem' }}>
                💡 Misconception Remediation
              </Link>
              <Link href="/student/tutor" style={{ textDecoration: 'none', color: '#a78bfa', fontSize: '0.9rem' }}>
                💬 Chat with AI Instructor
              </Link>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
