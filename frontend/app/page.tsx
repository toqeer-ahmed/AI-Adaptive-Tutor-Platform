'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';

interface HealthStatus {
  status: string;
  version: string;
  environment: string;
  services?: {
    postgresql: string;
    redis: string;
  };
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function checkHealth() {
      const res = await apiClient.get<HealthStatus>('/api/v1/health');
      if (res.data) {
        setHealth(res.data);
      }
      setLoading(false);
    }
    checkHealth();
  }, []);

  return (
    <main style={{ padding: '40px', maxWidth: '900px', margin: '0 auto' }}>
      <header style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '8px', color: '#818cf8' }}>
          AI Adaptive Education Platform
        </h1>
        <p style={{ fontSize: '1.1rem', color: '#94a3b8' }}>
          Production-grade Multi-Tenant Learning System (Grades 4–8)
        </p>
      </header>

      <section style={{
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '12px',
        padding: '24px',
        marginBottom: '24px'
      }}>
        <h2 style={{ fontSize: '1.4rem', marginBottom: '16px', color: '#f8fafc' }}>
          System Health Status
        </h2>
        {loading ? (
          <p style={{ color: '#94a3b8' }}>Checking backend health...</p>
        ) : health ? (
          <div>
            <p style={{ marginBottom: '8px' }}>
              <strong>API Status:</strong>{' '}
              <span style={{ color: health.status === 'healthy' ? '#4ade80' : '#f87171' }}>
                {health.status.toUpperCase()}
              </span>
            </p>
            <p style={{ marginBottom: '8px' }}>
              <strong>Environment:</strong> {health.environment}
            </p>
            <p style={{ marginBottom: '12px' }}>
              <strong>Version:</strong> {health.version}
            </p>
            {health.services && (
              <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #334155' }}>
                <p style={{ marginBottom: '4px' }}>
                  PostgreSQL: <span style={{ color: health.services.postgresql === 'reachable' ? '#4ade80' : '#f87171' }}>{health.services.postgresql}</span>
                </p>
                <p>
                  Redis: <span style={{ color: health.services.redis === 'reachable' ? '#4ade80' : '#f87171' }}>{health.services.redis}</span>
                </p>
              </div>
            )}
          </div>
        ) : (
          <p style={{ color: '#f87171' }}>Backend API unreachable at NEXT_PUBLIC_API_URL</p>
        )}
      </section>
    </main>
  );
}
