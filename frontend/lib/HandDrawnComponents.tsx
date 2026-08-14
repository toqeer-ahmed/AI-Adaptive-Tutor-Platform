'use client';

import React from 'react';
import Link from 'next/link';

export interface WobblyCardProps {
  children: React.ReactNode;
  variant?: 'white' | 'yellow' | 'green' | 'purple' | 'cyan' | 'orange';
  decoration?: 'tape' | 'tack-red' | 'tack-blue' | 'tack-yellow' | 'none';
  tilt?: 'left' | 'right' | 'left-sm' | 'right-sm' | 'none';
  className?: string;
  style?: React.CSSProperties;
}

export function WobblyCard({
  children,
  variant = 'white',
  decoration = 'none',
  tilt = 'none',
  className = '',
  style = {}
}: WobblyCardProps) {
  let bgClass = 'wobbly-box';
  if (variant === 'yellow') bgClass = 'postit-yellow';
  else if (variant === 'green') bgClass = 'postit-green';
  else if (variant === 'purple') bgClass = 'postit-purple';
  else if (variant === 'cyan') bgClass = 'postit-cyan';
  else if (variant === 'orange') bgClass = 'postit-orange';

  let tiltClass = '';
  if (tilt === 'left') tiltClass = 'tilt-left';
  else if (tilt === 'right') tiltClass = 'tilt-right';
  else if (tilt === 'left-sm') tiltClass = 'tilt-left-sm';
  else if (tilt === 'right-sm') tiltClass = 'tilt-right-sm';

  return (
    <div
      className={`${bgClass} ${tiltClass} ${className}`}
      style={{
        padding: '24px',
        position: 'relative',
        ...style
      }}
    >
      {decoration === 'tape' && <div className="tape-strip" />}
      {decoration === 'tack-red' && <div className="thumbtack-pin" />}
      {decoration === 'tack-blue' && <div className="thumbtack-pin blue" />}
      {decoration === 'tack-yellow' && <div className="thumbtack-pin yellow" />}
      {children}
    </div>
  );
}

export interface WobblyButtonProps {
  children: React.ReactNode;
  href?: string;
  onClick?: () => void;
  variant?: 'red' | 'blue' | 'secondary';
  disabled?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export function WobblyButton({
  children,
  href,
  onClick,
  variant = 'red',
  disabled = false,
  className = '',
  style = {}
}: WobblyButtonProps) {
  let btnClass = 'wobbly-btn';
  if (variant === 'blue') btnClass = 'wobbly-btn wobbly-btn-blue';
  else if (variant === 'secondary') btnClass = 'wobbly-btn wobbly-btn-secondary';

  if (href) {
    return (
      <Link href={href} className={`${btnClass} ${className}`} style={style}>
        {children}
      </Link>
    );
  }

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${btnClass} ${className}`}
      style={{ opacity: disabled ? 0.6 : 1, ...style }}
    >
      {children}
    </button>
  );
}

export function HandBadge({
  children,
  variant = 'yellow',
  className = '',
  style = {}
}: {
  children: React.ReactNode;
  variant?: 'red' | 'blue' | 'green' | 'yellow' | 'purple';
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <span className={`hand-badge hand-badge-${variant} ${className}`} style={style}>
      {children}
    </span>
  );
}

export function ScribbleUnderline() {
  return (
    <svg
      width="100%"
      height="12"
      viewBox="0 0 200 12"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ display: 'block', margin: '4px auto 0' }}
    >
      <path
        d="M2 9.5C45 3.5 155 2 198 8.5C140 10.5 60 11 35 10"
        stroke="#ff4d4d"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function HandDrawnArrow() {
  return (
    <svg
      width="60"
      height="45"
      viewBox="0 0 60 45"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ display: 'inline-block' }}
    >
      <path
        d="M5 25C18 10 38 8 52 22M52 22L42 16M52 22L46 30"
        stroke="#2d5da1"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
