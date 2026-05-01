import React, { useState } from 'react';
import T from '../../styles/theme';

/**
 * Reusable card container with optional hover effects.
 */
export default function Card({ children, style = {}, onClick, hoverable }) {
  const [hov, setHov] = useState(false);

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => hoverable && setHov(true)}
      onMouseLeave={() => hoverable && setHov(false)}
      style={{
        background: T.card,
        borderRadius: 10,
        border: `1px solid ${hov ? T.borderHover : T.border}`,
        padding: 20,
        transition: 'all 0.2s',
        cursor: onClick ? 'pointer' : 'default',
        transform: hov ? 'translateY(-2px)' : 'none',
        boxShadow: hov ? `0 8px 24px ${T.accentGlow}` : 'none',
        ...style,
      }}
    >
      {children}
    </div>
  );
}
