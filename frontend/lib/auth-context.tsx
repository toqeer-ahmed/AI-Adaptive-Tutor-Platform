'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from './api-client';

export interface User {
  id: string;
  email: string;
  full_name: string;
  organization_id: string;
  school_id: string | null;
  roles: string[];
}

export type SupportedRole =
  | 'Student'
  | 'Teacher'
  | 'Parent'
  | 'SchoolAdmin'
  | 'OrgAdmin'
  | 'CurriculumManager'
  | 'SuperAdmin';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: str, rememberMe?: boolean) => Promise<{ success: boolean; error?: string }>;
  quickDemoLogin: (role: SupportedRole) => Promise<boolean>;
  logout: () => Promise<void>;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  primaryRole: SupportedRole;
  refreshSession: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const DEMO_CREDENTIALS: Record<SupportedRole, { email: string; pass: string; title: string; desc: string }> = {
  Student: {
    email: 'student@school.edu',
    pass: 'Pass123!',
    title: 'Alex Johnson (Student)',
    desc: 'Grade 6 Learner'
  },
  Teacher: {
    email: 'teacher@school.edu',
    pass: 'Pass123!',
    title: 'Mrs. Sarah Davis (Teacher)',
    desc: 'Grade 6 Math Educator'
  },
  Parent: {
    email: 'parent@family.com',
    pass: 'Pass123!',
    title: 'Michael Johnson (Parent)',
    desc: 'Parent of Alex'
  },
  SchoolAdmin: {
    email: 'schooladmin@school.edu',
    pass: 'Pass123!',
    title: 'Principal Vance (School Admin)',
    desc: 'Oakridge Middle School'
  },
  OrgAdmin: {
    email: 'orgadmin@district.edu',
    pass: 'Pass123!',
    title: 'Director Rostova (Org Admin)',
    desc: 'District 101 Innovation'
  },
  CurriculumManager: {
    email: 'curriculum@district.edu',
    pass: 'Pass123!',
    title: 'Dr. Marcus Chen (Curriculum)',
    desc: 'District Curriculum Lead'
  },
  SuperAdmin: {
    email: 'platformadmin@platform.com',
    pass: 'Pass123!',
    title: 'SysAdmin (Platform Admin)',
    desc: 'Platform Operations'
  }
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();

  const loadUserProfile = useCallback(async () => {
    try {
      const res = await apiClient.get<User>('/api/v1/auth/me');
      if (res.data) {
        setUser(res.data);
      } else {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
      }
    } catch (e) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (token) {
      loadUserProfile();
    } else {
      setIsLoading(false);
    }
  }, [loadUserProfile]);

  const login = async (
    email: string,
    password: string,
    rememberMe: boolean = true
  ): Promise<{ success: boolean; error?: string }> => {

    setIsLoading(true);
    try {
      const res = await apiClient.post<any>('/api/v1/auth/login', { email: email.trim().toLowerCase(), password });
      if (res.data && res.data.access_token) {
        localStorage.setItem('access_token', res.data.access_token);
        localStorage.setItem('refresh_token', res.data.refresh_token);
        setUser(res.data.user);
        setIsLoading(false);
        return { success: true };
      } else {
        setIsLoading(false);
        return {
          success: false,
          error: res.error?.message || 'Invalid email or password.'
        };
      }
    } catch (e: any) {
      setIsLoading(false);
      return {
        success: false,
        error: e.message || 'An error occurred during authentication.'
      };
    }
  };

  const quickDemoLogin = async (role: SupportedRole): Promise<boolean> => {
    const creds = DEMO_CREDENTIALS[role];
    if (!creds) return false;
    const result = await login(creds.email, creds.pass);
    return result.success;
  };

  const logout = async () => {
    try {
      await apiClient.post('/api/v1/auth/logout', {});
    } catch (e) {
      // Best effort logout
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      router.push('/login');
    }
  };

  const refreshSession = async (): Promise<boolean> => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return false;

    try {
      const res = await apiClient.post<any>('/api/v1/auth/refresh', { refresh_token: refreshToken });
      if (res.data && res.data.access_token) {
        localStorage.setItem('access_token', res.data.access_token);
        localStorage.setItem('refresh_token', res.data.refresh_token);
        await loadUserProfile();
        return true;
      }
    } catch (e) {
      logout();
    }
    return false;
  };

  const hasRole = (role: string): boolean => {
    if (!user || !user.roles) return false;
    return user.roles.includes(role);
  };

  const hasAnyRole = (roles: string[]): boolean => {
    if (!user || !user.roles) return false;
    return roles.some((r) => user.roles.includes(r));
  };

  const getPrimaryRole = (): SupportedRole => {
    if (!user || !user.roles || user.roles.length === 0) return 'Student';
    if (user.roles.includes('SuperAdmin')) return 'SuperAdmin';
    if (user.roles.includes('OrgAdmin')) return 'OrgAdmin';
    if (user.roles.includes('SchoolAdmin')) return 'SchoolAdmin';
    if (user.roles.includes('CurriculumManager') || user.roles.includes('ContentManager')) return 'CurriculumManager';
    if (user.roles.includes('Teacher')) return 'Teacher';
    if (user.roles.includes('Parent')) return 'Parent';
    return 'Student';
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        quickDemoLogin,
        logout,
        hasRole,
        hasAnyRole,
        primaryRole: getPrimaryRole(),
        refreshSession
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

