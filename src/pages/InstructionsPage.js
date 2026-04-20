import React, { useState } from 'react';
import { Card, PageShell, PageHeader } from '../components/shared';
import T from '../styles/theme';

const STEPS = [
  { num: '01', title: 'Input Sequence', desc: 'Navigate to the Analysis page. Paste a raw nucleotide sequence (A/T/G/C), or upload a .FASTA or .txt file. You can also select a pre-loaded sequence from the Database page.' },
  { num: '02', title: 'SNP Detection', desc: 'The platform aligns your sequence against the healthy HBB reference and identifies single-nucleotide differences. Each SNP is annotated with its position, codon change, amino acid impact, disease association, and pathogenicity classification.' },
  { num: '03', title: 'CRISPR Design', desc: 'Click any detected SNP to generate candidate guide RNAs (gRNAs). The system scans for nearby PAM sites (NGG), generates 20-mer gRNA sequences, and scores each on cut site distance, GC content, homopolymer penalties, and off-target count.' },
  { num: '04', title: 'Binding Visualization', desc: 'Click a gRNA to see an interactive visualization of where it binds on the genome. The viewer shows the reference strand, complementary strand, PAM site, SNP position, and cut site. Zoom and pan to explore.' },
  { num: '05', title: 'Results & Refinement', desc: 'Review the full pipeline results in a summary view. If off-target counts are high, use the refinement tool to extend or reduce gRNA length (17–25 bases) and re-score. Export your results when ready.' },
];

const SETUP_STEPS = [
  {
    num: 'S1',
    title: 'Install BLAST+',
    desc: 'Download BLAST+ from the NCBI FTP site (https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/). Run the Windows installer. The default install location is C:\\Program Files\\NCBI\\blast-2.X.X+\\.',
  },
  {
    num: 'S2',
    title: 'Start the API server',
    desc: 'Open a terminal in the project root and run: uvicorn BLAST.server.main:app --reload --port 8000. Keep this terminal open while using the app.',
  },
  {
    num: 'S3',
    title: 'Configure the BLAST bin path',
    desc: 'Go to Settings. In the "BLAST+ bin folder path" field, paste the full path to the bin folder inside your BLAST+ installation — for example C:\\Program Files\\NCBI\\blast-2.17.0+\\bin. Click Save Configuration. The status indicator turns green when the path is valid.',
  },
  {
    num: 'S4',
    title: 'Build the reference database',
    desc: 'Still on the Settings page, scroll to "Initialize / Update Database". Either load a FASTA file (e.g. BLAST/sample_fasta_test/gene.fa from the project) or paste FASTA text directly, then click Build (overwrite). The Database Status card will update to show the number of sequences loaded.',
  },
  {
    num: 'S5',
    title: 'Verify and start analyzing',
    desc: 'Once the status card shows a green dot with a record count, the platform is ready. Navigate to Analysis and paste or upload a patient sequence to begin SNP detection.',
  },
];

const FAQS = [
  { q: 'How do I set up the platform for the first time?', a: 'Install BLAST+ from NCBI, start the API server with uvicorn, then go to Settings to configure the BLAST bin path and build the reference database. See the First-Time Setup section above for step-by-step instructions.' },
  { q: 'What input formats are supported?', a: 'The platform accepts raw nucleotide sequences (pasted directly), FASTA files (.fasta, .fa), and plain text files (.txt). Sequences should contain only A, T, G, C, and N characters.' },
  { q: 'What gene does this platform target?', a: 'Currently, CLEAVE SNP is designed for the HBB (beta-globin) gene. The platform aligns input sequences against a bundled HBB reference to detect sickle cell disease and related hemoglobin variants.' },
  { q: 'How is the gRNA score calculated?', a: 'The composite score combines four weighted metrics: cut site distance (30%), GC content (25%), homopolymer penalty (15%), and off-target count (30%). Higher scores indicate better candidates.' },
  { q: 'What does "off-target count" mean?', a: 'Off-target count represents the number of genomic locations (other than the intended target) where the gRNA could potentially bind with 3 or fewer mismatches. Lower counts indicate higher specificity and safety.' },
  { q: 'Can I analyze sequences from other genes?', a: 'The current version is optimized for HBB. Future releases may support additional disease genes like BRCA1, BRCA2, and others.' },
  { q: 'What is the difference between Base Edit and HDR?', a: 'Base editing makes a single nucleotide change without cutting both DNA strands — ideal for point mutations like the sickle cell A→T change. HDR (homology-directed repair) uses a donor template to replace a larger sequence region and requires a double-strand break.' },
];

