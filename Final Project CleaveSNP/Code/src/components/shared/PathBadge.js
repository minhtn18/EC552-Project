import React from 'react';
import T from '../../styles/theme';

const COLOR_MAP = {
  Pathogenic: { bg: T.redBg, text: T.red, border: T.redBorder },
  'Likely Pathogenic': { bg: T.orangeBg, text: T.orange, border: T.orangeBorder },
  Benign: { bg: T.greenBg, text: T.green, border: T.greenBorder },
  Unknown: { bg: T.surfaceAlt, text: T.textMuted, border: T.border },
};

/**
 * Color-coded pathogenicity badge.
 */
export default function PathBadge({ value }) {
  const c = COLOR_MAP[value] || COLOR_MAP.Unknown;
  return (
    <span
      style={{
        padding: '4px 12px',
        borderRadius: 20,
        fontSize: 11,
        fontWeight: 600,
        background: c.bg,
        color: c.text,
        border: `1px solid ${c.border}`,
        letterSpacing: 0.3,
      }}
    >
      {value}
    </span>
  );
}
