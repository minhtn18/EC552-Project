import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Btn, Card, PathBadge, PageShell, PageHeader, Spinner } from '../components/shared';
import { USE_MOCK } from '../data/config';
import { MOCK_GRNAS, MOCK_BINDING } from '../data/mockData';
import api from '../services/api';
import T from '../styles/theme';

export default function CRISPRDesignPage() {
  const navigate = useNavigate();
  const {
    selectedSNP, grnaCacheMap, snpResults, setSelectedSNP,
    setSelectedGRNA, setBindingSiteData, inputSequence,
    setGrnaCacheMap,
  } = useApp();

  const [sortKey, setSortKey] = useState('score');
  const [sortDir, setSortDir] = useState('desc');
  const [loading, setLoading] = useState(false);

  // Refinement modal state
  const [refiningGRNA, setRefiningGRNA] = useState(null);
  const [refineLength, setRefineLength] = useState(20);
  const [refineLoading, setRefineLoading] = useState(false);
  const [refinedResult, setRefinedResult] = useState(null);

  // Guard
  if (!selectedSNP || !grnaCacheMap.has(selectedSNP.snpNo)) {
    navigate('/results/snps', { replace: true });
    return null;
  }

  const grnas = grnaCacheMap.get(selectedSNP.snpNo) || [];
  const sorted = [...grnas].sort((a, b) =>
    sortDir === 'desc' ? b[sortKey] - a[sortKey] : a[sortKey] - b[sortKey]
  );

  const handleSort = (key) => {
    if (sortKey === key) setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'));
    else { setSortKey(key); setSortDir('desc'); }
  };

  const handleGRNAClick = async (grna) => {
    setSelectedGRNA(grna);
    setLoading(true);
    try {
      let binding;
      if (USE_MOCK) {
        await new Promise((r) => setTimeout(r, 500));
        binding = MOCK_BINDING;
      } else {
        binding = await api.getBindingSite(grna, selectedSNP, 100);
      }
      setBindingSiteData(binding);
      navigate('/results/binding');
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSNPSwitch = async (snp) => {
    setSelectedSNP(snp);
    if (grnaCacheMap.has(snp.snpNo)) return;

    setLoading(true);
    try {
      let g;
      if (USE_MOCK) {
        await new Promise((r) => setTimeout(r, 800));
        g = MOCK_GRNAS;
      } else {
        const res = await api.crisprDesign(snp, inputSequence, 50);
        g = res.grnaCandidates;
      }
      setGrnaCacheMap((prev) => new Map(prev).set(snp.snpNo, g));
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefine = async () => {
    if (!refiningGRNA) return;
    setRefineLoading(true);
    try {
      let result;
      if (USE_MOCK) {
        await new Promise((r) => setTimeout(r, 600));
        result = {
          refinedGRNA: {
            ...refiningGRNA,
            score: Math.min(1, refiningGRNA.score + 0.05 * (refineLength - refiningGRNA.sequence.length)),
            offTargetCount: Math.max(0, refiningGRNA.offTargetCount - 2),
          },
          previousScore: refiningGRNA.score,
          improvement: 0.05,
        };
      } else {
        result = await api.refineGrna(
          refiningGRNA.sequence, refineLength, selectedSNP.position, inputSequence
        );
      }
      setRefinedResult(result);
      // Update cache
      setGrnaCacheMap((prev) => {
        const newMap = new Map(prev);
        const list = newMap.get(selectedSNP.snpNo) || [];
        newMap.set(
          selectedSNP.snpNo,
          list.map((g) => (g.id === refiningGRNA.id ? result.refinedGRNA : g))
        );
        return newMap;
      });
    } catch (err) {
      alert(err.message);
    } finally {
      setRefineLoading(false);
    }
  };

  const SortTh = ({ label, field }) => (
    <th
      onClick={() => handleSort(field)}
      style={{
        padding: '14px 10px', textAlign: 'center', fontSize: 11, fontWeight: 700,
        color: sortKey === field ? T.accent : T.textDim, textTransform: 'uppercase',
        letterSpacing: 0.5, cursor: 'pointer', userSelect: 'none',
        borderBottom: `1px solid ${T.border}`, fontFamily: T.body,
      }}
    >
      {label} {sortKey === field ? (sortDir === 'desc' ? '↓' : '↑') : ''}
    </th>
  );

  return (
    <PageShell maxWidth={1100}>
      {loading && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Spinner />
        </div>
      )}

      <PageHeader
        title="CRISPR Edit Design"
        subtitle="Click a gRNA row to view binding site — or refine high off-target guides"
        actions={<Btn variant="ghost" onClick={() => navigate('/results/snps')}>← Back to SNPs</Btn>}
      />

      {/* SNP summary bar */}
      <Card style={{ display: 'flex', gap: 24, alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', padding: '16px 20px' }}>
        {[
          { label: 'Gene', value: selectedSNP.gene },
          { label: 'Position', value: selectedSNP.position, mono: true },
          { label: 'Mutation', custom: (
            <span style={{ fontFamily: T.mono }}>
              <span style={{ color: T.green }}>{selectedSNP.refNucleotide}</span>
              <span style={{ color: T.textDim }}> → </span>
              <span style={{ color: T.red }}>{selectedSNP.varNucleotide}</span>
            </span>
          )},
          { label: 'Disease', value: selectedSNP.disease },
        ].map((item, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <span style={{ fontSize: 10, color: T.textDim, textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5 }}>{item.label}</span>
            {item.custom || <span style={{ fontSize: 15, color: T.text, fontWeight: 600, fontFamily: item.mono ? T.mono : T.body }}>{item.value}</span>}
          </div>
        ))}
        <PathBadge value={selectedSNP.pathogenicity} />
        {snpResults && snpResults.length > 1 && (
          <select
            value={selectedSNP.snpNo}
            onChange={(e) => {
              const s = snpResults.find((x) => x.snpNo === Number(e.target.value));
              if (s) handleSNPSwitch(s);
            }}
            style={{
              marginLeft: 'auto', padding: '6px 10px', background: T.bg,
              border: `1px solid ${T.border}`, borderRadius: 6, color: T.text,
              fontSize: 12, cursor: 'pointer', fontFamily: T.body,
            }}
          >
            {snpResults.map((s) => (
              <option key={s.snpNo} value={s.snpNo}>SNP #{s.snpNo} — {s.disease}</option>
            ))}
          </select>
        )}
      </Card>

      {/* gRNA table */}
      <Card style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: T.surfaceAlt }}>
              <th style={{ padding: '14px 10px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: T.textDim, textTransform: 'uppercase', borderBottom: `1px solid ${T.border}`, fontFamily: T.body }}>gRNA Sequence</th>
              <SortTh label="Cut Dist" field="cutSiteDistance" />
              <SortTh label="GC %" field="gcContent" />
              <SortTh label="Homo" field="homopolymerPenalty" />
              <SortTh label="Off-Tgt" field="offTargetCount" />
              <SortTh label="Score" field="score" />
              <th style={{ padding: '14px 10px', textAlign: 'center', fontSize: 11, fontWeight: 700, color: T.textDim, textTransform: 'uppercase', borderBottom: `1px solid ${T.border}`, fontFamily: T.body }}>Type</th>
              <th style={{ padding: '14px 10px', textAlign: 'center', fontSize: 11, fontWeight: 700, color: T.textDim, textTransform: 'uppercase', borderBottom: `1px solid ${T.border}`, fontFamily: T.body }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((g, i) => {
              const isTop = i === 0 && sortKey === 'score' && sortDir === 'desc';
              return (
                <tr
                  key={g.id}
                  onClick={() => handleGRNAClick(g)}
                  style={{
                    cursor: 'pointer', transition: 'background 0.15s',
                    borderLeft: isTop ? `3px solid ${T.accent}` : '3px solid transparent',
                    borderBottom: `1px solid ${T.border}11`,
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = T.accentGlow; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                >
                  <td style={{ padding: '12px 10px', fontFamily: T.mono, fontSize: 12, color: T.green, letterSpacing: 1.2 }}>{g.sequence}</td>
                  <td style={{ padding: '12px 10px', color: T.text, textAlign: 'center', fontSize: 13 }}>{g.cutSiteDistance} nt</td>
                  <td style={{ padding: '12px 10px', color: g.gcContent >= 40 && g.gcContent <= 65 ? T.green : T.orange, textAlign: 'center', fontSize: 13 }}>{g.gcContent}%</td>
                  <td style={{ padding: '12px 10px', color: g.homopolymerPenalty > 0 ? T.orange : T.green, textAlign: 'center', fontSize: 13 }}>{g.homopolymerPenalty}</td>
                  <td style={{ padding: '12px 10px', textAlign: 'center', fontSize: 13 }}>
                    <span style={{ color: g.offTargetCount > 5 ? T.red : g.offTargetCount > 2 ? T.orange : T.green, fontWeight: 600 }}>{g.offTargetCount}</span>
                    {g.offTargetCount > 5 && ' ⚠️'}
                  </td>
                  <td style={{ padding: '12px 10px', textAlign: 'center', fontWeight: 700, fontSize: 16, color: g.score >= 0.8 ? T.green : g.score >= 0.6 ? T.orange : T.red }}>{g.score.toFixed(2)}</td>
                  <td style={{ padding: '12px 10px', textAlign: 'center' }}>
                    <span style={{ padding: '3px 10px', borderRadius: 12, fontSize: 11, fontWeight: 600, background: g.editType === 'Base Edit' ? T.greenBg : T.blueBg, color: g.editType === 'Base Edit' ? T.green : T.blue, border: `1px solid ${g.editType === 'Base Edit' ? T.greenBorder : T.blueBorder}` }}>{g.editType}</span>
                  </td>
                  <td style={{ padding: '12px 10px', textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                    {g.offTargetCount > 3 && (
                      <Btn variant="ghost" onClick={() => { setRefiningGRNA(g); setRefineLength(20); setRefinedResult(null); }} style={{ fontSize: 11, padding: '4px 10px' }}>Refine</Btn>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>

      {/* Refinement modal */}
      {refiningGRNA && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200 }}
          onClick={() => setRefiningGRNA(null)}
        >
          <Card onClick={(e) => e.stopPropagation()} style={{ maxWidth: 460, width: '90%', border: `1px solid ${T.accent}33` }}>
            <h3 style={{ margin: '0 0 12px', color: T.text, fontSize: 18 }}>Refine gRNA Length</h3>
            <p style={{ color: T.textMuted, fontSize: 13, marginBottom: 16 }}>
              Current: <span style={{ fontFamily: T.mono, color: T.green }}>{refiningGRNA.sequence}</span>{' '}
              ({refiningGRNA.sequence.length} bases)
            </p>
            <label style={{ color: T.textMuted, fontSize: 13 }}>
              New length: <strong style={{ color: T.text }}>{refineLength}</strong> bases
            </label>
            <input
              type="range" min={17} max={25} value={refineLength}
              onChange={(e) => setRefineLength(Number(e.target.value))}
              style={{ width: '100%', marginTop: 8, marginBottom: 4 }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', color: T.textDim, fontSize: 11, marginBottom: 16 }}>
              <span>17 (min)</span><span>20 (std)</span><span>25 (max)</span>
            </div>
            {refinedResult && (
              <Card style={{ background: T.bg, marginBottom: 16, padding: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ color: T.textMuted, fontSize: 13 }}>Previous Score</span>
                  <span style={{ color: T.orange, fontWeight: 600 }}>{refinedResult.previousScore.toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: T.textMuted, fontSize: 13 }}>New Score</span>
                  <span style={{ color: refinedResult.refinedGRNA.score > refinedResult.previousScore ? T.green : T.red, fontWeight: 700, fontSize: 20 }}>
                    {refinedResult.refinedGRNA.score.toFixed(2)}
                  </span>
                </div>
              </Card>
            )}
            <div style={{ display: 'flex', gap: 10 }}>
              <Btn onClick={handleRefine} disabled={refineLoading} style={{ flex: 1 }}>
                {refineLoading ? 'Scoring...' : 'Re-score'}
              </Btn>
              <Btn variant="ghost" onClick={() => setRefiningGRNA(null)}>Close</Btn>
            </div>
          </Card>
        </div>
      )}
    </PageShell>
  );
}
