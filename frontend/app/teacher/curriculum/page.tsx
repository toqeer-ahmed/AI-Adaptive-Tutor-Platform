'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface CurriculumVersion {
  id: string;
  version_number: number;
  status: string;
}

interface Curriculum {
  id: string;
  name: string;
  grade_level: number;
  subject_name: string;
  versions: CurriculumVersion[];
}

interface Objective {
  id: string;
  code: string;
  description: string;
}

interface Concept {
  id: string;
  name: string;
  difficulty_level: number;
  learning_objectives: Objective[];
}

interface Topic {
  id: string;
  name: string;
  concepts: Concept[];
}

interface Chapter {
  id: string;
  name: string;
  topics: Topic[];
}

interface VersionTree {
  id: string;
  version_number: number;
  status: string;
  published_at: string | null;
  chapters: Chapter[];
}

export default function CurriculumManagementPage() {
  const [curricula, setCurricula] = useState<Curriculum[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [versionTree, setVersionTree] = useState<VersionTree | null>(null);
  
  // New Curriculum Form
  const [name, setName] = useState('Grade 6 Core Curriculum');
  const [gradeLevel, setGradeLevel] = useState(6);
  const [subjectName, setSubjectName] = useState('Mathematics');

  // Node Inputs
  const [chapterName, setChapterName] = useState('');
  const [topicName, setTopicName] = useState('');
  const [conceptName, setConceptName] = useState('');
  const [objectiveCode, setObjectiveCode] = useState('');
  const [objectiveDesc, setObjectiveDesc] = useState('');

  const [activeChapterId, setActiveChapterId] = useState<string | null>(null);
  const [activeTopicId, setActiveTopicId] = useState<string | null>(null);
  const [activeConceptId, setActiveConceptId] = useState<string | null>(null);

  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchCurricula();
  }, []);

  async function fetchCurricula() {
    const res = await apiClient.get<Curriculum[]>('/api/v1/curricula');
    if (res.data) {
      setCurricula(res.data);
      if (res.data.length > 0 && res.data[0].versions.length > 0) {
        loadVersionTree(res.data[0].versions[0].id);
      }
    }
  }

  async function loadVersionTree(versionId: string) {
    setSelectedVersionId(versionId);
    const res = await apiClient.get<VersionTree>(`/api/v1/curricula/versions/${versionId}`);
    if (res.data) {
      setVersionTree(res.data);
    }
  }

  async function handleCreateCurriculum(e: React.FormEvent) {
    e.preventDefault();
    const res = await apiClient.post('/api/v1/curricula', {
      name,
      grade_level: Number(gradeLevel),
      subject_name: subjectName
    });
    if (res.data) {
      setMessage(`Curriculum '${name}' created successfully!`);
      fetchCurricula();
    }
  }

  async function handleTransitionStatus(nextStatus: string) {
    if (!selectedVersionId) return;
    const res = await apiClient.post(`/api/v1/curricula/versions/${selectedVersionId}/status`, {
      status: nextStatus
    });
    if (res.error) {
      setMessage(`Transition Error: ${res.error.message}`);
    } else {
      setMessage(`Version status updated to ${nextStatus}!`);
      loadVersionTree(selectedVersionId);
      fetchCurricula();
    }
  }

  async function handleAddChapter() {
    if (!selectedVersionId || !chapterName) return;
    const res = await apiClient.post(`/api/v1/curricula/versions/${selectedVersionId}/chapters`, {
      name: chapterName
    });
    if (res.error) {
      setMessage(`Error: ${res.error.message}`);
    } else {
      setChapterName('');
      loadVersionTree(selectedVersionId);
    }
  }

  async function handleAddTopic(chapterId: string) {
    if (!topicName) return;
    const res = await apiClient.post(`/api/v1/curricula/chapters/${chapterId}/topics`, {
      name: topicName
    });
    if (res.error) {
      setMessage(`Error: ${res.error.message}`);
    } else {
      setTopicName('');
      loadVersionTree(selectedVersionId!);
    }
  }

  async function handleAddConcept(topicId: string) {
    if (!conceptName) return;
    const res = await apiClient.post(`/api/v1/curricula/topics/${topicId}/concepts`, {
      name: conceptName,
      difficulty_level: 3
    });
    if (res.error) {
      setMessage(`Error: ${res.error.message}`);
    } else {
      setConceptName('');
      loadVersionTree(selectedVersionId!);
    }
  }

  async function handleAddObjective(conceptId: string) {
    if (!objectiveCode || !objectiveDesc) return;
    const res = await apiClient.post(`/api/v1/curricula/concepts/${conceptId}/objectives`, {
      code: objectiveCode,
      description: objectiveDesc
    });
    if (res.error) {
      setMessage(`Error: ${res.error.message}`);
    } else {
      setObjectiveCode('');
      setObjectiveDesc('');
      loadVersionTree(selectedVersionId!);
    }
  }

  const isImmutable = versionTree?.status === 'PUBLISHED' || versionTree?.status === 'ARCHIVED';

  return (
    <div style={{ padding: '32px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '2rem', color: '#818cf8', marginBottom: '8px' }}>
          Curriculum Management & Hierarchy Builder
        </h1>
        <p style={{ color: '#94a3b8' }}>
          Manual curriculum tree creation, source traceability, and version publishing workflow.
        </p>
      </header>

      {message && (
        <div style={{ padding: '12px', borderRadius: '8px', backgroundColor: '#1e293b', border: '1px solid #6366f1', marginBottom: '20px' }}>
          {message}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px' }}>
        {/* Left Panel: Curricula & Version Selector */}
        <aside style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '16px' }}>Create Curriculum</h2>
          <form onSubmit={handleCreateCurriculum} style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
            <input
              type="text"
              placeholder="Curriculum Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{ padding: '8px', borderRadius: '6px', background: '#0f172a', border: '1px solid #334155', color: '#fff' }}
              required
            />
            <input
              type="number"
              placeholder="Grade Level (4-8)"
              value={gradeLevel}
              onChange={(e) => setGradeLevel(Number(e.target.value))}
              style={{ padding: '8px', borderRadius: '6px', background: '#0f172a', border: '1px solid #334155', color: '#fff' }}
              required
            />
            <input
              type="text"
              placeholder="Subject (e.g. Mathematics)"
              value={subjectName}
              onChange={(e) => setSubjectName(e.target.value)}
              style={{ padding: '8px', borderRadius: '6px', background: '#0f172a', border: '1px solid #334155', color: '#fff' }}
              required
            />
            <button type="submit" style={{ padding: '10px', borderRadius: '6px', background: '#6366f1', color: '#fff', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}>
              + Create Curriculum
            </button>
          </form>

          <h2 style={{ fontSize: '1.2rem', marginBottom: '12px' }}>Curricula List</h2>
          {curricula.map((c) => (
            <div key={c.id} style={{ marginBottom: '16px', padding: '12px', background: '#0f172a', borderRadius: '8px' }}>
              <div style={{ fontWeight: 'bold', color: '#38bdf8' }}>{c.name}</div>
              <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '8px' }}>
                Grade {c.grade_level} • {c.subject_name}
              </div>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {c.versions.map((v) => (
                  <button
                    key={v.id}
                    onClick={() => loadVersionTree(v.id)}
                    style={{
                      padding: '4px 8px',
                      fontSize: '0.75rem',
                      borderRadius: '4px',
                      border: '1px solid #334155',
                      background: selectedVersionId === v.id ? '#6366f1' : '#1e293b',
                      color: '#fff',
                      cursor: 'pointer'
                    }}
                  >
                    v{v.version_number} ({v.status})
                  </button>
                ))}
              </div>
            </div>
          ))}
        </aside>

        {/* Right Panel: Tree View & State Control */}
        <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          {versionTree ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #334155', paddingBottom: '16px' }}>
                <div>
                  <h2 style={{ fontSize: '1.4rem' }}>
                    Version {versionTree.version_number} Tree Builder
                  </h2>
                  <span style={{
                    fontSize: '0.85rem',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    backgroundColor: isImmutable ? '#ef4444' : '#22c55e',
                    color: '#fff',
                    fontWeight: 'bold',
                    marginRight: '8px'
                  }}>
                    {versionTree.status} {isImmutable && '(IMMUTABLE)'}
                  </span>
                </div>

                {/* State Machine Transition Actions */}
                <div style={{ display: 'flex', gap: '8px' }}>
                  {versionTree.status === 'DRAFT' && (
                    <button onClick={() => handleTransitionStatus('REVIEW')} style={{ padding: '8px 14px', borderRadius: '6px', background: '#f59e0b', color: '#fff', border: 'none', cursor: 'pointer' }}>
                      Submit for Review
                    </button>
                  )}
                  {versionTree.status === 'REVIEW' && (
                    <button onClick={() => handleTransitionStatus('APPROVED')} style={{ padding: '8px 14px', borderRadius: '6px', background: '#3b82f6', color: '#fff', border: 'none', cursor: 'pointer' }}>
                      Approve
                    </button>
                  )}
                  {versionTree.status === 'APPROVED' && (
                    <button onClick={() => handleTransitionStatus('PUBLISHED')} style={{ padding: '8px 14px', borderRadius: '6px', background: '#10b981', color: '#fff', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}>
                      Publish Version
                    </button>
                  )}
                </div>
              </div>

              {/* Add Chapter */}
              {!isImmutable && (
                <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
                  <input
                    type="text"
                    placeholder="New Chapter Name (e.g., Fractions)"
                    value={chapterName}
                    onChange={(e) => setChapterName(e.target.value)}
                    style={{ flex: 1, padding: '8px', borderRadius: '6px', background: '#0f172a', border: '1px solid #334155', color: '#fff' }}
                  />
                  <button onClick={handleAddChapter} style={{ padding: '8px 16px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
                    + Add Chapter
                  </button>
                </div>
              )}

              {/* Tree View */}
              {versionTree.chapters.map((ch) => (
                <div key={ch.id} style={{ backgroundColor: '#0f172a', borderRadius: '8px', padding: '16px', marginBottom: '16px', borderLeft: '4px solid #6366f1' }}>
                  <h3 style={{ color: '#a5b4fc', fontSize: '1.2rem', marginBottom: '8px' }}>
                    📖 Chapter: {ch.name}
                  </h3>

                  {!isImmutable && activeChapterId === ch.id && (
                    <div style={{ display: 'flex', gap: '8px', margin: '8px 0 16px 16px' }}>
                      <input
                        type="text"
                        placeholder="Topic Name (e.g., Adding Fractions)"
                        value={topicName}
                        onChange={(e) => setTopicName(e.target.value)}
                        style={{ padding: '6px', borderRadius: '4px', background: '#1e293b', border: '1px solid #334155', color: '#fff', flex: 1 }}
                      />
                      <button onClick={() => handleAddTopic(ch.id)} style={{ padding: '6px 12px', background: '#38bdf8', color: '#000', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                        + Add Topic
                      </button>
                    </div>
                  )}
                  {!isImmutable && activeChapterId !== ch.id && (
                    <button onClick={() => setActiveChapterId(ch.id)} style={{ fontSize: '0.8rem', color: '#38bdf8', background: 'none', border: 'none', cursor: 'pointer', marginBottom: '12px' }}>
                      + Add Topic to Chapter
                    </button>
                  )}

                  {/* Topics */}
                  {ch.topics.map((tp) => (
                    <div key={tp.id} style={{ marginLeft: '16px', padding: '12px', backgroundColor: '#1e293b', borderRadius: '6px', marginBottom: '12px', borderLeft: '3px solid #38bdf8' }}>
                      <h4 style={{ color: '#38bdf8', marginBottom: '6px' }}>📂 Topic: {tp.name}</h4>

                      {!isImmutable && activeTopicId === tp.id && (
                        <div style={{ display: 'flex', gap: '8px', margin: '8px 0 12px 12px' }}>
                          <input
                            type="text"
                            placeholder="Concept Name (e.g., Common Denominator)"
                            value={conceptName}
                            onChange={(e) => setConceptName(e.target.value)}
                            style={{ padding: '6px', borderRadius: '4px', background: '#0f172a', border: '1px solid #334155', color: '#fff', flex: 1 }}
                          />
                          <button onClick={() => handleAddConcept(tp.id)} style={{ padding: '6px 12px', background: '#34d399', color: '#000', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                            + Add Concept
                          </button>
                        </div>
                      )}
                      {!isImmutable && activeTopicId !== tp.id && (
                        <button onClick={() => setActiveTopicId(tp.id)} style={{ fontSize: '0.75rem', color: '#34d399', background: 'none', border: 'none', cursor: 'pointer', marginBottom: '8px' }}>
                          + Add Concept to Topic
                        </button>
                      )}

                      {/* Concepts */}
                      {tp.concepts.map((cp) => (
                        <div key={cp.id} style={{ marginLeft: '12px', padding: '10px', backgroundColor: '#0f172a', borderRadius: '4px', marginBottom: '8px', borderLeft: '2px solid #34d399' }}>
                          <div style={{ fontWeight: 'bold', color: '#34d399' }}>
                            💡 Concept: {cp.name} (Diff: {cp.difficulty_level})
                          </div>

                          {!isImmutable && activeConceptId === cp.id && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', margin: '8px 0 8px 8px' }}>
                              <input
                                type="text"
                                placeholder="Objective Code (e.g., MATH-G6-FRAC-001)"
                                value={objectiveCode}
                                onChange={(e) => setObjectiveCode(e.target.value)}
                                style={{ padding: '6px', borderRadius: '4px', background: '#1e293b', border: '1px solid #334155', color: '#fff' }}
                              />
                              <input
                                type="text"
                                placeholder="Description (e.g., Finds common denominator for two fractions)"
                                value={objectiveDesc}
                                onChange={(e) => setObjectiveDesc(e.target.value)}
                                style={{ padding: '6px', borderRadius: '4px', background: '#1e293b', border: '1px solid #334155', color: '#fff' }}
                              />
                              <button onClick={() => handleAddObjective(cp.id)} style={{ padding: '6px 12px', background: '#f472b6', color: '#000', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                                + Save Objective
                              </button>
                            </div>
                          )}
                          {!isImmutable && activeConceptId !== cp.id && (
                            <button onClick={() => setActiveConceptId(cp.id)} style={{ fontSize: '0.75rem', color: '#f472b6', background: 'none', border: 'none', cursor: 'pointer' }}>
                              + Add Learning Objective
                            </button>
                          )}

                          {/* Objectives */}
                          {cp.learning_objectives.map((lo) => (
                            <div key={lo.id} style={{ marginLeft: '12px', marginTop: '4px', fontSize: '0.85rem', color: '#cbd5e1' }}>
                              🎯 <strong>[{lo.code}]</strong>: {lo.description}
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: '40px', textAlignment: 'center', color: '#94a3b8' }}>
              Select a curriculum version on the left to view or edit the hierarchy tree.
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
