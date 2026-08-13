'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface SourceChunk {
  document_id?: string;
  page_number?: number;
  text?: string;
}

interface TutorTurn {
  id: string;
  student_message: string;
  tutor_response: string;
  mode: string;
  sources_cited: SourceChunk[];
  created_at: string;
}

export default function StudentTutorWorkspace() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [conceptId, setConceptId] = useState<string>('00000000-0000-0000-0000-000000000000');
  const [versionId, setVersionId] = useState<string>('00000000-0000-0000-0000-000000000000');
  const [mode, setMode] = useState<string>('explanation');

  const [inputMessage, setInputMessage] = useState('');
  const [turns, setTurns] = useState<TutorTurn[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [activeSources, setActiveSources] = useState<SourceChunk[]>([]);

  useEffect(() => {
    initTutorSession();
  }, []);

  async function initTutorSession() {
    const currRes = await apiClient.get<any[]>('/api/v1/curricula');
    let cId = conceptId;
    let vId = versionId;

    if (currRes.data && currRes.data.length > 0 && currRes.data[0].versions.length > 0) {
      vId = currRes.data[0].versions[0].id;
      setVersionId(vId);
      const vRes = await apiClient.get<any>(`/api/v1/curricula/versions/${vId}`);
      if (vRes.data && vRes.data.chapters.length > 0 && vRes.data.chapters[0].topics.length > 0 && vRes.data.chapters[0].topics[0].concepts.length > 0) {
        cId = vRes.data.chapters[0].topics[0].concepts[0].id;
        setConceptId(cId);
      }
    }

    const sessRes = await apiClient.post<{ session_id: string }>('/api/v1/tutor/sessions', {
      concept_id: cId,
      curriculum_version_id: vId,
      mode: mode
    });

    if (sessRes.data) {
      setSessionId(sessRes.data.session_id);
    }
  }

  async function handleSendMessage(overrideMode?: string) {
    if (!inputMessage.trim() || !sessionId || isSending) return;
    const msg = inputMessage;
    setInputMessage('');
    setIsSending(true);

    const activeMode = overrideMode || mode;

    const res = await apiClient.post<TutorTurn>('/api/v1/tutor/turn', {
      session_id: sessionId,
      student_message: msg,
      mode: activeMode,
      provider: 'mock'
    });

    setIsSending(false);

    if (res.data) {
      setTurns(prev => [...prev, res.data!]);
      if (res.data.sources_cited && res.data.sources_cited.length > 0) {
        setActiveSources(res.data.sources_cited);
      }
    }
  }

  function handleRequestHint() {
    setInputMessage('Can you give me a hint to help me figure this out?');
    handleSendMessage('hint');
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '24px', height: 'calc(100vh - 64px)', padding: '24px', maxWidth: '1400px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      
      {/* Main Chat Workspace */}
      <div style={{ display: 'flex', flexDirection: 'column', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', overflow: 'hidden' }}>
        
        {/* Header & Mode Switcher */}
        <header style={{ padding: '16px 20px', borderBottom: '1px solid #334155', backgroundColor: '#0f172a', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontSize: '1.2rem', color: '#818cf8', margin: 0 }}>
              🤖 AI Adaptive Tutor (Grade 6 Mathematics)
            </h1>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '2px 0 0 0' }}>
              Curriculum Grounded • Socratic & Hint Guided
            </p>
          </div>

          <div style={{ display: 'flex', gap: '6px' }}>
            {['explanation', 'socratic', 'hint', 'remediation', 'worked_example'].map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                style={{
                  padding: '4px 10px',
                  fontSize: '0.75rem',
                  borderRadius: '6px',
                  border: 'none',
                  backgroundColor: mode === m ? '#6366f1' : '#334155',
                  color: '#fff',
                  cursor: 'pointer',
                  fontWeight: mode === m ? 'bold' : 'normal'
                }}
              >
                {m.toUpperCase()}
              </button>
            ))}
          </div>
        </header>

        {/* Conversation Message History */}
        <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {turns.length === 0 && (
            <div style={{ textAlign: 'center', color: '#94a3b8', marginTop: '60px' }}>
              <p style={{ fontSize: '1.1rem', marginBottom: '8px' }}>👋 Hello! Ask me anything about Grade 6 Mathematics!</p>
              <p style={{ fontSize: '0.85rem' }}>Example: "Why do I need a common denominator?"</p>
            </div>
          )}

          {turns.map((tr) => (
            <React.Fragment key={tr.id}>
              {/* Student Bubble */}
              <div style={{ alignSelf: 'flex-end', maxWidth: '75%', backgroundColor: '#2563eb', padding: '12px 16px', borderRadius: '12px 12px 0 12px', color: '#fff' }}>
                <div style={{ fontSize: '0.95rem' }}>{tr.student_message}</div>
              </div>

              {/* Tutor Bubble */}
              <div style={{ alignSelf: 'flex-start', maxWidth: '80%', backgroundColor: '#0f172a', border: '1px solid #334155', padding: '14px 18px', borderRadius: '12px 12px 12px 0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#818cf8' }}>
                    TUTOR ({tr.mode.toUpperCase()})
                  </span>
                  {tr.sources_cited && tr.sources_cited.length > 0 && (
                    <span style={{ fontSize: '0.75rem', color: '#10b981' }}>
                      📚 {tr.sources_cited.length} Sources Grounded
                    </span>
                  )}
                </div>
                <div style={{ fontSize: '0.95rem', lineHeight: '1.5', color: '#f1f5f9' }}>
                  {tr.tutor_response}
                </div>
              </div>
            </React.Fragment>
          ))}

          {isSending && (
            <div style={{ alignSelf: 'flex-start', color: '#94a3b8', fontSize: '0.85rem', fontStyle: 'italic' }}>
              Tutor is retrieving curriculum and thinking...
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div style={{ padding: '16px', borderTop: '1px solid #334155', backgroundColor: '#0f172a', display: 'flex', gap: '10px' }}>
          <input
            type="text"
            placeholder="Ask a question (e.g. Why do I need a common denominator?)..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            style={{ flex: 1, padding: '12px', background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#fff', fontSize: '0.95rem' }}
          />
          <button
            onClick={handleRequestHint}
            style={{ padding: '12px 16px', background: '#f59e0b', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            💡 Hint
          </button>
          <button
            onClick={() => handleSendMessage()}
            disabled={isSending || !inputMessage.trim()}
            style={{ padding: '12px 20px', background: isSending ? '#475569' : '#6366f1', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            Send
          </button>
        </div>
      </div>

      {/* Curriculum RAG Inspector Sidebar */}
      <aside style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px', display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ fontSize: '1.1rem', color: '#38bdf8', marginBottom: '12px' }}>
          📚 Grounded Curriculum Evidence
        </h2>
        <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '16px' }}>
          Approved textbook chunks retrieved for current response.
        </p>

        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {activeSources.length === 0 ? (
            <div style={{ fontSize: '0.85rem', color: '#64748b', fontStyle: 'italic' }}>
              No sources cited yet. Ask a question to view RAG evidence.
            </div>
          ) : (
            activeSources.map((src, idx) => (
              <div key={idx} style={{ padding: '12px', background: '#0f172a', borderRadius: '6px', borderLeft: '3px solid #10b981' }}>
                <div style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 'bold', marginBottom: '4px' }}>
                  Chunk #{idx + 1} (Page {src.page_number || 1})
                </div>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8', lineHeight: '1.4' }}>
                  {src.text ? src.text.slice(0, 180) + '...' : 'Approved curriculum content.'}
                </div>
              </div>
            ))
          )}
        </div>
      </aside>

    </div>
  );
}
