'use client';

import React, { useState } from 'react';
import AuthenticatedShell from '@/components/AuthenticatedShell';
import { useAuth } from '@/lib/auth-context';
import { apiClient } from '@/lib/api-client';
import {
  WobblyCard,
  WobblyButton,
  HandBadge
} from '@/lib/HandDrawnComponents';

export default function ProfilePage() {
  const { user, primaryRole } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    if (!fullName.trim()) return;

    setSaving(true);
    setError(null);
    setSaveSuccess(false);

    try {
      const res = await apiClient.patch('/api/v1/users/me/profile', {
        full_name: fullName.trim()
      });
      if (res.data) {
        setSaveSuccess(true);
        if (user) {
          user.full_name = res.data.full_name;
        }
      } else {
        setError(res.error?.message || 'Failed to update profile.');
      }
    } catch (e: any) {
      setError(e.message || 'Failed to save changes.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <AuthenticatedShell title="User Profile & Settings">
      <div style={{ padding: '28px 32px 60px', maxWidth: '850px', margin: '0 auto' }}>
        <WobblyCard decoration="tape" style={{ padding: '32px', marginBottom: '28px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div
                style={{
                  width: '60px',
                  height: '60px',
                  borderRadius: '50%',
                  background: 'var(--postit-yellow)',
                  border: '2px solid var(--pencil-black)',
                  boxShadow: 'var(--shadow-hard-sm)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.8rem',
                  fontWeight: 700
                }}
              >
                {user?.full_name?.charAt(0) || 'U'}
              </div>
              <div>
                <h1 style={{ fontSize: '1.8rem', marginBottom: '2px' }}>
                  {user?.full_name || 'My Profile'}
                </h1>
                <p style={{ color: 'var(--pencil-subtle)', fontSize: '0.95rem' }}>
                  {user?.email}
                </p>
              </div>
            </div>

            <HandBadge variant="blue" style={{ fontSize: '1rem', padding: '6px 14px' }}>
              {primaryRole}
            </HandBadge>
          </div>

          {saveSuccess && (
            <div style={{ padding: '12px 16px', background: 'var(--postit-green)', border: '1.5px solid var(--pencil-black)', borderRadius: 'var(--wobbly-sm)', marginBottom: '20px', fontWeight: 700, color: 'var(--pencil-black)' }}>
              ✅ Profile updated successfully!
            </div>
          )}

          {error && (
            <div style={{ padding: '12px 16px', background: '#fee2e2', border: '1.5px solid var(--marker-red)', borderRadius: 'var(--wobbly-sm)', marginBottom: '20px', fontWeight: 700, color: 'var(--marker-red)' }}>
              ⚠️ {error}
            </div>
          )}

          <form onSubmit={handleSaveProfile} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div>
              <label style={{ display: 'block', fontWeight: 700, fontSize: '0.95rem', marginBottom: '6px', color: 'var(--pencil-black)' }}>
                Display Full Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="wobbly-input"
                style={{ width: '100%' }}
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: 700, fontSize: '0.95rem', marginBottom: '6px', color: 'var(--pencil-black)' }}>
                Email Address (Managed by Institution)
              </label>
              <input
                type="text"
                disabled
                value={user?.email || ''}
                className="wobbly-input"
                style={{ width: '100%', background: 'var(--pencil-muted)', cursor: 'not-allowed' }}
              />
              <span style={{ fontSize: '0.8rem', color: 'var(--pencil-subtle)', marginTop: '4px', display: 'block' }}>
                Protected attribute. Email cannot be modified directly.
              </span>
            </div>

            {/* Role Context Grid */}
            <div style={{ padding: '18px', background: 'var(--bg-paper)', borderRadius: 'var(--wobbly-sm)', border: '1.5px solid var(--pencil-black)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div>
                <span style={{ fontSize: '0.85rem', color: 'var(--pencil-subtle)', fontWeight: 700 }}>Organization Context:</span>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--pencil-black)', marginTop: '2px' }}>
                  District 101 Innovation
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.85rem', color: 'var(--pencil-subtle)', fontWeight: 700 }}>School Campus:</span>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--pencil-black)', marginTop: '2px' }}>
                  Oakridge Middle School
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
              <WobblyButton variant="red" disabled={saving} style={{ fontSize: '1.05rem', padding: '10px 24px' }}>
                {saving ? 'Saving...' : 'Save Profile Changes'}
              </WobblyButton>
            </div>
          </form>
        </WobblyCard>

        {/* Security Info Card */}
        <WobblyCard variant="purple" decoration="tape" tilt="left-sm" style={{ padding: '22px' }}>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '10px' }}>
            🔒 Security &amp; Data Privacy Invariants
          </h2>
          <ul style={{ paddingLeft: '20px', color: 'var(--pencil-black)', fontSize: '0.95rem', lineHeight: 1.6 }}>
            <li>Zero PII is shared with public LLMs or external models.</li>
            <li>Role elevation or organization override is strictly denied by PostgreSQL RLS.</li>
            <li>All student interaction sessions are logged with cryptographic audit hashes.</li>
          </ul>
        </WobblyCard>
      </div>
    </AuthenticatedShell>
  );
}
