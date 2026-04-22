import React from 'react';
import { NavLink } from 'react-router-dom';
import T from '../styles/theme';

const NAV_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/database', label: 'Database' },
  { to: '/analysis', label: 'Analysis' },
  { to: '/instructions', label: 'Instructions' },
  { to: '/settings', label: 'Settings' },
];

export default function Navbar() {
  return (
    <nav
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '0 28px',
        height: 56,
        background: T.surface,
        borderBottom: `1px solid ${T.border}`,
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      {/* Logo */}
      <NavLink to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 8 }}>
        <div
          style={{
            width: 8,
            height: 8,
            background: T.accent,
            borderRadius: 2,
            transform: 'rotate(45deg)',
          }}
        />
        <span
          style={{
            fontSize: 17,
            fontWeight: 800,
            color: T.accent,
            fontFamily: T.mono,
            letterSpacing: 2,
          }}
        >
          CLEAVE SNP
        </span>
      </NavLink>

      {/* Nav links */}
      <div style={{ display: 'flex', gap: 4 }}>
        {NAV_LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            style={({ isActive }) => ({
              padding: '8px 18px',
              borderRadius: 6,
              border: 'none',
              textDecoration: 'none',
              background: isActive ? T.accentGlow : 'transparent',
              color: isActive ? T.accent : T.textMuted,
              fontSize: 13,
              fontWeight: isActive ? 700 : 500,
              fontFamily: T.body,
              transition: 'all 0.2s',
            })}
          >
            {link.label}
          </NavLink>
        ))}
      </div>

      {/* Spacer for balance */}
      <div style={{ width: 120 }} />
    </nav>
  );
}
