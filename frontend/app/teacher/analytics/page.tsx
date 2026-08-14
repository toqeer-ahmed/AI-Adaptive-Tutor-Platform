'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import AuthenticatedShell from '@/components/AuthenticatedShell';
import { apiClient } from '@/lib/api-client';
import {
  WobblyCard,
  WobblyButton,
  HandBadge,
  ScribbleUnderline
} from '@/lib/HandDrawnComponents';

export default function TeacherAnalyticsPage() {
  const [copilotQuery, setCopilotQuery] = useState('');
  const [copilotChat, setCopilotChat] = useState<Array<{ sender: 'teacher' | 'copilot'; text: string }>>([
    {
      sender: 'copilot',
      text: "Hello Teacher! 🍎 I'm your AI Instructional Co-Pilot. I've analyzed your Period 2 Mathematics class. 8 students are currently confusing unlike denominators by adding numerators directly. Would you like me to draft a 15-minute small-group visual fraction bar activity?"
    }
  ]);
  const [isCopilotLoading, setIsCopilotLoading] = useState(false);

  async function handleSendCopilot(e: React.FormEvent) {
    e.preventDefault();
    if (!copilotQuery.trim() || isCopilotLoading) return;

    const query = copilotQuery;
    setCopilotChat(prev => [...prev, { sender: 'teacher', text: query }]);
    setCopilotQuery('');
    setIsCopilotLoading(true);

    try {
      // Execute turn through model router or demo response
      setTimeout(() => {
        setCopilotChat(prev => [
          ...prev,
          {
            sender: 'copilot',
            text: "💡 Remediation Proposal:\n1. Open with a tactile analogy: Cut a chocolate bar into 3 pieces, and another into 6 pieces. Ask students if 1 third-piece equals 2 sixth-pieces.\n2. Guided Practice: Solve 1/4 + 1/8 using fraction bars before writing numbers.\n3. Independent Check: Assign Question #q-101 from your Question Bank."
          }
        ]);
        setIsCopilotLoading(false);
      }, 700);
    } catch (e) {
      setIsCopilotLoading(false);
    }
  }

  return (
    <AuthenticatedShell allowedRoles={['Teacher', 'OrgAdmin', 'SchoolAdmin', 'SuperAdmin']} title="Class Analytics & AI Co-Pilot">
      <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
        
        {/* Header Ribbon */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <h1 style={{ fontSize: '2.2rem', fontFamily: 'var(--font-heading)', color: 'var(--text-main)', margin: 0 }}>
                📊 Class Analytics &amp; AI Instructional Co-Pilot
              </h1>
              <HandBadge variant="purple">Deterministic Provenance</HandBadge>
            </div>
            <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-handwriting)', fontSize: '1.15rem', margin: 0 }}>
              Period 2 (Section A) • Grade 6 Mathematics • 24 Enrolled Students
            </p>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <Link href="/teacher/dashboard">
              <WobblyButton variant="secondary">
                ← Dashboard
              </WobblyButton>
            </Link>
            <Link href="/teacher/classes">
              <WobblyButton variant="secondary">
                View Rosters 👥
              </WobblyButton>
            </Link>
          </div>
        </div>

        {/* Top 3 KPI Post-Its */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '18px' }}>
          <WobblyCard decoration="tape" style={{ padding: '20px', background: '#ecfdf5', border: '2px solid #10b981' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 'bold', color: '#047857', marginBottom: '4px' }}>
              CLASS MASTERY BAND
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#065f46', fontFamily: 'var(--font-heading)' }}>
              On Track 📈
            </div>
            <div style={{ fontSize: '0.88rem', color: '#047857', marginTop: '6px' }}>
              14 Strong, 6 On Track, 4 Getting There
            </div>
          </WobblyCard>

          <WobblyCard decoration="tape" style={{ padding: '20px', background: '#fffbeb', border: '2px solid #f59e0b' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 'bold', color: '#b45309', marginBottom: '4px' }}>
              ACTIVE MISCONCEPTION ALERT
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#92400e', fontFamily: 'var(--font-heading)' }}>
              33% of Class ⚠️
            </div>
            <div style={{ fontSize: '0.88rem', color: '#b45309', marginTop: '6px' }}>
              Adding denominators directly (1/3+1/6 = 2/9)
            </div>
          </WobblyCard>

          <WobblyCard decoration="tape" style={{ padding: '20px', background: '#eff6ff', border: '2px solid #3b82f6' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 'bold', color: '#1d4ed8', marginBottom: '4px' }}>
              ASSIGNMENT COMPLETION
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#1e40af', fontFamily: 'var(--font-heading)' }}>
              92% Submitted
            </div>
            <div style={{ fontSize: '0.88rem', color: '#1d4ed8', marginTop: '6px' }}>
              22 of 24 students completed Unit 1 Quiz
            </div>
          </WobblyCard>
        </div>

        {/* Main Grid: Concept Mastery Heatmap + AI Instructional Co-Pilot */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: '24px', alignItems: 'start' }}>
          
          {/* Left Column: Topic Mastery Heatmap & Misconception Breakdown */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            
            {/* Concept Mastery Heatmap */}
            <WobblyCard decoration="tack-blue" style={{ padding: '24px', background: '#fff' }}>
              <h3 style={{ fontSize: '1.3rem', fontFamily: 'var(--font-heading)', margin: '0 0 16px 0' }}>
                🗺️ Concept Mastery Heatmap — Unit 1 Fractions
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {[
                  { name: '1. Understanding Unit Fractions', score: 0.94, band: 'Strong 🌟', color: '#10b981' },
                  { name: '2. Equivalent Fractions on Number Line', score: 0.88, band: 'Strong 🌟', color: '#10b981' },
                  { name: '3. Adding Unlike Fractions (LCM)', score: 0.62, band: 'Getting There 💡', color: '#f59e0b' },
                  { name: '4. Mixed Numbers Regrouping', score: 0.74, band: 'On Track 📈', color: '#3b82f6' }
                ].map((c, idx) => (
                  <div key={idx} style={{ borderBottom: '1px solid var(--border-light)', paddingBottom: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 'bold', fontSize: '0.95rem' }}>{c.name}</span>
                      <HandBadge variant={c.band.includes('Strong') ? 'green' : c.band.includes('On Track') ? 'blue' : 'yellow'}>
                        {c.band}
                      </HandBadge>
                    </div>
                    <div style={{ height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{ width: `${c.score * 100}%`, height: '100%', background: c.color, borderRadius: '4px' }} />
                    </div>
                  </div>
                ))}
              </div>
            </WobblyCard>

            {/* Root-Cause Misconceptions Breakdown */}
            <WobblyCard style={{ padding: '24px', background: '#fff' }}>
              <h3 style={{ fontSize: '1.3rem', fontFamily: 'var(--font-heading)', margin: '0 0 12px 0' }}>
                🧬 Detected Misconceptions &amp; Root Causes
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ background: '#fffbeb', border: '1.5px solid #f59e0b', borderRadius: '8px', padding: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 'bold', color: '#b45309' }}>ADD_DENOMINATORS_DIRECTLY (8 Students)</span>
                    <HandBadge variant="yellow">High Prevalence</HandBadge>
                  </div>
                  <p style={{ fontSize: '0.88rem', color: '#92400e', margin: '0 0 6px 0' }}>
                    Students treat numerators and denominators as independent whole numbers (e.g. 1/3 + 1/6 = 2/9).
                  </p>
                  <div style={{ fontSize: '0.82rem', color: '#78350f', fontWeight: 'bold' }}>
                    Recommended Action: Tactile fraction tiles or pizza slice visual demonstration.
                  </div>
                </div>

                <div style={{ background: '#f8fafc', border: '1px solid var(--border-light)', borderRadius: '8px', padding: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 'bold' }}>LONGER_DECIMAL_IS_LARGER (2 Students)</span>
                    <HandBadge variant="blue">Low Prevalence</HandBadge>
                  </div>
                  <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', margin: 0 }}>
                    Students assume 0.125 > 0.5 because 125 has more digits.
                  </p>
                </div>
              </div>
            </WobblyCard>

          </div>

          {/* Right Column: Teacher AI Instructional Co-Pilot */}
          <WobblyCard decoration="tack-red" style={{ padding: '24px', background: '#fff', position: 'sticky', top: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.6rem' }}>🤖</span>
                <h3 style={{ fontSize: '1.25rem', fontFamily: 'var(--font-heading)', margin: 0 }}>
                  Teacher AI Co-Pilot
                </h3>
              </div>
              <HandBadge variant="purple">Assistant Only</HandBadge>
            </div>

            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', margin: '0 0 14px 0' }}>
              Ask your instructional co-pilot to draft lesson plans, generate targeted review activities, or summarize student misconceptions.
            </p>

            {/* Chat Thread */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
              maxHeight: '380px',
              overflowY: 'auto',
              paddingRight: '4px',
              marginBottom: '14px'
            }}>
              {copilotChat.map((m, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '12px 14px',
                    borderRadius: '10px',
                    fontSize: '0.92rem',
                    lineHeight: 1.45,
                    alignSelf: m.sender === 'teacher' ? 'flex-end' : 'flex-start',
                    background: m.sender === 'teacher' ? '#eef2ff' : '#f8fafc',
                    border: m.sender === 'teacher' ? '1px solid #c7d2fe' : '1px solid var(--border-light)',
                    maxWidth: '92%',
                    whiteSpace: 'pre-wrap'
                  }}
                >
                  <div style={{ fontSize: '0.72rem', fontWeight: 'bold', color: 'var(--text-muted)', marginBottom: '2px' }}>
                    {m.sender === 'teacher' ? 'You (Teacher)' : 'AI Instructional Co-Pilot'}
                  </div>
                  {m.text}
                </div>
              ))}
              {isCopilotLoading && (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                  AI Co-Pilot is analyzing class data... ⏳
                </div>
              )}
            </div>

            {/* Query Form */}
            <form onSubmit={handleSendCopilot} style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                placeholder="Ask Co-Pilot (e.g. Draft 10-min small group activity)..."
                value={copilotQuery}
                onChange={(e) => setCopilotQuery(e.target.value)}
                style={{
                  flex: 1,
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1.5px solid var(--border-dark)',
                  fontSize: '0.9rem'
                }}
              />
              <button
                type="submit"
                disabled={isCopilotLoading || !copilotQuery.trim()}
                style={{
                  padding: '10px 14px',
                  background: 'var(--color-primary)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 'bold',
                  cursor: isCopilotLoading ? 'not-allowed' : 'pointer'
                }}
              >
                Send 🚀
              </button>
            </form>
          </WobblyCard>

        </div>

      </div>
    </AuthenticatedShell>
  );
}
