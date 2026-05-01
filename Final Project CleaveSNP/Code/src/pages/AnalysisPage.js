import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Btn, Card, PageShell, PageHeader } from '../components/shared';
import { parseFasta, validateSequence, detectFormat } from '../utils/sequence';
import T from '../styles/theme';

export default function AnalysisPage() {
  const navigate = useNavigate();
  const { setInputSequence, setInputMeta } = useApp();

  const [text, setText] = useState('');
  const [fileName, setFileName] = useState(null);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['fasta', 'fa', 'txt'].includes(ext)) {
      setError('Unsupported file type. Use .fasta or .txt');
      return;
    }
    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target.result;
      const seq =
        ['fasta', 'fa'].includes(ext)
          ? parseFasta(content)
          : content.replace(/\s/g, '').toUpperCase();
      setText(seq);
      setFileName(file.name);
      setError(null);
    };
    reader.readAsText(file);
  };

  const handleSubmit = () => {
    const result = validateSequence(text);
    if (!result.valid) {
      setError(result.error);
      return;
    }
    const format = detectFormat(fileName);
    setInputSequence(result.cleaned);
    setInputMeta({ fileName, format });
    navigate('/analyzing');
  };

  return (
    <PageShell maxWidth={680}>
      <PageHeader
        title="Sequence Analysis"
        subtitle="Paste or upload a DNA sequence to detect disease-causing SNPs"
      />

      <Card>
        <label
          style={{
            color: T.textMuted, fontSize: 12, fontWeight: 600,
            textTransform: 'uppercase', letterSpacing: 1,
          }}
        >
          Genomic Sequence
        </label>
        <textarea
          value={text}
          onChange={(e) => { setText(e.target.value); setError(null); }}
          placeholder="ATGGTGCATCTGACTCCTGA..."
          rows={8}
          style={{
            width: '100%', marginTop: 10, padding: 16, fontFamily: T.mono,
            fontSize: 14, background: T.bg, border: `1px solid ${T.border}`,
            borderRadius: 8, color: T.green, resize: 'vertical', outline: 'none',
            boxSizing: 'border-box', lineHeight: 1.7, letterSpacing: 1.2,
          }}
        />

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '16px 0' }}>
          <div style={{ flex: 1, height: 1, background: T.border }} />
          <span style={{ color: T.textDim, fontSize: 12 }}>OR</span>
          <div style={{ flex: 1, height: 1, background: T.border }} />
        </div>

        <Btn
          variant="ghost"
          onClick={() => fileRef.current?.click()}
          style={{ width: '100%', padding: '14px', border: `1px dashed ${T.border}` }}
        >
          📄 Load .FASTA or .txt file
        </Btn>
        <input
          ref={fileRef}
          type="file"
          accept=".fasta,.fa,.txt"
          onChange={handleFileUpload}
          style={{ display: 'none' }}
        />

        {fileName && (
          <div
            style={{
              padding: '8px 14px', background: T.greenBg, borderRadius: 6,
              marginTop: 12, color: T.green, fontSize: 13,
              border: `1px solid ${T.greenBorder}`,
            }}
          >
            ✓ Loaded: {fileName} ({text.length} bases)
          </div>
        )}

        {error && (
          <div
            style={{
              padding: '10px 14px', background: T.redBg, borderRadius: 6,
              marginTop: 12, color: T.red, fontSize: 13,
              border: `1px solid ${T.redBorder}`,
            }}
          >
            ⚠ {error}
          </div>
        )}

        <Btn
          disabled={!text.trim()}
          onClick={handleSubmit}
          style={{ width: '100%', marginTop: 16, padding: '14px', fontSize: 15, letterSpacing: 1 }}
        >
          START ANALYSIS
        </Btn>
      </Card>

      <div style={{ textAlign: 'center', marginTop: 16 }}>
        <button
          onClick={() => navigate('/database')}
          style={{
            background: 'none', border: 'none', color: T.textDim,
            cursor: 'pointer', fontSize: 13, fontFamily: T.body,
          }}
        >
          or select a sequence from the{' '}
          <span style={{ color: T.accent, textDecoration: 'underline' }}>Database</span>
        </button>
      </div>
    </PageShell>
  );
}
