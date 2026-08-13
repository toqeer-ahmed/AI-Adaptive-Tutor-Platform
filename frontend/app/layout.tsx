import './globals.css';
import React from 'react';
import { AuthProvider } from '@/lib/auth-context';

export const metadata = {
  title: 'AI Adaptive Education Platform',
  description: 'Production-grade AI Adaptive Learning System for Grades 4-8',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
