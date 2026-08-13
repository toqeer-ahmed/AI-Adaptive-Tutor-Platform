'use client';

import React, { useState } from 'react';
import { apiClient } from '@/lib/api-client';

interface SourceChunk {
  chunk_id: string;
  text: string;
  grade: number;
  subject: string;
  chapter: string | null;
  topic: string | null;
  concept: string | null;
  page_number: number | null;
  fusion_score: number;
}

interface RAGResponse {
  has_context: boolean;
  fallback_response: string | null;
  confidence_score: number;
  formatted_context: string;
  sources: SourceChunk[];
}

export default function StudentRAGPage() {
  const [query, setQuery] = useState('How do I find a common denominator for adding fractions in Grade 6 Math?');
  const [grade, setGrade] = useState(6);
  const [subject, setSubject] = useState('Mathematics');

  const [isLoading, setIsLoading] = useState(false);
  const [ragResult, setRagResult] = useState<RAGResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query) return;

    setIsLoading(true);
    setError(null);

    const res = await apiClient.post<RAGResponse>('/api/v1/rag/query', {
      query,
      grade: Number(grade),
      subject
    });

    setIsLoading(false);

    if (res.error) {
      setError(`RAG Query Error: ${res.error.message}`);
    } else if (res.data) {
      setRagResult(res.data);
    }
  }

  return (
    <div style={{ padding: '32px', maxWidth: '1000px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '2rem', color: '#818cf8', marginBottom: '8px' }}>
          Approved Curriculum Search & Source Citation Inspector
        </h1>
        <p style={{ color: '#94a3b8' }}>
          Query approved, published curriculum material with hybrid vector retrieval and explicit source evidence citations.
        </p>
      </header>

      {error && (
        <div style={{ padding: '12px', borderRadius: '8px', backgroundColor: '#450a0a', border: '1px solid #ef4444', marginBottom: '20px', color: '#f87171' }}>
          {error}
        </div>
      )}

      {/* Query Bar */}
      <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px', marginBottom: '28px' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 150px 180px', gap: '12px' }}>
            <input
              type="text"
              placeholder="Ask a question about your curriculum..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{ padding: '12px', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#fff', fontSize: '1rem' }}
              required
            />
            <select
              value={grade}
              onChange={(e) => setGrade(Number(e.target.value))}
              style={{ padding: '12px', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }}
            >
              <option value={4}>Grade 4</option>
              <option value={5}>Grade 5</option>
              <option value={6}>Grade 6</option>
              <option value={7}>Grade 7</option>
              <option value={8}>Grade 8</option>
            </select>
            <input
              type="text"
              placeholder="Subject (e.g. Mathematics)"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              style={{ padding: '12px', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            style={{
              padding: '12px 24px',
              backgroundColor: isLoading ? '#475569' : '#6366f1',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 'bold',
              fontSize: '1rem',
              cursor: isLoading ? 'not-allowed' : 'pointer'
            }}
          >
            {isLoading ? 'Retrieving Approved Context...' : '🔍 Search Approved Curriculum'}
          </button>
        </form>
      </section>

      {/* Results Display */}
      {ragResult && (
        <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          {!ragResult.has_context ? (
            /* Controlled No-Context Fallback Card */
            <div style={{ padding: '20px', borderRadius: '8px', backgroundColor: '#0f172a', border: '1px solid #f59e0b', color: '#fbbf24' }}>
              <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>⚠️ No Curriculum Evidence Found</h3>
              <p style={{ fontSize: '1rem', color: '#fcd34d' }}>
                "{ragResult.fallback_response}"
              </p>
            </div>
          ) : (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #334155', paddingBottom: '12px' }}>
                <h2 style={{ fontSize: '1.3rem', color: '#38bdf8' }}>
                  Retrieved Source-Traceable Evidence ({ragResult.sources.length} Chunks)
                </h2>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                  Fusion Score: {ragResult.confidence_score.toFixed(4)}
                </span>
              </div>

              {/* Source Cards */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {ragResult.sources.map((src, idx) => (
                  <div key={src.chunk_id} style={{ padding: '16px', background: '#0f172a', borderRadius: '8px', borderLeft: '4px solid #38bdf8' }}>
                    <div style={{ fontSize: '0.85rem', color: '#38bdf8', fontWeight: 'bold', marginBottom: '6px' }}>
                      [Citation #{idx + 1}]: Grade {src.grade} {src.subject} • Chapter: {src.chapter || 'N/A'} • Topic: {src.topic || 'N/A'} • Concept: {src.concept || 'N/A'} (Page {src.page_number ?? 'N/A'})
                    </div>
                    <p style={{ fontSize: '0.95rem', color: '#cbd5e1', whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>
                      "{src.text}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
