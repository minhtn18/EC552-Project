import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Btn, Card, PageShell, PageHeader } from '../components/shared';
import T from '../styles/theme';

export default function EditResultsPage() {
  const navigate = useNavigate();
  const { selectedSNP, selectedGRNA, grnaCacheMap, inputSequence } = useApp();

  // Guard
  if (!selectedSNP || !selectedGRNA) {
    navigate('/results/crispr', { replace: true });
    return null;
  }

  const allGRNAs = grnaCacheMap.get(selectedSNP.snpNo) || [];

  const handleExport = () => {
    const report = {
      timestamp: new Date().toISOString(),
      gene: selectedSNP.gene,
      snp: selectedSNP,
      selectedGRNA,
      allCandidates: allGRNAs,
      inputSequenceLength: inputSequence?.length,
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cleave_snp_report_${selectedSNP.gene}_SNP${selectedSNP.snpNo}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <PageShell maxWidth={900}>
      <PageHeader
        title="Edit Results"
        subtitle="Full pipeline summary — review, modify, and export"
        actions={
          <div style={{ display: 'flex', gap: 8 }}>
            <Btn onClick={handleExport} style={{ fontSize: 13 }}>Export JSON</Btn>
            <Btn variant="ghost" onClick={() => navigate('/analysis')}>New Analysis</Btn>
          </div>
        }
      />

      {/* Section 1: SNP Summary */}
      <Card style={{ marginBottom: 16 }}>
        <h3 style={{ margin: '0 0 16px', color: T.accent, fontSize: 14, textTransform: 'uppercase', letterSpacing: 1, fontFamily: T.body }}>
          Detected SNP
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 16 }}>
          {[
            { label: 'Gene', value: selectedSNP.gene },
            { label: 'Position', value: selectedSNP.position },
            { label: 'Ref → Var', value: `${selectedSNP.refNucleotide} → ${selectedSNP.varNucleotide}` },
            { label: 'Codon Change', value: selectedSNP.codon },
            { label: 'AA Change', value: selectedSNP.aminoAcidChange },
            { label: 'Disease', value: selectedSNP.disease },
          ].map((item) => (
            <div key={item.label}>
              <div style={{ fontSize: 10, color: T.textDim, textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5, marginBottom: 4 }}>{item.label}</div>
              <div style={{ fontSize: 15, color: T.text, fontWeight: 600, fontFamily: T.mono }}>{item.value}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Section 2: Selected gRNA */}
      <Card style={{ marginBottom: 16 }}>
        <h3 style={{ margin: '0 0 16px', color: T.accent, fontSize: 14, textTransform: 'uppercase', letterSpacing: 1, fontFamily: T.body }}>
          Selected gRNA
        </h3>
        <div style={{ padding: '14px 16px', background: T.bg, borderRadius: 6, border: `1px solid ${T.greenBorder}`, marginBottom: 16 }}>
          <span style={{ fontFamily: T.mono, fontSize: 16, color: T.green, letterSpacing: 2 }}>
            {selectedGRNA.sequence}
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 16 }}>
          {[
            { label: 'Score', value: selectedGRNA.score.toFixed(2), color: selectedGRNA.score >= 0.8 ? T.green : T.orange },
            { label: 'Cut Site Dist', value: `${selectedGRNA.cutSiteDistance} nt` },
            { label: 'GC Content', value: `${selectedGRNA.gcContent}%`, color: selectedGRNA.gcContent >= 40 && selectedGRNA.gcContent <= 65 ? T.green : T.orange },
            { label: 'Off-Targets', value: selectedGRNA.offTargetCount, color: selectedGRNA.offTargetCount > 5 ? T.red : T.green },
            { label: 'Edit Type', value: selectedGRNA.editType },
            { label: 'PAM', value: selectedGRNA.pamSite },
            { label: 'Strand', value: selectedGRNA.strand },
          ].map((item) => (
            <div key={item.label}>
              <div style={{ fontSize: 10, color: T.textDim, textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5, marginBottom: 4 }}>{item.label}</div>
              <div style={{ fontSize: 15, color: item.color || T.text, fontWeight: 600, fontFamily: T.mono }}>{item.value}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Section 3: All Candidates */}
      <Card style={{ marginBottom: 16 }}>
        <h3 style={{ margin: '0 0 16px', color: T.accent, fontSize: 14, textTransform: 'uppercase', letterSpacing: 1, fontFamily: T.body }}>
          All Candidates ({allGRNAs.length})
        </h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr>
                {['Sequence', 'Score', 'Cut Dist', 'GC%', 'Off-Tgt', 'Type'].map((h) => (
                  <th key={h} style={{ padding: '8px 10px', textAlign: 'left', fontSize: 11, color: T.textDim, fontWeight: 600, textTransform: 'uppercase', borderBottom: `1px solid ${T.border}`, fontFamily: T.body }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...allGRNAs].sort((a, b) => b.score - a.score).map((g) => (
                <tr key={g.id} style={{ background: g.id === selectedGRNA.id ? T.accentGlow : 'transparent' }}>
                  <td style={{ padding: '8px 10px', fontFamily: T.mono, fontSize: 11, color: g.id === selectedGRNA.id ? T.green : T.textMuted }}>{g.sequence}</td>
                  <td style={{ padding: '8px 10px', fontWeight: 700, color: g.score >= 0.8 ? T.green : g.score >= 0.6 ? T.orange : T.red }}>{g.score.toFixed(2)}</td>
                  <td style={{ padding: '8px 10px', color: T.text }}>{g.cutSiteDistance} nt</td>
                  <td style={{ padding: '8px 10px', color: T.text }}>{g.gcContent}%</td>
                  <td style={{ padding: '8px 10px', color: g.offTargetCount > 5 ? T.red : T.text }}>{g.offTargetCount}</td>
                  <td style={{ padding: '8px 10px' }}>
                    <span style={{ fontSize: 11, color: g.editType === 'Base Edit' ? T.green : T.blue }}>{g.editType}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Navigation actions */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <Btn variant="ghost" onClick={() => navigate('/results/binding')} style={{ flex: '1 1 auto' }}>← View Binding Site</Btn>
        <Btn variant="ghost" onClick={() => navigate('/results/crispr')} style={{ flex: '1 1 auto' }}>← Change gRNA Selection</Btn>
        <Btn variant="ghost" onClick={() => navigate('/results/snps')} style={{ flex: '1 1 auto' }}>← Change SNP</Btn>
        <Btn onClick={() => navigate('/analysis')} style={{ flex: '1 1 auto' }}>New Analysis</Btn>
      </div>
    </PageShell>
  );
}
