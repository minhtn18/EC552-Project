import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Btn, PageShell, Spinner } from '../components/shared';
import { USE_MOCK } from '../data/config';
import { MOCK_SNPS } from '../data/mockData';
import api from '../services/api';
import T from '../styles/theme';

export default function AnalyzingPage() {
  const navigate = useNavigate();
  const { inputSequence, inputMeta, setSnpResults, setSnpFastaReport, setGrnaCacheMap } = useApp();
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!inputSequence) {
      navigate('/analysis', { replace: true });
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        let result;
        if (USE_MOCK) {
          await new Promise((r) => setTimeout(r, 1800));
          result = { snps: MOCK_SNPS };
        } else {
          result = await api.analyze(inputSequence, inputMeta?.format || 'raw');
        }
        if (!cancelled) {
          setSnpResults(result.snps);
          setSnpFastaReport(result.fasta_report || '');
          setGrnaCacheMap(new Map());
          navigate('/results/snps', { replace: true });
        }
      } catch (err) {
        if (!cancelled) setError(err.message || 'Analysis failed');
      }
    })();

    return () => { cancelled = true; };
  }, []); // Run once on mount

  if (error) {
    return (
      <PageShell maxWidth={500}>
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
          <h2 style={{ color: T.red, margin: '0 0 8px' }}>Analysis Failed</h2>
          <p style={{ color: T.textMuted, marginBottom: 24 }}>{error}</p>
          <Btn onClick={() => navigate('/analysis')}>← Back to Analysis</Btn>
        </div>
      </PageShell>
    );
  }

  return <Spinner text="Aligning against HBB reference and detecting variants..." />;
}
