import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Btn, Card, PageShell, PageHeader } from '../components/shared';
import T from '../styles/theme';

const BASE_COLOR = { A: '#22cc66', T: '#ff4455', G: '#ffaa33', C: '#4488ee' };

const LEGEND = [
  { bg: '#22cc6633', border: '#22cc66', label: 'gRNA binding' },
  { bg: '#ffaa3333', border: '#ffaa33', label: 'PAM site' },
  { bg: T.redBg, border: T.red, label: 'SNP position' },
  { bg: 'transparent', border: T.red, label: '✂ Cut site' },
];

export default function BindingViewPage() {
  const navigate = useNavigate();
  const { bindingSiteData, selectedGRNA, selectedSNP } = useApp();

  const [zoom, setZoom] = useState(1);
  const [panX, setPanX] = useState(0);
  const [dragging, setDragging] = useState(false);
  const [dragStart, setDragStart] = useState(0);

  // Guard
  if (!bindingSiteData || !selectedGRNA) {
    navigate('/results/crispr', { replace: true });
    return null;
  }

  const {
    referenceWindow, startPosition, grnaBindStart, grnaBindEnd,
    pamStart, pamEnd, snpPositionInWindow, cutSitePosition, complementaryStrand,
  } = bindingSiteData;

  const bases = referenceWindow.split('');
  const comp = complementaryStrand.split('');
  const bw = 18 * zoom;
  const viewW = 860;

  const onWheel = useCallback((e) => {
    e.preventDefault();
    setZoom((z) => Math.max(0.3, Math.min(4, z + (e.deltaY > 0 ? -0.15 : 0.15))));
  }, []);

  return (
    <PageShell maxWidth={1000}>
      <PageHeader
        title="Genome Binding Site"
        subtitle={
          <span>
            gRNA: <span style={{ fontFamily: T.mono, color: T.green }}>{selectedGRNA.sequence}</span>
            {' '}· Scroll to zoom, drag to pan
          </span>
        }
        actions={
          <div style={{ display: 'flex', gap: 8 }}>
            <Btn onClick={() => navigate('/results/edit')}>View Full Results →</Btn>
            <Btn variant="ghost" onClick={() => navigate('/results/crispr')}>← Back to gRNAs</Btn>
          </div>
        }
      />

      {/* Legend */}
      <div style={{ display: 'flex', gap: 24, marginBottom: 16, fontSize: 12, color: T.textMuted, flexWrap: 'wrap' }}>
        {LEGEND.map(({ bg, border, label }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 14, height: 14, background: bg, border: `1px solid ${border}`, borderRadius: 3 }} />
            <span>{label}</span>
          </div>
        ))}
      </div>

      {/* SVG Viewer */}
      <Card style={{ padding: 0, overflow: 'hidden' }}>
        <div
          style={{ cursor: dragging ? 'grabbing' : 'grab', userSelect: 'none', overflow: 'hidden' }}
          onWheel={onWheel}
          onMouseDown={(e) => { setDragging(true); setDragStart(e.clientX - panX); }}
          onMouseMove={(e) => { if (dragging) setPanX(e.clientX - dragStart); }}
          onMouseUp={() => setDragging(false)}
          onMouseLeave={() => setDragging(false)}
        >
          <svg
            width={viewW}
            height={180}
            viewBox={`${-panX} 0 ${viewW} 180`}
            style={{ display: 'block', width: '100%', height: 'auto' }}
          >
            {/* Position labels */}
            {bases.map((_, i) => {
              if (i % Math.max(1, Math.floor(5 / zoom)) !== 0) return null;
              return (
                <text key={i} x={i * bw + bw / 2} y={18} textAnchor="middle" fill={T.textDim} fontSize={Math.min(10, 8 * zoom)} fontFamily="monospace">
                  {startPosition + i}
                </text>
              );
            })}

            {/* gRNA highlight */}
            <rect x={(grnaBindStart - 1) * bw} y={24} width={(grnaBindEnd - grnaBindStart + 1) * bw} height={56} fill="rgba(34,204,102,0.08)" stroke={T.green} strokeWidth={1} rx={4} />

            {/* PAM highlight */}
            <rect x={(pamStart - 1) * bw} y={24} width={(pamEnd - pamStart + 1) * bw} height={56} fill="rgba(255,170,51,0.12)" stroke={T.orange} strokeWidth={1} rx={4} />

            {/* Top strand */}
            {bases.map((b, i) => (
              <g key={`t${i}`}>
                <rect x={i * bw} y={28} width={bw - 1} height={22} fill={BASE_COLOR[b] || '#666'} opacity={0.12} rx={2} />
                {zoom > 0.5 && (
                  <text x={i * bw + bw / 2} y={44} textAnchor="middle" fill={BASE_COLOR[b]} fontSize={Math.min(13, 11 * zoom)} fontFamily="monospace" fontWeight={600}>
                    {b}
                  </text>
                )}
              </g>
            ))}

            {/* Strand separator */}
            <line x1={0} y1={55} x2={bases.length * bw} y2={55} stroke={T.border} strokeWidth={0.5} />

            {/* Bottom strand */}
            {comp.map((b, i) => (
              <g key={`b${i}`}>
                <rect x={i * bw} y={58} width={bw - 1} height={22} fill={BASE_COLOR[b] || '#666'} opacity={0.06} rx={2} />
                {zoom > 0.5 && (
                  <text x={i * bw + bw / 2} y={74} textAnchor="middle" fill={BASE_COLOR[b]} fontSize={Math.min(13, 11 * zoom)} fontFamily="monospace" opacity={0.5}>
                    {b}
                  </text>
                )}
              </g>
            ))}

            {/* SNP marker */}
            <polygon
              points={`${(snpPositionInWindow - 1) * bw + bw / 2},22 ${(snpPositionInWindow - 1) * bw + bw / 2 - 5},14 ${(snpPositionInWindow - 1) * bw + bw / 2 + 5},14`}
              fill={T.red}
            />
            <text x={(snpPositionInWindow - 1) * bw + bw / 2} y={10} textAnchor="middle" fill={T.red} fontSize={8} fontWeight={700} fontFamily="monospace">SNP</text>

            {/* Cut site */}
            <line x1={(cutSitePosition - 1) * bw + bw / 2} y1={24} x2={(cutSitePosition - 1) * bw + bw / 2} y2={86} stroke={T.red} strokeWidth={1.5} strokeDasharray="4,3" />
            <text x={(cutSitePosition - 1) * bw + bw / 2} y={98} textAnchor="middle" fill={T.red} fontSize={11}>✂</text>

            {/* Direction arrow */}
            <text x={grnaBindEnd * bw + 6} y={106} fill={T.green} fontSize={10} fontWeight={600} fontFamily="monospace">
              {selectedGRNA.strand === 'sense' ? '→ 5′ to 3′' : '← 3′ to 5′'}
            </text>
          </svg>
        </div>
      </Card>

      {/* Zoom controls */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 10, marginTop: 14 }}>
        <Btn variant="ghost" onClick={() => setZoom((z) => Math.max(0.3, z - 0.3))} style={{ width: 36, height: 36, padding: 0, fontSize: 18, textAlign: 'center' }}>−</Btn>
        <span style={{ color: T.textMuted, fontSize: 13, lineHeight: '36px', minWidth: 50, textAlign: 'center' }}>
          {Math.round(zoom * 100)}%
        </span>
        <Btn variant="ghost" onClick={() => setZoom((z) => Math.min(4, z + 0.3))} style={{ width: 36, height: 36, padding: 0, fontSize: 18, textAlign: 'center' }}>+</Btn>
        <Btn variant="ghost" onClick={() => { setZoom(1); setPanX(0); }} style={{ fontSize: 12 }}>Reset</Btn>
      </div>
    </PageShell>
  );
}