export default function InstructionsPage() {
  const [openFaq, setOpenFaq] = useState(null);

  return (
    <PageShell maxWidth={800}>
      <PageHeader title="Instructions" subtitle="How to use the CLEAVE SNP platform" />

      {/* First-Time Setup */}
      <h2 style={{ fontSize: 22, fontWeight: 700, color: T.text, marginBottom: 4, fontFamily: T.display }}>
        First-Time Setup
      </h2>
      <p style={{ fontSize: 14, color: T.textMuted, marginBottom: 24, lineHeight: 1.7 }}>
        Complete these steps once before using the platform. After setup, only the API server needs to be running.
      </p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginBottom: 48 }}>
        {SETUP_STEPS.map((s, i) => (
          <div
            key={s.num}
            style={{
              display: 'flex', gap: 20, padding: '20px 0',
              borderBottom: i < SETUP_STEPS.length - 1 ? `1px solid ${T.border}22` : 'none',
            }}
          >
            <div style={{
              fontSize: 24, fontWeight: 800, color: T.accent,
              fontFamily: T.mono, opacity: 0.5, minWidth: 48,
            }}>
              {s.num}
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: T.text, marginBottom: 6 }}>{s.title}</div>
              <div style={{ fontSize: 14, color: T.textMuted, lineHeight: 1.7 }}>{s.desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Analysis Pipeline */}
      <h2 style={{ fontSize: 22, fontWeight: 700, color: T.text, marginBottom: 4, fontFamily: T.display }}>
        Analysis Pipeline
      </h2>
      <p style={{ fontSize: 14, color: T.textMuted, marginBottom: 24, lineHeight: 1.7 }}>
        Each analysis run follows these five stages.
      </p>

      {/* Steps */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginBottom: 48 }}>
        {STEPS.map((s, i) => (
          <div
            key={s.num}
            style={{
              display: 'flex', gap: 20, padding: '20px 0',
              borderBottom: i < STEPS.length - 1 ? `1px solid ${T.border}22` : 'none',
            }}
          >
            <div
              style={{
                fontSize: 32, fontWeight: 800, color: T.accent,
                fontFamily: T.mono, opacity: 0.5, minWidth: 48,
              }}
            >
              {s.num}
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: T.text, marginBottom: 6 }}>
                {s.title}
              </div>
              <div style={{ fontSize: 14, color: T.textMuted, lineHeight: 1.7 }}>{s.desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* FAQ */}
      <h2
        style={{
          fontSize: 22, fontWeight: 700, color: T.text,
          marginBottom: 20, fontFamily: T.display,
        }}
      >
        Frequently Asked Questions
      </h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {FAQS.map((f, i) => (
          <Card
            key={i}
            onClick={() => setOpenFaq(openFaq === i ? null : i)}
            hoverable
            style={{ cursor: 'pointer', padding: '16px 20px' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 600, color: T.text, fontSize: 14 }}>{f.q}</span>
              <span
                style={{
                  color: T.textDim, fontSize: 18, transition: 'transform 0.2s',
                  transform: openFaq === i ? 'rotate(45deg)' : 'none',
                }}
              >
                +
              </span>
            </div>
            {openFaq === i && (
              <p
                style={{
                  margin: '12px 0 0', color: T.textMuted, fontSize: 14, lineHeight: 1.7,
                  borderTop: `1px solid ${T.border}22`, paddingTop: 12,
                }}
              >
                {f.a}
              </p>
            )}
          </Card>
        ))}
      </div>
    </PageShell>
  );
}
