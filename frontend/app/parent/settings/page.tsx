'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import AuthenticatedShell from '@/components/AuthenticatedShell';
import { apiClient } from '@/lib/api-client';
import {
  WobblyCard,
  HandBadge,
  WobblyButton
} from '@/lib/HandDrawnComponents';

interface NotificationSettings {
  email_enabled: boolean;
  in_app_enabled: boolean;
  push_enabled: boolean;
  digest_frequency: string;
  assignment_reminders: boolean;
  teacher_feedback_alerts: boolean;
}

export default function ParentSettingsPage() {
  const [settings, setSettings] = useState<NotificationSettings>({
    email_enabled: true,
    in_app_enabled: true,
    push_enabled: false,
    digest_frequency: 'DAILY',
    assignment_reminders: true,
    teacher_feedback_alerts: true
  });
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  async function fetchSettings() {
    try {
      const res = await apiClient.get<NotificationSettings>('/api/v1/parents/notifications/settings');
      if (res.data) {
        setSettings(res.data);
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function handleSave() {
    setSaving(true);
    setSaveSuccess(false);
    try {
      await apiClient.put('/api/v1/parents/notifications/settings', {
        email_enabled: settings.email_enabled,
        in_app_enabled: settings.in_app_enabled,
        push_enabled: settings.push_enabled,
        digest_frequency: settings.digest_frequency
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  }

  return (
    <AuthenticatedShell allowedRoles={['Parent', 'OrgAdmin', 'SchoolAdmin', 'SuperAdmin']} title="Family Notification Settings">
      <div style={{ padding: '28px 32px 60px', maxWidth: '880px', margin: '0 auto' }}>
        
        {/* Header Card */}
        <WobblyCard decoration="tape" style={{ padding: '26px 30px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <span style={{ fontSize: '2rem' }}>🔔</span>
              <h1 style={{ fontSize: '2.1rem', margin: 0 }}>Family Digest & Alert Settings</h1>
            </div>
            <p style={{ color: 'var(--pencil-subtle)', fontSize: '1.05rem', margin: 0 }}>
              Customize how and when you receive homework updates and teacher notes without notification overload.
            </p>
          </div>
          <Link href="/parent/dashboard">
            <WobblyButton variant="neutral">&larr; Back to Dashboard</WobblyButton>
          </Link>
        </WobblyCard>

        {saveSuccess && (
          <div
            style={{
              padding: '14px 20px',
              background: 'var(--postit-green)',
              borderRadius: 'var(--wobbly-sm)',
              border: '2px solid var(--pencil-black)',
              fontWeight: 800,
              color: 'var(--pencil-black)',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}
          >
            <span>✅</span> Notification preferences saved successfully!
          </div>
        )}

        {/* Digest Frequency Settings */}
        <WobblyCard style={{ padding: '24px', marginBottom: '24px', background: '#ffffff' }}>
          <h2 style={{ fontSize: '1.3rem', margin: '0 0 14px 0' }}>📬 Learning Summary Digest Frequency</h2>
          <p style={{ fontSize: '0.9rem', color: 'var(--pencil-subtle)', marginBottom: '18px' }}>
            We bundle homework progress and quiz completions into a friendly growth summary to respect your family inbox.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[
              { key: 'DAILY', title: 'Daily Evening Digest (Recommended)', desc: 'Sent at 6:00 PM on school days with daily accomplishments.' },
              { key: 'WEEKLY', title: 'Weekly Family Summary', desc: 'Sent Friday afternoon with a weekly mastery overview & streak celebration.' },
              { key: 'IMMEDIATE', title: 'Immediate Notifications', desc: 'Receive real-time alerts as soon as an assignment or note is published.' }
            ].map((opt) => (
              <label
                key={opt.key}
                style={{
                  padding: '14px 18px',
                  background: settings.digest_frequency === opt.key ? 'var(--postit-cyan)' : 'var(--bg-paper)',
                  borderRadius: 'var(--wobbly-sm)',
                  border: '1.5px solid var(--pencil-black)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  cursor: 'pointer'
                }}
              >
                <input
                  type="radio"
                  name="digest_freq"
                  checked={settings.digest_frequency === opt.key}
                  onChange={() => setSettings(s => ({ ...s, digest_frequency: opt.key }))}
                  style={{ marginTop: '4px', cursor: 'pointer' }}
                />
                <div>
                  <div style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--pencil-black)' }}>{opt.title}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--pencil-subtle)', marginTop: '2px' }}>{opt.desc}</div>
                </div>
              </label>
            ))}
          </div>
        </WobblyCard>

        {/* Communication Channels */}
        <WobblyCard style={{ padding: '24px', marginBottom: '24px', background: '#ffffff' }}>
          <h2 style={{ fontSize: '1.3rem', margin: '0 0 14px 0' }}>📡 Communication Channels</h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', padding: '12px 16px', background: 'var(--bg-paper)', borderRadius: 'var(--wobbly-sm)', border: '1.5px solid var(--pencil-black)' }}>
              <div>
                <div style={{ fontWeight: 800, color: 'var(--pencil-black)' }}>📧 Email Digests</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--pencil-subtle)' }}>Receive learning reports via verified parent email.</div>
              </div>
              <input
                type="checkbox"
                checked={settings.email_enabled}
                onChange={(e) => setSettings(s => ({ ...s, email_enabled: e.target.checked }))}
                style={{ width: '20px', height: '20px', cursor: 'pointer' }}
              />
            </label>

            <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', padding: '12px 16px', background: 'var(--bg-paper)', borderRadius: 'var(--wobbly-sm)', border: '1.5px solid var(--pencil-black)' }}>
              <div>
                <div style={{ fontWeight: 800, color: 'var(--pencil-black)' }}>🔔 In-App Portal Alerts</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--pencil-subtle)' }}>Show notification badges in your family header bar.</div>
              </div>
              <input
                type="checkbox"
                checked={settings.in_app_enabled}
                onChange={(e) => setSettings(s => ({ ...s, in_app_enabled: e.target.checked }))}
                style={{ width: '20px', height: '20px', cursor: 'pointer' }}
              />
            </label>
          </div>
        </WobblyCard>

        {/* Save Preferences Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <WobblyButton variant="green" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save Notification Preferences 💾'}
          </WobblyButton>
        </div>

      </div>
    </AuthenticatedShell>
  );
}
