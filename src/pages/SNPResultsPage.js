import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Btn, Card, PathBadge, PageShell, PageHeader, Spinner } from '../components/shared';
import { USE_MOCK } from '../data/config';
import { MOCK_GRNAS } from '../data/mockData';
import api from '../services/api';
import T from '../styles/theme';

const COLUMNS = ['SNP #', 'Position', 'Ref', 'Variant', 'Codon', 'AA Change', 'Disease', 'Pathogenicity'];

export default function SNPResultsPage() {
  const navigate = useNavigate();
  const {
    snpResults, setSelectedSNP, inputSequence,
    grnaCacheMap, setGrnaCacheMap,
  } = useApp();
  const [loading, setLoading] = useState(false);

  // Guard: redirect if no results
  if (!snpResults) {
    navigate('/analysis', { replace: true });
    return null;
  }

  // No SNPs found
  if (snpResults.length === 0) {
    return (
      <PageShell maxWidth={500}>
        <div className="fade-in" style={{ textAlign: 'center', padding: '60px 0' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
          <h2 style={{ color: T.green, margin: '0 0 8px' }}>SNP Not Detected</h2>
          <p style={{ color: T.textMuted, marginBottom: 24 }}>
            The submitted sequence matches the healthy HBB reference. No disease-causing
            variants were found.
          </p>
          <Btn onClick={() => navigate('/analysis')}>← Try Another Sequence</Btn>
        </div>
      </PageShell>
    );
  }

  const handleSelect = async (snp) => {
    setSelectedSNP(snp);

    // Check cache
    if (grnaCacheMap.has(snp.snpNo)) {
      navigate('/results/crispr');
      return;
    }

    setLoading(true);
    try {
      let grnas;
      if (USE_MOCK) {
        await new Promise((r) => setTimeout(r, 900));
        grnas = MOCK_GRNAS;
      } else {
        const result = await api.crisprDesign(snp, inputSequence, 50);
        grnas = result.grnaCandidates;
      }
      setGrnaCacheMap((prev) => new Map(prev).set(snp.snpNo, grnas));
      navigate('/results/crispr');
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageShell maxWidth={1000}>
      {loading && (
        <div
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
            zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
        >
          <Spinner text="Generating CRISPR designs..." />
        </div>
      )}

      <PageHeader
        title="SNP Detection Results"
        subtitle={`${snpResults.length} variant${snpResults.length !== 1 ? 's' : ''} detected — click a row to design CRISPR corrections`}
        actions={<Btn variant="ghost" onClick={() => navigate('/analysis')}>← New Analysis</Btn>}
      />

      <Card style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: T.surfaceAlt }}>
              {COLUMNS.map((h) => (
                <th
                  key={h}
                  style={{
                    padding: '14px 12px', textAlign: 'left', fontSize: 11, fontWeight: 700,
                    color: T.textDim, textTransform: 'uppercase', letterSpacing: 0.5,
                    fontFamily: T.body, borderBottom: `1px solid ${T.border}`,
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {snpResults.map((snp) => (
              <tr
                key={snp.snpNo}
                onClick={() => handleSelect(snp)}
                style={{ cursor: 'pointer', transition: 'background 0.15s', borderBottom: `1px solid ${T.border}11` }}
                onMouseEnter={(e) => { e.currentTarget.style.background = T.accentGlow; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
              >
                <td style={{ padding: '14px 12px', color: T.accent, fontWeight: 700, fontFamily: T.mono }}>{snp.snpNo}</td>
                <td style={{ padding: '14px 12px', color: T.text, fontFamily: T.mono }}>{snp.position}</td>
                <td style={{ padding: '14px 12px', color: T.green, fontFamily: T.mono, fontWeight: 700 }}>{snp.refNucleotide}</td>
                <td style={{ padding: '14px 12px', color: T.red, fontFamily: T.mono, fontWeight: 700 }}>{snp.varNucleotide}</td>
                <td style={{ padding: '14px 12px', color: T.textMuted, fontFamily: T.mono, fontSize: 13 }}>{snp.codon}</td>
                <td style={{ padding: '14px 12px', color: T.textMuted, fontSize: 13 }}>{snp.aminoAcidChange}</td>
                <td style={{ padding: '14px 12px', color: T.text, fontSize: 13 }}>{snp.disease}</td>
                <td style={{ padding: '14px 12px' }}><PathBadge value={snp.pathogenicity} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </PageShell>
  );
}
