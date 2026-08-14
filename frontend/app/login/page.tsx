'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth, DEMO_CREDENTIALS, SupportedRole } from '@/lib/auth-context';
import {
  WobblyCard,
  WobblyButton,
  HandBadge
} from '@/lib/HandDrawnComponents';

export default function LoginPage() {
  const { login, quickDemoLogin } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    if (!email || !password) {
      setErrorMsg('Please enter both email and password.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);

    const res = await login(email, password, rememberMe);
    setLoading(false);

    if (res.success) {
      router.push('/dashboard');
    } else {
      setErrorMsg(res.error || 'Invalid email or password.');
    }
  }

  async function handleDemoRole(role: SupportedRole) {
    setLoading(true);
    setErrorMsg(null);
    const success = await quickDemoLogin(role);
    setLoading(false);
    if (success) {
      router.push('/dashboard');
    } else {
      setErrorMsg(`Could not log in as demo ${role}.`);
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '32px 16px', background: 'var(--bg-paper)' }}>
      <div style={{ width: '100%', maxWidth: '920px', display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '32px' }}>
        {/* Left Side: Standard Login Form */}
        <WobblyCard decoration="tape" style={{ padding: '36px 32px' }}>
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ fontSize: '2rem' }}>📐</span>
              <h1 style={{ fontSize: '2.1rem' }}>Welcome Back</h1>
            </div>
            <p style={{ color: 'var(--pencil-subtle)', fontSize: '1.05rem' }}>
              Sign in to your AI Adaptive Education account.
            </p>
          </div>

          {errorMsg && (
            <div
              style={{
                padding: '12px 16px',
                background: '#fee2e2',
                border: '1.5px solid var(--marker-red)',
                borderRadius: 'var(--wobbly-sm)',
                color: 'var(--marker-red)',
                fontSize: '0.95rem',
                fontWeight: 700,
                marginBottom: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <span>⚠️</span>
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div>
              <label style={{ display: 'block', fontWeight: 700, fontSize: '0.95rem', marginBottom: '6px', color: 'var(--pencil-black)' }}>
                Email Address or Username
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. student@school.edu"
                className="wobbly-input"
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <label style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--pencil-black)' }}>
                  Password
                </label>
                <Link href="/forgot-password" style={{ fontSize: '0.85rem', color: 'var(--pen-blue)', textDecoration: 'none', fontWeight: 700 }}>
                  Forgot password?
                </Link>
              </div>

              <div style={{ position: 'relative' }}>
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="wobbly-input"
                  style={{ width: '100%', paddingRight: '46px' }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute',
                    right: '12px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '1.1rem'
                  }}
                >
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="checkbox"
                id="rememberMe"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                style={{ width: '18px', height: '18px', accentColor: 'var(--pencil-black)', cursor: 'pointer' }}
              />
              <label htmlFor="rememberMe" style={{ fontSize: '0.9rem', color: 'var(--pencil-subtle)', fontWeight: 600, cursor: 'pointer' }}>
                Remember session on this computer
              </label>
            </div>

            <WobblyButton
              variant="red"
              disabled={loading}
              style={{ width: '100%', marginTop: '6px', fontSize: '1.15rem', padding: '12px' }}
            >
              {loading ? '✏️ Verifying Credentials...' : 'Sign In to Portal →'}
            </WobblyButton>
          </form>
        </WobblyCard>

        {/* Right Side: Quick Role Switcher (1-Click Test Access) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <WobblyCard variant="yellow" decoration="tack-yellow" tilt="right-sm" style={{ padding: '26px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h2 style={{ fontSize: '1.3rem' }}>
                ⚡ Quick Role Switcher
              </h2>
              <HandBadge variant="blue">Instant Demo</HandBadge>
            </div>

            <p style={{ fontSize: '0.92rem', color: 'var(--pencil-subtle)', marginBottom: '16px' }}>
              Click any supported role below to immediately sign in and experience that role&apos;s authenticated dashboard:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {(Object.keys(DEMO_CREDENTIALS) as SupportedRole[]).map((role) => {
                const cred = DEMO_CREDENTIALS[role];
                return (
                  <button
                    key={role}
                    onClick={() => handleDemoRole(role)}
                    disabled={loading}
                    style={{
                      padding: '10px 14px',
                      background: '#ffffff',
                      border: '1.5px solid var(--pencil-black)',
                      borderRadius: 'var(--wobbly-sm)',
                      boxShadow: 'var(--shadow-hard-sm)',
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      textAlign: 'left'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--pencil-black)' }}>
                        {cred.title}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--pencil-subtle)' }}>
                        {cred.desc} • {cred.email}
                      </div>
                    </div>
                    <span style={{ fontSize: '1.1rem', color: 'var(--pen-blue)' }}>→</span>
                  </button>
                );
              })}
            </div>
          </WobblyCard>

          <WobblyCard variant="purple" decoration="tape" tilt="left-sm" style={{ padding: '18px 22px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ fontSize: '1.2rem' }}>🔒</span>
              <strong style={{ fontSize: '1rem', color: 'var(--pencil-black)' }}>Server-Authoritative RBAC</strong>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--pencil-subtle)', lineHeight: 1.4 }}>
              Permissions and tenant scoping are strictly validated on the backend. Client route manipulation cannot bypass authorization.
            </p>
          </WobblyCard>
        </div>
      </div>
    </div>
  );
}
