/**
 * Mock data for development — remove or bypass once the FastAPI backend is connected.
 * Toggle USE_MOCK in config.js to switch between mock and live API.
 */

export const MOCK_DB_SEQUENCES = [
  {
    id: 1,
    name: 'HBB Sickle Cell Mutation (HbS)',
    gene: 'HBB',
    organism: 'Homo sapiens',
    length: 147,
    description: 'Beta-globin gene with Glu6Val sickle cell mutation',
    sequence:
      'ATGGTGCATCTGACTCCTGTGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAAGTTGGTGGTGAGGCCCTGGGCAGGTTGGTATCAAGGTTACAAGACAGGTTTAAGGAGACCAATAGAAACTGGGCATGTGGAGACAGAGAAGACTCTTGG',
    added: '2026-03-15',
  },
  {
    id: 2,
    name: 'HBB Hemoglobin C (HbC)',
    gene: 'HBB',
    organism: 'Homo sapiens',
    length: 147,
    description: 'Beta-globin gene with Glu6Lys mutation',
    sequence:
      'ATGGTGCATCTGACTCCTAAGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAAGTTGGTGGTGAGGCCCTGGGCAGGTTGGTATCAAGGTTACAAGACAGGTTTAAGGAGACCAATAGAAACTGGGCATGTGGAGACAGAGAAGACTCTTGG',
    added: '2026-03-15',
  },
  {
    id: 3,
    name: 'HBB Wild Type (Healthy Reference)',
    gene: 'HBB',
    organism: 'Homo sapiens',
    length: 147,
    description: 'Normal beta-globin gene — no mutations',
    sequence:
      'ATGGTGCATCTGACTCCTGAGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAAGTTGGTGGTGAGGCCCTGGGCAGGTTGGTATCAAGGTTACAAGACAGGTTTAAGGAGACCAATAGAAACTGGGCATGTGGAGACAGAGAAGACTCTTGG',
    added: '2026-03-10',
  },
];

export const MOCK_SNPS = [
  {
    snpNo: 1, position: 20, refNucleotide: 'A', varNucleotide: 'T',
    codon: 'GAG → GTG', aminoAcidChange: 'Glu → Val',
    gene: 'HBB', disease: 'Sickle Cell Disease', pathogenicity: 'Pathogenic',
  },
  {
    snpNo: 2, position: 26, refNucleotide: 'G', varNucleotide: 'A',
    codon: 'GAG → AAG', aminoAcidChange: 'Glu → Lys',
    gene: 'HBB', disease: 'Hemoglobin C Disease', pathogenicity: 'Pathogenic',
  },
];

export const MOCK_GRNAS = [
  { id: 1, sequence: 'ATGGTGCATCTGACTCCTGA', pamSite: 'TGG', pamPosition: 18, cutSiteDistance: 3, gcContent: 50.0, homopolymerPenalty: 0, offTargetCount: 1, score: 0.92, editType: 'Base Edit', strand: 'sense' },
  { id: 2, sequence: 'GTGCATCTGACTCCTGAGGA', pamSite: 'AGG', pamPosition: 22, cutSiteDistance: 5, gcContent: 55.0, homopolymerPenalty: 0, offTargetCount: 2, score: 0.85, editType: 'Base Edit', strand: 'sense' },
  { id: 3, sequence: 'CCTGAGGAGAAGTCTGCCGT', pamSite: 'CGG', pamPosition: 30, cutSiteDistance: 10, gcContent: 60.0, homopolymerPenalty: 1, offTargetCount: 4, score: 0.68, editType: 'HDR', strand: 'antisense' },
  { id: 4, sequence: 'TGACTCCTGAGGAGAAGTCT', pamSite: 'TGG', pamPosition: 25, cutSiteDistance: 7, gcContent: 45.0, homopolymerPenalty: 0, offTargetCount: 8, score: 0.55, editType: 'HDR', strand: 'sense' },
];

export const MOCK_BINDING = {
  referenceWindow:
    'ATGGTGCATCTGACTCCTGAGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAAGTTGGTGGTGAGGCCCTGGGCAGGTTGGTATCAAGG',
  startPosition: 1,
  endPosition: 104,
  grnaBindStart: 1,
  grnaBindEnd: 20,
  pamStart: 21,
  pamEnd: 23,
  snpPositionInWindow: 20,
  cutSitePosition: 17,
  complementaryStrand:
    'TACCACGTAGACTGAGGACTCCTCTTCAGACGGCAATGACGGGACACCCCGTTCCACTTGCACCTACTTCAACCACCACTCCGGGACCCGTCCAACCATAGTTCC',
};
