'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth, SupportedRole } from '@/lib/auth-context';
import { apiClient } from '@/lib/api-client';
import { HandBadge, WobblyButton } from '@/lib/HandDrawnComponents';

interface NotificationItem {
  id: string;
  title: string;
  body: string;
  is_read: boolean;
  created_at: string;
}

interface NavItem {
  label: string;
  href: string;
  icon: string;
  badge?: string;
}

export default function AuthenticatedShell({
  children,
  allowedRoles,
  title
}: {
  children: React.ReactNode;
  allowedRoles?: SupportedRole[];
  title?: string;
}) {
  const { user, isLoading, logout, primaryRole, hasRole } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [showNotifDropdown, setShowNotifDropdown] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  useEffect(() => {
    if (user) {
      fetchNotifications();
    }
  }, [user]);

  async function fetchNotifications() {
    try {
      const res = await apiClient.get<NotificationItem[]>('/api/v1/notifications');
      if (res.data) {
        setNotifications(res.data);
        setUnreadCount(res.data.filter((n) => !n.is_read).length);
      }
    } catch (e) {
      // Fallback
    }
  }

  async function markAsRead(id: string) {
    try {
      await apiClient.patch(`/api/v1/notifications/${id}/read`, {});
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (e) {
      // Ignore
    }
  }

  if (isLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-paper)' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>✏️</div>
          <div style={{ fontSize: '1.4rem', fontFamily: 'var(--font-heading)', color: 'var(--pencil-black)' }}>
            Loading your study desk...
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  // Role Gate
  if (allowedRoles && allowedRoles.length > 0 && !allowedRoles.some((r) => hasRole(r))) {
    return (
      <div style={{ minHeight: '100vh', padding: '60px 24px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-paper)' }}>
        <div
          style={{
            maxWidth: '550px',
            width: '100%',
            padding: '36px',
            background: 'var(--postit-yellow)',
            border: '2px solid var(--pencil-black)',
            borderRadius: 'var(--wobbly-card)',
            boxShadow: 'var(--shadow-hard)',
            textAlign: 'center'
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🚫</div>
          <h1 style={{ fontSize: '2rem', marginBottom: '12px', color: 'var(--pencil-black)' }}>
            Access Restricted (403)
          </h1>
          <p style={{ color: 'var(--pencil-subtle)', fontSize: '1.05rem', marginBottom: '24px', lineHeight: 1.5 }}>
            Your account ({user.email}) is assigned the <strong style={{ color: 'var(--pencil-black)' }}>{primaryRole}</strong> role and does not have permission to view this workspace.
          </p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <WobblyButton variant="blue" onClick={() => router.push('/dashboard')}>
              Go to My Dashboard
            </WobblyButton>
            <WobblyButton variant="red" onClick={logout}>
              Sign Out
            </WobblyButton>
          </div>
        </div>
      </div>
    );
  }

  // Build role-tailored sidebar menu
  const getNavItems = (): NavItem[] => {
    switch (primaryRole) {
      case 'Teacher':
        return [
          { label: 'Teaching Studio', href: '/teacher/dashboard', icon: '🍎' },
          { label: 'Curriculum Review', href: '/teacher/curriculum/review', icon: '📖' },
          { label: 'Question Bank', href: '/teacher/assessments', icon: '📝' },
          { label: 'Grading Desk', href: '/teacher/grading', icon: '✒️' },
          { label: 'AI Instructor', href: '/student/tutor', icon: '🤖' },
          { label: 'My Profile', href: '/profile', icon: '👤' },
        ];
      case 'Parent':
        return [
          { label: 'Family Dashboard', href: '/parent/dashboard', icon: '🏡' },
          { label: 'Learning Progress', href: '/parent/progress', icon: '📊' },
          { label: 'Assignments & Work', href: '/parent/assignments', icon: '📝' },
          { label: 'Notification Alerts', href: '/parent/settings', icon: '🔔' },
          { label: 'My Profile', href: '/profile', icon: '👤' },
        ];
      case 'SchoolAdmin':
      case 'OrgAdmin':
      case 'SuperAdmin':
        return [
          { label: 'Admin Command', href: '/admin/dashboard', icon: '⚡' },
          { label: 'Curriculum Studio', href: '/teacher/curriculum/review', icon: '📚' },
          { label: 'Teacher Studio', href: '/teacher/dashboard', icon: '🍎' },
          { label: 'Parent Digest', href: '/parent/dashboard', icon: '🏡' },
          { label: 'Student Learning', href: '/student/dashboard', icon: '🎒' },
          { label: 'My Profile', href: '/profile', icon: '👤' },
        ];
      case 'CurriculumManager':
        return [
          { label: 'Curriculum Review', href: '/teacher/curriculum/review', icon: '📖' },
          { label: 'Question Bank', href: '/teacher/assessments', icon: '📝' },
          { label: 'Textbook RAG', href: '/student/rag', icon: '🔍' },
          { label: 'My Profile', href: '/profile', icon: '👤' },
        ];
      case 'Student':
      default:
        return [
          { label: 'My Study Desk', href: '/student/dashboard', icon: '🎒' },
          { label: 'AI Socratic Tutor', href: '/student/tutor', icon: '🤖' },
          { label: 'Knowledge Map', href: '/student/mastery', icon: '📊' },
          { label: 'Adaptive Path', href: '/student/adaptive', icon: '🧭' },
          { label: 'Practice Quizzes', href: '/student/assessments', icon: '✏️' },
          { label: 'Textbook Search', href: '/student/rag', icon: '🔍' },
          { label: 'My Profile', href: '/profile', icon: '👤' },
        ];
    }
  };

  const navItems = getNavItems();

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-paper)' }}>
      {/* Hand-Drawn Sidebar */}
      <aside
        style={{
          width: '260px',
          background: '#ffffff',
          borderRight: '2px solid var(--pencil-black)',
          padding: '24px 16px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          flexShrink: 0
        }}
      >
        <div>
          {/* Logo / School Brand */}
          <Link href="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '28px', padding: '0 8px' }}>
            <span style={{ fontSize: '1.8rem' }}>📐</span>
            <div>
              <div style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem', fontWeight: 700, color: 'var(--pencil-black)' }}>
                Adaptive Tutor
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--pencil-subtle)', fontWeight: 600 }}>
                Oakridge Middle • Gr 4-8
              </div>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: 'var(--wobbly-sm)',
                    border: isActive ? '2px solid var(--pencil-black)' : '2px solid transparent',
                    background: isActive ? 'var(--postit-yellow)' : 'transparent',
                    boxShadow: isActive ? 'var(--shadow-hard-sm)' : 'none',
                    color: 'var(--pencil-black)',
                    textDecoration: 'none',
                    fontWeight: 700,
                    fontSize: '1rem',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span>{item.icon}</span>
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span style={{ fontSize: '0.75rem', padding: '2px 6px', background: 'var(--pencil-black)', color: '#ffffff', borderRadius: '10px' }}>
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Card & Logout in Footer */}
        <div
          style={{
            padding: '14px',
            background: 'var(--postit-green)',
            borderRadius: 'var(--wobbly-sm)',
            border: '2px solid var(--pencil-black)',
            boxShadow: 'var(--shadow-hard-sm)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: '#ffffff',
                border: '1.5px solid var(--pencil-black)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '1.1rem'
              }}
            >
              {user.full_name.charAt(0)}
            </div>
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--pencil-black)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                {user.full_name}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--pencil-subtle)', fontWeight: 600 }}>
                {primaryRole}
              </div>
            </div>
          </div>
          <button
            onClick={logout}
            style={{
              width: '100%',
              padding: '6px',
              background: '#ffffff',
              border: '1.5px solid var(--pencil-black)',
              borderRadius: 'var(--wobbly-sm)',
              fontFamily: 'var(--font-heading)',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: 'pointer',
              color: 'var(--marker-red)'
            }}
          >
            🚪 Sign Out
          </button>
        </div>
      </aside>

      {/* Main Viewport */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Top Header */}
        <header
          style={{
            height: '64px',
            background: '#ffffff',
            borderBottom: '2px solid var(--pencil-black)',
            padding: '0 28px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <div>
            <span style={{ fontFamily: 'var(--font-heading)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--pencil-black)' }}>
              {title || 'Oakridge Learning Studio'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <HandBadge variant="blue">
              Role: {primaryRole}
            </HandBadge>

            {/* Notifications Bell */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setShowNotifDropdown(!showNotifDropdown)}
                style={{
                  background: '#ffffff',
                  border: '1.5px solid var(--pencil-black)',
                  borderRadius: '50%',
                  width: '38px',
                  height: '38px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  fontSize: '1.1rem',
                  position: 'relative'
                }}
              >
                🔔
                {unreadCount > 0 && (
                  <span
                    style={{
                      position: 'absolute',
                      top: '-4px',
                      right: '-4px',
                      background: 'var(--marker-red)',
                      color: '#ffffff',
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      borderRadius: '50%',
                      width: '18px',
                      height: '18px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: '1px solid #ffffff'
                    }}
                  >
                    {unreadCount}
                  </span>
                )}
              </button>

              {/* Dropdown Menu */}
              {showNotifDropdown && (
                <div
                  style={{
                    position: 'absolute',
                    top: '48px',
                    right: '0',
                    width: '320px',
                    background: '#ffffff',
                    border: '2px solid var(--pencil-black)',
                    borderRadius: 'var(--wobbly-sm)',
                    boxShadow: 'var(--shadow-hard)',
                    zIndex: 100,
                    padding: '12px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', paddingBottom: '6px', borderBottom: '1px solid var(--pencil-muted)' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Notifications</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--pencil-subtle)' }}>{unreadCount} unread</span>
                  </div>

                  {notifications.length === 0 ? (
                    <div style={{ padding: '16px 0', textAlign: 'center', color: 'var(--pencil-subtle)', fontSize: '0.9rem' }}>
                      No notifications yet 📭
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '240px', overflowY: 'auto' }}>
                      {notifications.slice(0, 5).map((n) => (
                        <div
                          key={n.id}
                          onClick={() => markAsRead(n.id)}
                          style={{
                            padding: '8px 10px',
                            background: n.is_read ? 'transparent' : 'var(--postit-yellow)',
                            borderRadius: '4px',
                            border: '1px solid var(--pencil-muted)',
                            cursor: 'pointer'
                          }}
                        >
                          <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--pencil-black)' }}>
                            {n.title}
                          </div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--pencil-subtle)', marginTop: '2px' }}>
                            {n.body}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Dynamic Content */}
        <main style={{ flex: 1, overflowY: 'auto' }}>
          {children}
        </main>
      </div>
    </div>
  );
}
