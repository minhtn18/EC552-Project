import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/shared';
import T from '../styles/theme';

const FEATURES = [
  { icon: '🔬', title: 'Database', desc: 'Browse and manage DNA sequences', path: '/database' },
  { icon: '🧪', title: 'Analysis', desc: 'Detect SNPs in patient sequences', path: '/analysis' },
  { icon: '📖', title: 'Instructions', desc: 'Learn how to use the platform', path: '/instructions' },
];

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="fade-in" style={{ textAlign: 'center', padding: '80px 24px 60px' }}>
      <div style={{ marginBottom: 12 }}>
        <div
          style={{
            width: 16, height: 16, background: T.accent,
            borderRadius: 3, transform: 'rotate(45deg)', margin: '0 auto 20px',
          }}
        />
        <h1
          style={{
            fontSize: 52, fontWeight: 800, color: T.accent,
            margin: 0, fontFamily: T.mono, letterSpacing: 4,
          }}
        >
          CLEAVE SNP
        </h1>
        <p
          style={{
            color: T.textMuted, fontSize: 17, margin: '12px auto 0',
            maxWidth: 480, lineHeight: 1.6, fontFamily: T.body,
          }}
        >
          Computational platform for detecting disease-causing SNPs and designing
          CRISPR-based genetic corrections
        </p>
      </div>

      <div
        style={{
          display: 'flex', gap: 16, maxWidth: 720,
          margin: '48px auto 0', justifyContent: 'center', flexWrap: 'wrap',
        }}
      >
        {FEATURES.map((f) => (
          <Card
            key={f.path}
            hoverable
            onClick={() => navigate(f.path)}
            style={{ flex: '1 1 200px', maxWidth: 220, textAlign: 'center', padding: '28px 20px' }}
          >
            <div style={{ fontSize: 32, marginBottom: 12 }}>{f.icon}</div>
            <div style={{ fontSize: 16, fontWeight: 700, color: T.text, marginBottom: 6 }}>
              {f.title}
            </div>
            <div style={{ fontSize: 13, color: T.textMuted, lineHeight: 1.5 }}>{f.desc}</div>
          </Card>
        ))}
      </div>

      <div style={{ marginTop: 48, color: T.textDim, fontSize: 12, fontFamily: T.body }}>
        EC552 — Computational Synthetic Biology — Boston University
      </div>
    </div>
  );
}
