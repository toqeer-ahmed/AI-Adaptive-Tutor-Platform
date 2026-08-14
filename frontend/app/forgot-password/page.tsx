'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import {
  WobblyCard,
  WobblyButton,
  HandBadge
} from '@/lib/HandDrawnComponents';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;

    setLoading(true);
    setError(null);

    try {
      await apiClient.post('/api/v1/auth/password-reset/request', { email: email.trim().toLowerCase() });
      setSubmitted(true);
    } catch (e: any) {
      // Show same neutral message to prevent user enumeration
      setSubmitted(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '32px 16px', background: 'var(--bg-paper)' }}>
      <div style={{ width: '100%', maxWidth: '520px' }}>
        <WobblyCard decoration="tape" style={{ padding: '36px 32px' }}>
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ fontSize: '2rem' }}>🔑</span>
              <h1 style={{ fontSize: '2rem' }}>Reset Password</h1>
            </div>
            <p style={{ color: 'var(--pencil-subtle)', fontSize: '1.02rem' }}>
              Enter your account email to receive instructions for resetting your password.
            </p>
          </div>

          {submitted ? (
            <div
              style={{
                padding: '20px',
                background: 'var(--postit-green)',
                borderRadius: 'var(--wobbly-sm)',
                border: '1.5px solid var(--pencil-black)',
                boxShadow: 'var(--shadow-hard-sm)',
                marginBottom: '24px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span style={{ fontSize: '1.4rem' }}>📬</span>
                <strong style={{ fontSize: '1.1rem', color: 'var(--pencil-black)' }}>Instructions Sent</strong>
              </div>
              <p style={{ fontSize: '0.95rem', color: 'var(--pencil-subtle)', lineHeight: 1.5 }}>
                If an active account exists for <strong style={{ color: 'var(--pencil-black)' }}>{email}</strong>, a secure password reset token has been dispatched.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <div>
                <label style={{ display: 'block', fontWeight: 700, fontSize: '0.95rem', marginBottom: '6px', color: 'var(--pencil-black)' }}>
                  Registered Email Address
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. user@school.edu"
                  className="wobbly-input"
                  style={{ width: '100%' }}
                />
              </div>

              <WobblyButton
                variant="red"
                disabled={loading}
                style={{ width: '100%', fontSize: '1.1rem', padding: '12px' }}
              >
                {loading ? 'Sending Request...' : 'Send Reset Instructions →'}
              </WobblyButton>
            </form>
          )}

          <div style={{ marginTop: '24px', textAlign: 'center' }}>
            <Link href="/login" style={{ color: 'var(--pen-blue)', textDecoration: 'none', fontWeight: 700, fontSize: '0.95rem' }}>
              ← Return to Sign In
            </Link>
          </div>
        </WobblyCard>
      </div>
    </div>
  );
}
