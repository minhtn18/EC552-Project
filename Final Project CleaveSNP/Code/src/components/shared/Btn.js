import React from 'react';
import T from '../../styles/theme';

/**
 * Reusable button with variant support.
 * Variants: 'primary' | 'secondary' | 'ghost' | 'danger'
 */
export default function Btn({ children, variant = 'primary', disabled, onClick, style = {} }) {
  const base = {
    padding: '10px 22px',
    borderRadius: 8,
    border: 'none',
    cursor: disabled ? 'not-allowed' : 'pointer',
    fontWeight: 600,
    fontSize: 14,
    fontFamily: T.body,
    transition: 'all 0.2s',
    opacity: disabled ? 0.4 : 1,
    ...style,
  };

  const variants = {
    primary: { ...base, background: T.accent, color: '#fff' },
    secondary: { ...base, background: T.surfaceAlt, color: T.textMuted, border: `1px solid ${T.border}` },
    ghost: { ...base, background: 'transparent', color: T.textMuted, border: `1px solid ${T.border}` },
    danger: { ...base, background: T.redBg, color: T.red, border: `1px solid ${T.redBorder}` },
  };

  return (
    <button onClick={disabled ? undefined : onClick} style={variants[variant] || variants.primary}>
      {children}
    </button>
  );
}
