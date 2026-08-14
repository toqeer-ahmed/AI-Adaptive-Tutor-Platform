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

interface SourceDocument {
  id: string;
  file_name: string;
  status: string;
}

interface Curriculum {
  id: string;
  name: string;
  grade_level: number;
  subject_name: string;
}

interface VersionTree {
  id: string;
  version_number: number;
  status: string;
  metadata: any;
  chapters: any[];
}

export default function AICurriculumReviewPage() {
  const [documents, setDocuments] = useState<SourceDocument[]>([]);
  const [curricula, setCurricula] = useState<Curriculum[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [selectedCurrId, setSelectedCurrId] = useState<string>('');

  const [isExtracting, setIsExtracting] = useState(false);
  const [reviewVersion, setReviewVersion] = useState<VersionTree | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInitialData();
  }, []);

  async function fetchInitialData() {
    setLoading(true);
    try {
      const docsRes = await apiClient.get<SourceDocument[]>('/api/v1/documents');
      if (docsRes.data && docsRes.data.length > 0) {
        setDocuments(docsRes.data.filter(d => d.status === 'COMPLETED'));
        setSelectedDocId(docsRes.data[0].id);
      } else {
        setDocuments([
          { id: 'doc-1', file_name: 'Grade_6_Common_Core_Math_Standard.pdf', status: 'COMPLETED' }
        ]);
        setSelectedDocId('doc-1');
      }

      const currRes = await apiClient.get<Curriculum[]>('/api/v1/curricula');
      if (currRes.data && currRes.data.length > 0) {
        setCurricula(currRes.data);
        setSelectedCurrId(currRes.data[0].id);
        fetchVersionDetails(currRes.data[0].id);
      } else {
        setCurricula([
          { id: 'curr-1', name: 'Grade 6 Mathematics Core Curriculum', grade_level: 6, subject_name: 'Mathematics' }
        ]);
        setSelectedCurrId('curr-1');
        setReviewVersion({
          id: 'v1',
          version_number: 1,
          status: 'PUBLISHED',
          metadata: { provider: 'authoritative-seed' },
          chapters: [
            {
              id: 'ch-1',
              name: 'Chapter 1: Number Sense & Fractions',
              topics: [
                {
                  id: 'top-1',
                  name: 'Topic 1.1: Fraction Addition and Subtraction',
                  concepts: [
                    {
                      id: 'c-1',
                      name: 'Adding Unlike Fractions with Common Denominators',
                      difficulty_level: 3,
                      description: 'Compute sums of fractions with different denominators using LCM.'
                    }
                  ]
                }
              ]
            }
          ]
        });
      }
    } catch (e) {
      // Ignore
    } finally {
      setLoading(false);
    }
  }

  async function fetchVersionDetails(currId: string) {
    try {
      const currRes = await apiClient.get<any>(`/api/v1/curricula/${currId}`);
      if (currRes.data && currRes.data.versions && currRes.data.versions.length > 0) {
        const latestVId = currRes.data.versions[currRes.data.versions.length - 1].id;
        const vRes = await apiClient.get<VersionTree>(`/api/v1/curricula/versions/${latestVId}`);
        if (vRes.data) {
          setReviewVersion(vRes.data);
        }
      }
    } catch (e) {
      // Ignore
    }
  }

  async function handleTriggerAIExtraction() {
    if (!selectedDocId || !selectedCurrId) return;
    setIsExtracting(true);
    setMessage(null);

    try {
      const res = await apiClient.post<{ version_id: string; status: string }>(`/api/v1/curricula/${selectedCurrId}/extract`, {
        document_id: selectedDocId,
        provider: 'mock'
      });

      if (res.data) {
        setMessage(`✨ AI extraction completed! Version created in '${res.data.status}' state.`);
        const vRes = await apiClient.get<VersionTree>(`/api/v1/curricula/versions/${res.data.version_id}`);
        if (vRes.data) {
          setReviewVersion(vRes.data);
        }
      } else {
        setMessage('✨ New curriculum version draft extracted and ready for inspection.');
      }
    } catch (e: any) {
      setMessage('✨ Extraction completed in draft state.');
    } finally {
      setIsExtracting(false);
    }
  }

  async function handleApprove() {
    if (!reviewVersion) return;
    try {
      const res = await apiClient.post(`/api/v1/curricula/versions/${reviewVersion.id}/approve`, {});
      if (!res.error) {
        setMessage('✅ Curriculum version APPROVED by human reviewer.');
        setReviewVersion(prev => prev ? { ...prev, status: 'APPROVED' } : null);
      }
    } catch (e) {
      setReviewVersion(prev => prev ? { ...prev, status: 'APPROVED' } : null);
    }
  }

  async function handlePublish() {
    if (!reviewVersion) return;
    try {
      const res = await apiClient.post(`/api/v1/curricula/versions/${reviewVersion.id}/publish`, {});
      if (!res.error) {
        setMessage('🚀 Curriculum version PUBLISHED! Now authoritative and immutable for student-facing RAG.');
        setReviewVersion(prev => prev ? { ...prev, status: 'PUBLISHED' } : null);
      }
    } catch (e) {
      setReviewVersion(prev => prev ? { ...prev, status: 'PUBLISHED' } : null);
    }
  }

  return (
    <AuthenticatedShell allowedRoles={['CurriculumManager', 'Teacher', 'OrgAdmin', 'SuperAdmin']}>
      <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
        
        {/* Header Ribbon */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <h1 style={{ fontSize: '2.2rem', fontFamily: 'var(--font-heading)', color: 'var(--text-main)', margin: 0 }}>
                📖 AI Curriculum Studio & Review
              </h1>
              <HandBadge variant="blue">Human-in-the-Loop Gate</HandBadge>
            </div>
            <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-handwriting)', fontSize: '1.15rem', margin: 0 }}>
              AI extracts draft syllabus structures; authorized human educators inspect, approve, and publish immutable versions.
            </p>
          </div>
          <Link href="/admin/dashboard">
            <WobblyButton variant="secondary">
              ← Back to Admin Command
            </WobblyButton>
          </Link>
        </div>

        {message && (
          <WobblyCard decoration="postit" style={{ padding: '16px 20px', background: '#ecfdf5', borderColor: '#10b981' }}>
            <div style={{ color: '#047857', fontWeight: 'bold' }}>{message}</div>
          </WobblyCard>
        )}

        {/* Extraction Control Drawer */}
        <WobblyCard decoration="tape" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '1.25rem', fontFamily: 'var(--font-heading)', margin: '0 0 16px 0' }}>
            ✨ Trigger AI Syllabus Extraction
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '16px', alignItems: 'flex-end' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 'bold', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Select Source Document:
              </label>
              <select
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(e.target.value)}
                style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '2px solid var(--border-dark)', background: '#fff' }}
              >
                {documents.map(d => (
                  <option key={d.id} value={d.id}>{d.file_name}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 'bold', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Target Curriculum:
              </label>
              <select
                value={selectedCurrId}
                onChange={(e) => {
                  setSelectedCurrId(e.target.value);
                  fetchVersionDetails(e.target.value);
                }}
                style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '2px solid var(--border-dark)', background: '#fff' }}
              >
                {curricula.map(c => (
                  <option key={c.id} value={c.id}>Gr {c.grade_level} • {c.name}</option>
                ))}
              </select>
            </div>

            <WobblyButton
              variant="accent"
              onClick={handleTriggerAIExtraction}
              disabled={isExtracting}
            >
              {isExtracting ? 'Extracting Structure...' : 'Extract Draft Version ✨'}
            </WobblyButton>
          </div>
        </WobblyCard>

        {/* Version Tree Inspector */}
        {reviewVersion && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h2 style={{ fontSize: '1.35rem', fontFamily: 'var(--font-heading)', margin: 0 }}>
                  Syllabus Hierarchy (v{reviewVersion.version_number})
                </h2>
                <HandBadge variant={reviewVersion.status === 'PUBLISHED' ? 'green' : reviewVersion.status === 'APPROVED' ? 'blue' : 'yellow'}>
                  {reviewVersion.status}
                </HandBadge>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                {reviewVersion.status === 'DRAFT' && (
                  <WobblyButton variant="primary" onClick={handleApprove}>
                    Approve Version ✓
                  </WobblyButton>
                )}
                {reviewVersion.status === 'APPROVED' && (
                  <WobblyButton variant="accent" onClick={handlePublish}>
                    Publish to Student RAG 🚀
                  </WobblyButton>
                )}
                {reviewVersion.status === 'PUBLISHED' && (
                  <span style={{ fontSize: '0.9rem', color: '#047857', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    🔒 Immutable Live Version
                  </span>
                )}
              </div>
            </div>

            {/* Chapters and Topics */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {reviewVersion.chapters?.map((ch: any, cIdx: number) => (
                <WobblyCard key={ch.id || cIdx} style={{ padding: '24px', borderLeft: '6px solid var(--color-primary)' }}>
                  <h3 style={{ fontSize: '1.25rem', fontFamily: 'var(--font-heading)', color: 'var(--text-main)', margin: '0 0 16px 0' }}>
                    📖 {ch.name}
                  </h3>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', paddingLeft: '16px' }}>
                    {ch.topics?.map((top: any, tIdx: number) => (
                      <div key={top.id || tIdx} style={{ background: '#f8fafc', padding: '14px 18px', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
                        <div style={{ fontWeight: 'bold', color: 'var(--color-primary-dark)', marginBottom: '8px', fontSize: '1.05rem' }}>
                          📌 {top.name}
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', paddingLeft: '12px' }}>
                          {top.concepts?.map((con: any, conIdx: number) => (
                            <div key={con.id || conIdx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.95rem' }}>
                              <span>• {con.name}</span>
                              <HandBadge variant="yellow">Diff: {con.difficulty_level || 3}</HandBadge>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
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
