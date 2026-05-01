import React from 'react';
import T from '../../styles/theme';

/**
 * Page-level container with max-width and padding.
 */
export function PageShell({ children, maxWidth = 960 }) {
  return (
    <div className="fade-in" style={{ maxWidth, margin: '0 auto', padding: '40px 24px' }}>
      {children}
    </div>
  );
}

/**
 * Consistent page header with title, subtitle, and optional action buttons.
 */
export function PageHeader({ title, subtitle, actions }) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 32,
        flexWrap: 'wrap',
        gap: 16,
      }}
    >
      <div>
        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 700, color: T.text, fontFamily: T.display }}>
          {title}
        </h1>
        {subtitle && (
          <p style={{ margin: '6px 0 0', color: T.textMuted, fontSize: 14 }}>{subtitle}</p>
        )}
      </div>
      {actions && <div style={{ display: 'flex', gap: 8 }}>{actions}</div>}
    </div>
  );
}

/**
 * Loading spinner with text.
 */
export function Spinner({ text = 'Processing...' }) {
  return (
    <div style={{ textAlign: 'center', padding: '80px 24px' }}>
      <div
        style={{
          width: 48,
          height: 48,
          border: `3px solid ${T.border}`,
          borderTopColor: T.accent,
          borderRadius: '50%',
          margin: '0 auto 20px',
          animation: 'cleaveSpin 0.8s linear infinite',
        }}
      />
      <p style={{ color: T.textMuted, fontSize: 15 }}>{text}</p>
    </div>
  );
}
