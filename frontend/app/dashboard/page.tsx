'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

export default function DashboardRedirectPage() {
  const { user, isLoading, primaryRole } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (!user) {
        router.replace('/login');
      } else {
        switch (primaryRole) {
          case 'Teacher':
            router.replace('/teacher/dashboard');
            break;
          case 'Parent':
            router.replace('/parent/dashboard');
            break;
          case 'SchoolAdmin':
          case 'OrgAdmin':
          case 'SuperAdmin':
            router.replace('/admin/dashboard');
            break;
          case 'CurriculumManager':
            router.replace('/teacher/curriculum/review');
            break;
          case 'Student':
          default:
            router.replace('/student/dashboard');
            break;
        }
      }
    }
  }, [user, isLoading, primaryRole, router]);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-paper)' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>🧭</div>
        <div style={{ fontSize: '1.4rem', fontFamily: 'var(--font-heading)', color: 'var(--pencil-black)' }}>
          Routing to your authorized workspace...
        </div>
      </div>
    </div>
  );
}
