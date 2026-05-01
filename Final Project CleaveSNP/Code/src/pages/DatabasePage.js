import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Btn, Card, PageShell, PageHeader } from '../components/shared';
import { parseFasta, validateSequence } from '../utils/sequence';
import T from '../styles/theme';

export default function DatabasePage() {
  const navigate = useNavigate();
  const { setInputSequence, setInputMeta, dbSequences, setDbSequences } = useApp();

  const [showUpload, setShowUpload] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newSeq, setNewSeq] = useState('');
  const [uploadError, setUploadError] = useState(null);
  const fileRef = useRef(null);

  const handleSelectForAnalysis = (seq) => {
    setInputSequence(seq.sequence);
    setInputMeta({ fileName: seq.name, format: 'database' });
    navigate('/analyzing');
  };

  const handleAddSequence = () => {
    if (!newName.trim() || !newSeq.trim()) {
      setUploadError('Name and sequence are required');
      return;
    }
    const result = validateSequence(newSeq);
    if (!result.valid) {
      setUploadError(result.error);
      return;
    }
    const newEntry = {
      id: Date.now(),
      name: newName.trim(),
      gene: 'HBB',
      organism: 'Homo sapiens',
      length: result.cleaned.length,
      description: newDesc.trim() || 'User-uploaded sequence',
      sequence: result.cleaned,
      added: new Date().toISOString().split('T')[0],
    };
    setDbSequences((prev) => [...prev, newEntry]);
    setNewName('');
    setNewDesc('');
    setNewSeq('');
    setShowUpload(false);
    setUploadError(null);
  };

  const handleFileLoad = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target.result;
      const ext = file.name.split('.').pop().toLowerCase();
      const seq =
        ['fasta', 'fa'].includes(ext)
          ? parseFasta(content)
          : content.replace(/\s/g, '').toUpperCase();
      setNewSeq(seq);
      if (!newName) setNewName(file.name.replace(/\.[^.]+$/, ''));
    };
    reader.readAsText(file);
  };

  return (
    <PageShell>
      <PageHeader
        title="Sequence Database"
        subtitle={`${dbSequences.length} sequences available — select one to analyze or add your own`}
        actions={
          <Btn onClick={() => setShowUpload(!showUpload)}>
            {showUpload ? 'Cancel' : '+ Add Sequence'}
          </Btn>
        }
      />

      {/* Upload panel */}
      {showUpload && (
        <Card style={{ marginBottom: 24, border: `1px solid ${T.accent}33` }}>
          <h3 style={{ margin: '0 0 16px', color: T.text, fontSize: 16 }}>Add New Sequence</h3>
          <div style={{ display: 'flex', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Sequence name *"
              style={{
                flex: '1 1 200px', padding: '10px 14px', background: T.bg,
                border: `1px solid ${T.border}`, borderRadius: 6, color: T.text,
                fontSize: 14, fontFamily: T.body, outline: 'none',
              }}
            />
            <input
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              placeholder="Description (optional)"
              style={{
                flex: '2 1 300px', padding: '10px 14px', background: T.bg,
                border: `1px solid ${T.border}`, borderRadius: 6, color: T.text,
                fontSize: 14, fontFamily: T.body, outline: 'none',
              }}
            />
          </div>
          <textarea
            value={newSeq}
            onChange={(e) => { setNewSeq(e.target.value); setUploadError(null); }}
            placeholder="Paste nucleotide sequence (A/T/G/C) or load from file below..."
            rows={4}
            style={{
              width: '100%', padding: '12px 14px', background: T.bg,
              border: `1px solid ${T.border}`, borderRadius: 6, color: T.green,
              fontSize: 13, fontFamily: T.mono, resize: 'vertical', outline: 'none',
              boxSizing: 'border-box', marginBottom: 12,
            }}
          />
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
            <Btn variant="ghost" onClick={() => fileRef.current?.click()}>
              Load from .FASTA / .txt
            </Btn>
            <input
              ref={fileRef}
              type="file"
              accept=".fasta,.fa,.txt"
              onChange={handleFileLoad}
              style={{ display: 'none' }}
            />
            <div style={{ flex: 1 }} />
            {uploadError && (
              <span style={{ color: T.red, fontSize: 13 }}>⚠ {uploadError}</span>
            )}
            <Btn onClick={handleAddSequence}>Save to Database</Btn>
          </div>
        </Card>
      )}

      {/* Sequence list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {dbSequences.map((seq) => (
          <Card
            key={seq.id}
            hoverable
            style={{
              display: 'flex', justifyContent: 'space-between',
              alignItems: 'center', flexWrap: 'wrap', gap: 12,
            }}
          >
            <div style={{ flex: '1 1 300px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                <span style={{ fontWeight: 700, color: T.text, fontSize: 15 }}>{seq.name}</span>
                <span
                  style={{
                    fontSize: 11, color: T.textDim, padding: '2px 8px',
                    background: T.surfaceAlt, borderRadius: 4,
                  }}
                >
                  {seq.gene}
                </span>
              </div>
              <div style={{ fontSize: 13, color: T.textMuted, marginBottom: 4 }}>
                {seq.description}
              </div>
              <div style={{ fontSize: 12, color: T.textDim }}>
                {seq.length} bp · {seq.organism} · Added {seq.added}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <Btn
                variant="ghost"
                onClick={() => navigator.clipboard?.writeText(seq.sequence)}
                style={{ fontSize: 12, padding: '6px 14px' }}
              >
                Copy
              </Btn>
              <Btn
                onClick={() => handleSelectForAnalysis(seq)}
                style={{ fontSize: 12, padding: '6px 14px' }}
              >
                Analyze →
              </Btn>
            </div>
          </Card>
        ))}
      </div>
    </PageShell>
  );
}
