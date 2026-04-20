import React, { useEffect, useRef, useState } from 'react';
import { Btn, Card, PageShell, PageHeader } from '../components/shared';
import api from '../services/api';
import T from '../styles/theme';

export default function SettingsPage() {
  // ── BLAST bin config ──────────────────────────────────────────────────────
  const [blastBin, setBlastBin]     = useState('');
  const [configured, setConfigured] = useState(false);
  const [loading, setLoading]       = useState(true);
  const [saving, setSaving]         = useState(false);
  const [configStatus, setConfigStatus] = useState(null); // { type, message }

  // ── Database status ───────────────────────────────────────────────────────
  const [dbStatus, setDbStatus]           = useState(null);
  const [dbStatusLoading, setDbStatusLoading] = useState(true);

  // ── Build / add database ──────────────────────────────────────────────────
  const [fastaInput, setFastaInput]       = useState('');
  const [dbBuilding, setDbBuilding]       = useState(false);
  const [dbBuildStatus, setDbBuildStatus] = useState(null); // { type, message }
  const fileRef = useRef(null);

  // Load config and DB status in parallel on mount
  useEffect(() => {
    (async () => {
      try {
        const [cfg, dbStat] = await Promise.all([api.getConfig(), api.getDbStatus()]);
        setBlastBin(cfg.blast_bin || '');
        setConfigured(cfg.configured || false);
        setDbStatus(dbStat);
      } catch {
        setConfigStatus({ type: 'error', message: 'Could not reach the server. Make sure uvicorn is running on port 8000.' });
      } finally {
        setLoading(false);
        setDbStatusLoading(false);
      }
    })();
  }, []);

  const handleSave = async () => {
    if (!blastBin.trim()) {
      setConfigStatus({ type: 'error', message: 'BLAST bin path cannot be empty.' });
      return;
    }
    setSaving(true);
    setConfigStatus(null);
    try {
      const saved = await api.saveConfig({ blast_bin: blastBin.trim() });
      setConfigured(saved.configured);
      setConfigStatus({ type: 'success', message: 'Configuration saved. BLAST analysis is now available.' });
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Failed to save config.';
      setConfigStatus({ type: 'error', message });
    } finally {
      setSaving(false);
    }
  };

  const handleRefreshDbStatus = async () => {
    setDbStatusLoading(true);
    try {
      setDbStatus(await api.getDbStatus());
    } finally {
      setDbStatusLoading(false);
    }
  };

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => { setFastaInput(ev.target.result || ''); setDbBuildStatus(null); };
    reader.readAsText(file);
  };

  const handleBuild = async (overwrite) => {
    if (!fastaInput.trim()) {
      setDbBuildStatus({ type: 'error', message: 'No FASTA content provided.' });
      return;
    }
    setDbBuilding(true);
    setDbBuildStatus(null);
    try {
      const result = overwrite
        ? await api.buildDatabase(fastaInput)
        : await api.addToDatabase(fastaInput);
      setDbStatus(result.status);
      setDbBuildStatus({ type: 'success', message: result.message });
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Operation failed.';
      setDbBuildStatus({ type: 'error', message });
    } finally {
      setDbBuilding(false);
    }
  };

  const statusBanner = (s) => s && (
    <div style={{
      padding: '10px 14px', borderRadius: 6, marginBottom: 16, fontSize: 13,
      background: s.type === 'success' ? `${T.green}18` : `${T.red}18`,
      border: `1px solid ${s.type === 'success' ? T.green : T.red}44`,
      color: s.type === 'success' ? T.green : T.red,
    }}>
      {s.type === 'success' ? '✓ ' : '⚠ '}{s.message}
    </div>
  );

  return (
    <PageShell maxWidth={640}>
      <PageHeader
        title="Settings"
        subtitle="Configure BLAST+ and initialize the reference database"
      />

      {/* ── Card 1: BLAST bin config ─────────────────────────────────────── */}
      <Card>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24 }}>
          <div style={{
            width: 10, height: 10, borderRadius: '50%',
            background: configured ? T.green : T.red, flexShrink: 0,
          }} />
          <span style={{ color: T.textMuted, fontSize: 13 }}>
            {loading ? 'Checking server…'
              : configured ? 'BLAST is configured and ready'
              : 'BLAST is not configured — analysis is unavailable'}
          </span>
        </div>

        <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: T.textDim, fontWeight: 600 }}>
          BLAST+ bin folder path
        </label>
        <p style={{ fontSize: 12, color: T.textMuted, margin: '0 0 10px' }}>
          Paste the full path to the folder containing{' '}
          <code style={{ color: T.green, fontFamily: T.mono }}>blastn.exe</code>,{' '}
          <code style={{ color: T.green, fontFamily: T.mono }}>makeblastdb.exe</code>, and{' '}
          <code style={{ color: T.green, fontFamily: T.mono }}>blastdbcmd.exe</code>.
          <br />
          Example: <code style={{ color: T.textDim, fontFamily: T.mono }}>C:\Program Files\NCBI\blast-2.17.0+\bin</code>
        </p>
        <input
          value={blastBin}
          onChange={(e) => { setBlastBin(e.target.value); setConfigStatus(null); }}
          placeholder="C:\...\blast-2.17.0+\bin"
          disabled={loading}
          style={{
            width: '100%', padding: '10px 14px', background: T.bg,
            border: `1px solid ${T.border}`, borderRadius: 6, color: T.text,
            fontSize: 13, fontFamily: T.mono, outline: 'none',
            boxSizing: 'border-box', marginBottom: 20, opacity: loading ? 0.5 : 1,
          }}
        />

        {statusBanner(configStatus)}

        <Btn onClick={handleSave} disabled={loading || saving}>
          {saving ? 'Saving…' : 'Save Configuration'}
        </Btn>
      </Card>

      {/* ── Card 2: Database status ──────────────────────────────────────── */}
      <Card style={{ marginTop: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ margin: 0, fontSize: 14, color: T.text }}>Database Status</h3>
          <Btn variant="ghost" onClick={handleRefreshDbStatus} disabled={dbStatusLoading}
              style={{ padding: '6px 14px', fontSize: 12 }}>
            {dbStatusLoading ? 'Refreshing…' : 'Refresh'}
          </Btn>
        </div>

        {dbStatusLoading ? (
          <p style={{ color: T.textMuted, fontSize: 13, margin: 0 }}>Checking database…</p>
        ) : dbStatus ? (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <div style={{
                width: 10, height: 10, borderRadius: '50%',
                background: dbStatus.exists ? T.green : T.red, flexShrink: 0,
              }} />
              <span style={{ color: T.textMuted, fontSize: 13 }}>
                {dbStatus.exists
                  ? dbStatus.record_count !== null
                    ? `${dbStatus.record_count} sequence${dbStatus.record_count !== 1 ? 's' : ''} in database`
                    : 'Database files found — configure BLAST bin to inspect records'
                  : 'Database not initialized'}
              </span>
            </div>
            {dbStatus.headers && dbStatus.headers.length > 0 && (
              <ul style={{ margin: 0, paddingLeft: 18, color: T.textDim, fontSize: 12, lineHeight: 1.8 }}>
                {dbStatus.headers.map((h, i) => (
                  <li key={i} style={{ fontFamily: T.mono }}>{h}</li>
                ))}
              </ul>
            )}
          </>
        ) : (
          <p style={{ color: T.textMuted, fontSize: 13, margin: 0 }}>Unable to fetch database status.</p>
        )}
      </Card>

      {/* ── Card 3: Initialize / update database ────────────────────────── */}
      <Card style={{ marginTop: 16 }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 14, color: T.text }}>Initialize / Update Database</h3>

        <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: T.textDim, fontWeight: 600 }}>
          Load from file
        </label>
        <input
          ref={fileRef}
          type="file"
          accept=".fa,.fasta,.txt"
          onChange={handleFileInput}
          disabled={dbBuilding}
          style={{ display: 'block', marginBottom: 16, fontSize: 13, color: T.textMuted }}
        />

        <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: T.textDim, fontWeight: 600 }}>
          Or paste FASTA directly
        </label>
        <textarea
          value={fastaInput}
          onChange={(e) => { setFastaInput(e.target.value); setDbBuildStatus(null); }}
          placeholder={'>SequenceName\nACTGACTGACTG...'}
          disabled={dbBuilding}
          rows={8}
          style={{
            width: '100%', padding: '10px 14px', background: T.bg,
            border: `1px solid ${T.border}`, borderRadius: 6, color: T.text,
            fontSize: 12, fontFamily: T.mono, outline: 'none',
            boxSizing: 'border-box', resize: 'vertical', marginBottom: 16,
            opacity: dbBuilding ? 0.5 : 1,
          }}
        />

        {statusBanner(dbBuildStatus)}

        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <Btn onClick={() => handleBuild(true)} disabled={dbBuilding || !configured}>
            {dbBuilding ? 'Building…' : 'Build (overwrite)'}
          </Btn>
          <Btn variant="ghost" onClick={() => handleBuild(false)} disabled={dbBuilding || !configured}>
            {dbBuilding ? 'Adding…' : 'Add to Existing'}
          </Btn>
        </div>

        {!configured && (
          <p style={{ fontSize: 12, color: T.textMuted, marginTop: 10, marginBottom: 0 }}>
            Save the BLAST bin path above before building the database.
          </p>
        )}
      </Card>

      {/* ── Card 4: How to find blast_bin ────────────────────────────────── */}
      <Card style={{ marginTop: 16 }}>
        <h3 style={{ margin: '0 0 12px', fontSize: 14, color: T.text }}>How to find your BLAST bin path</h3>
        <ol style={{ margin: 0, paddingLeft: 20, color: T.textMuted, fontSize: 13, lineHeight: 1.8 }}>
          <li>
            Download BLAST+ from{' '}
            <a href="https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/"
               target="_blank" rel="noreferrer" style={{ color: T.accent }}>
              NCBI FTP
            </a>{' '}
            and install it.
          </li>
          <li>
            Open File Explorer and navigate to the installation folder
            (e.g. <code style={{ fontFamily: T.mono, color: T.textDim }}>C:\Program Files\NCBI\blast-2.17.0+</code>).
          </li>
          <li>
            Open the <code style={{ fontFamily: T.mono, color: T.textDim }}>bin</code> subfolder and confirm
            you can see <code style={{ fontFamily: T.mono, color: T.textDim }}>blastn.exe</code>.
          </li>
          <li>Click the address bar in File Explorer to copy the full path, then paste it above.</li>
        </ol>
      </Card>
    </PageShell>
  );
}
