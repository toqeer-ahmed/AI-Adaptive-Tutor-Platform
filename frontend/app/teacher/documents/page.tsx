'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface SourceDocument {
  id: string;
  file_name: string;
  file_size: number;
  status: string;
  error_message: string | null;
  created_at: string;
}

interface Chunk {
  id: string;
  chunk_index: number;
  text: string;
  page_number: number | null;
  section: string | null;
}

export default function DocumentIngestionPage() {
  const [documents, setDocuments] = useState<SourceDocument[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedDocChunks, setSelectedDocChunks] = useState<Chunk[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchDocuments();
    const interval = setInterval(fetchDocuments, 5000); // Poll status every 5s
    return () => clearInterval(interval);
  }, []);

  async function fetchDocuments() {
    const res = await apiClient.get<SourceDocument[]>('/api/v1/documents');
    if (res.data) {
      setDocuments(res.data);
    }
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    setMessage(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/documents/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
        },
        body: formData
      });

      const json = await response.json();
      if (!response.ok) {
        setMessage(`Upload Failed: ${json.detail || 'Server error'}`);
      } else {
        setMessage(`Document '${selectedFile.name}' uploaded successfully! Pipeline processing started.`);
        setSelectedFile(null);
        fetchDocuments();
      }
    } catch (err: any) {
      setMessage(`Upload Exception: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  }

  async function handleViewChunks(docId: string) {
    setSelectedDocId(docId);
    const res = await apiClient.get<Chunk[]>(`/api/v1/documents/${docId}/chunks`);
    if (res.data) {
      setSelectedDocChunks(res.data);
    }
  }

  function getStatusBadgeColor(status: string) {
    switch (status) {
      case 'COMPLETED': return '#22c55e';
      case 'FAILED': return '#ef4444';
      case 'OCR_REQUIRED': case 'REVIEW_REQUIRED': return '#f59e0b';
      default: return '#3b82f6';
    }
  }

  return (
    <div style={{ padding: '32px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'sans-serif', color: '#f8fafc' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '2rem', color: '#818cf8', marginBottom: '8px' }}>
          Curriculum Document Ingestion Pipeline
        </h1>
        <p style={{ color: '#94a3b8' }}>
          Upload PDF, DOCX, or TXT syllabi for automated validation, malware scanning, parsing, and page-aware chunking.
        </p>
      </header>

      {message && (
        <div style={{ padding: '12px', borderRadius: '8px', backgroundColor: '#1e293b', border: '1px solid #6366f1', marginBottom: '20px' }}>
          {message}
        </div>
      )}

      {/* File Upload Section */}
      <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px', marginBottom: '28px' }}>
        <h2 style={{ fontSize: '1.2rem', marginBottom: '16px', color: '#f8fafc' }}>Upload Curriculum Syllabus</h2>
        <form onSubmit={handleUpload} style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
            style={{ flex: 1, padding: '10px', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }}
            required
          />
          <button
            type="submit"
            disabled={isUploading || !selectedFile}
            style={{
              padding: '10px 24px',
              backgroundColor: isUploading ? '#475569' : '#6366f1',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 'bold',
              cursor: isUploading ? 'not-allowed' : 'pointer'
            }}
          >
            {isUploading ? 'Uploading...' : 'Upload & Process'}
          </button>
        </form>
        <span style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '8px', display: 'block' }}>
          Allowed types: PDF, DOCX, TXT. Max size: 50 MB. Strictly checked for magic-byte signatures.
        </span>
      </section>

      {/* Documents List & Status */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '16px' }}>Uploaded Documents & Pipeline Status</h2>
          {documents.length === 0 ? (
            <p style={{ color: '#94a3b8' }}>No documents uploaded yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {documents.map((doc) => (
                <div key={doc.id} style={{ padding: '12px', background: '#0f172a', borderRadius: '8px', border: '1px solid #334155' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 'bold', color: '#38bdf8' }}>{doc.file_name}</span>
                    <span style={{
                      fontSize: '0.75rem',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      backgroundColor: getStatusBadgeColor(doc.status),
                      color: '#fff',
                      fontWeight: 'bold'
                    }}>
                      {doc.status}
                    </span>
                  </div>

                  <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '8px' }}>
                    {(doc.file_size / (1024 * 1024)).toFixed(2)} MB • {new Date(doc.created_at).toLocaleString()}
                  </div>

                  {doc.error_message && (
                    <div style={{ fontSize: '0.8rem', color: '#f87171', marginBottom: '8px', background: '#450a0a', padding: '6px', borderRadius: '4px' }}>
                      ⚠️ Error: {doc.error_message}
                    </div>
                  )}

                  {doc.status === 'COMPLETED' && (
                    <button
                      onClick={() => handleViewChunks(doc.id)}
                      style={{ padding: '4px 10px', fontSize: '0.8rem', background: '#6366f1', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                    >
                      View Extracted Chunks
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Chunks Inspector Panel */}
        <section style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '16px' }}>Extracted Chunks & Source Metadata</h2>
          {selectedDocChunks.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '500px', overflowY: 'auto' }}>
              {selectedDocChunks.map((chunk) => (
                <div key={chunk.id} style={{ padding: '12px', background: '#0f172a', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#38bdf8', marginBottom: '4px' }}>
                    <span>Chunk #{chunk.chunk_index}</span>
                    <span>Page: {chunk.page_number ?? 'N/A'} | Section: {chunk.section || 'General'}</span>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: '#cbd5e1', whiteSpace: 'pre-wrap' }}>
                    {chunk.text}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: '#94a3b8' }}>
              Select a completed document on the left to view its extracted chunks and source page metadata.
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
