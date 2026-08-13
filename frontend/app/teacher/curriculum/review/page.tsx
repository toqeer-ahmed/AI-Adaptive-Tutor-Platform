'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

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

  useEffect(() => {
    fetchInitialData();
  }, []);

  async function fetchInitialData() {
    const docsRes = await apiClient.get<SourceDocument[]>('/api/v1/documents');
    if (docsRes.data) {
      setDocuments(docsRes.data.filter(d => d.status === 'COMPLETED'));
      if (docsRes.data.length > 0) setSelectedDocId(docsRes.data[0].id);
    }

    const currRes = await apiClient.get<Curriculum[]>('/api/v1/curricula');
    if (currRes.data) {
      setCurricula(currRes.data);
      if (currRes.data.length > 0) setSelectedCurrId(currRes.data[0].id);
    }
  }

  async function handleTriggerAIExtraction() {
    if (!selectedDocId || !selectedCurrId) return;
    setIsExtracting(true);
    setMessage(null);

    const res = await apiClient.post<{ version_id: string; status: string }>(`/api/v1/curricula/${selectedCurrId}/extract`, {
      document_id: selectedDocId,
      provider: 'mock'
    });

    setIsExtracting(false);

    if (res.error) {
      setMessage(`AI Extraction Error: ${res.error.message}`);
    } else if (res.data) {
      setMessage(`AI Extraction finished! Proposed version created in status '${res.data.status}'.`);
      loadVersionForReview(res.data.version_id);
    }
  }

  async function loadVersionForReview(versionId: string) {
    const res = await apiClient.get<VersionTree>(`/api/v1/curricula/versions/${versionId}`);
    if (res.data) {
      setReviewVersion(res.data);
    }
  }

  async function handleNodeAction(action: string, nodeType: string, nodeId: string, payload: any = {}) {
    if (!reviewVersion) return;
    const res = await apiClient.post(`/api/v1/curricula/versions/${reviewVersion.id}/nodes/batch`, {
      action,
      target_node_type: nodeType,
      node_id: nodeId,
      payload
    });
    if (res.error) {
      setMessage(`Node Action Error: ${res.error.message}`);
    } else {
      setMessage(`Action '${action}' applied to ${nodeType}.`);
      loadVersionForReview(reviewVersion.id);
    }
  }

  async function handleApproveAndPublish() {
    if (!reviewVersion) return;
    // Step 1: Approve
    const appRes = await apiClient.post(`/api/v1/curricula/versions/${reviewVersion.id}/status`, { status: 'APPROVED' });
    if (appRes.error) {
      setMessage(`Approval Error: ${appRes.error.message}`);
      return;
    }
    // Step 2: Publish
    const pubRes = await apiClient.post(`/api/v1/curricula/versions/${reviewVersion.id}/status`, { status: 'PUBLISHED' });
    if (pubRes.error) {
      setMessage(`Publish Error: ${pubRes.error.message}`);
    } else {
      setMessage('Curriculum Version approved by human reviewer and published as Authoritative!');
      loadVersionForReview(reviewVersion.id);
    }
  }

  return (
    <div style={{ padding: '32px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '2rem', color: '#818cf8', marginBottom: '8px' }}>
          AI Curriculum Extraction & Human Review Inspector
        </h1>
        <p style={{ color: '#94a3b8' }}>
          Extract proposed curriculum hierarchies using AI provider abstraction. Human approval is strictly required before publication.
        </p>
      </header>

      {message && (
        <div style={{ padding: '12px', borderRadius: '8px', backgroundColor: '#1e293b', border: '1px solid #6366f1', marginBottom: '20px' }}>
          {message}
        </div>
      )}

      {/* Extraction Trigger Panel */}
      <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px', marginBottom: '28px' }}>
        <h2 style={{ fontSize: '1.2rem', marginBottom: '16px' }}>Trigger AI Extraction from Document</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 200px', gap: '16px', alignItems: 'center' }}>
          <div>
            <label style={{ fontSize: '0.85rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Target Curriculum</label>
            <select
              value={selectedCurrId}
              onChange={(e) => setSelectedCurrId(e.target.value)}
              style={{ width: '100%', padding: '10px', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }}
            >
              {curricula.map((c) => (
                <option key={c.id} value={c.id}>{c.name} (Grade {c.grade_level})</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.85rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Ingested Document</label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              style={{ width: '100%', padding: '10px', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }}
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>{d.file_name}</option>
              ))}
            </select>
          </div>

          <button
            onClick={handleTriggerAIExtraction}
            disabled={isExtracting || !selectedDocId || !selectedCurrId}
            style={{
              padding: '12px',
              backgroundColor: isExtracting ? '#475569' : '#6366f1',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 'bold',
              cursor: isExtracting ? 'not-allowed' : 'pointer',
              marginTop: '18px'
            }}
          >
            {isExtracting ? 'Extracting...' : '✨ Run AI Extraction'}
          </button>
        </div>
      </section>

      {/* Human Review & Editing Inspector */}
      {reviewVersion && (
        <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #334155', paddingBottom: '16px' }}>
            <div>
              <h2 style={{ fontSize: '1.4rem' }}>
                Proposed Version {reviewVersion.version_number} Review
              </h2>
              <span style={{ fontSize: '0.85rem', padding: '2px 8px', borderRadius: '4px', backgroundColor: '#f59e0b', color: '#fff', fontWeight: 'bold', marginRight: '8px' }}>
                STATUS: {reviewVersion.status} (PROPOSED / UNCONFIRMED)
              </span>
            </div>

            {reviewVersion.status !== 'PUBLISHED' && (
              <button
                onClick={handleApproveAndPublish}
                style={{ padding: '10px 20px', background: '#10b981', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}
              >
                ✅ Human Approve & Publish as Authoritative
              </button>
            )}
          </div>

          {/* Tree View with Edit / Delete Actions */}
          {reviewVersion.chapters?.map((ch: any) => (
            <div key={ch.id} style={{ backgroundColor: '#0f172a', borderRadius: '8px', padding: '16px', marginBottom: '16px', borderLeft: '4px solid #818cf8' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ color: '#a5b4fc', fontSize: '1.2rem' }}>📖 Chapter: {ch.name}</h3>
                <button onClick={() => handleNodeAction('DELETE', 'chapter', ch.id)} style={{ fontSize: '0.75rem', background: '#ef4444', color: '#fff', border: 'none', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer' }}>
                  Delete Chapter
                </button>
              </div>

              {ch.topics?.map((tp: any) => (
                <div key={tp.id} style={{ marginLeft: '16px', marginTop: '12px', padding: '12px', backgroundColor: '#1e293b', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h4 style={{ color: '#38bdf8' }}>📂 Topic: {tp.name}</h4>
                    <button onClick={() => handleNodeAction('DELETE', 'topic', tp.id)} style={{ fontSize: '0.75rem', background: '#ef4444', color: '#fff', border: 'none', padding: '3px 6px', borderRadius: '4px', cursor: 'pointer' }}>
                      Delete Topic
                    </button>
                  </div>

                  {tp.concepts?.map((cp: any) => (
                    <div key={cp.id} style={{ marginLeft: '12px', marginTop: '8px', padding: '10px', backgroundColor: '#0f172a', borderRadius: '4px', borderLeft: '2px solid #34d399' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 'bold', color: '#34d399' }}>
                          💡 Concept: {cp.name} (Difficulty: {cp.difficulty_level})
                        </span>
                        <button onClick={() => handleNodeAction('DELETE', 'concept', cp.id)} style={{ fontSize: '0.7rem', background: '#ef4444', color: '#fff', border: 'none', padding: '2px 6px', borderRadius: '4px', cursor: 'pointer' }}>
                          Delete Concept
                        </button>
                      </div>

                      {cp.learning_objectives?.map((lo: any) => (
                        <div key={lo.id} style={{ marginLeft: '12px', marginTop: '4px', fontSize: '0.85rem', color: '#cbd5e1' }}>
                          🎯 <strong>[{lo.code}]</strong>: {lo.description} (Taxonomy: {lo.bloom_taxonomy_level})
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
