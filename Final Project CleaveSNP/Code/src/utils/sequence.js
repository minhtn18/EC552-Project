/**
 * Parse a FASTA-formatted string into a raw nucleotide sequence.
 * Strips header lines (starting with '>') and whitespace.
 */
export function parseFasta(text) {
  return text
    .split('\n')
    .filter((line) => !line.startsWith('>'))
    .join('')
    .replace(/\s/g, '')
    .toUpperCase();
}

/**
 * Validate a nucleotide sequence.
 * Returns { valid: true, cleaned } or { valid: false, error }.
 */
export function validateSequence(seq) {
  if (!seq || seq.trim().length === 0) {
    return { valid: false, error: 'Please input your DNA sequence' };
  }

  const cleaned = seq
    .replace(/^>.*$/gm, '') // strip FASTA headers
    .replace(/\s/g, '')     // strip whitespace
    .toUpperCase();

  if (cleaned.length < 30) {
    return { valid: false, error: 'Sequence too short (minimum 30 bases)' };
  }

  const invalid = cleaned.match(/[^ATGCN]/g);
  if (invalid) {
    return {
      valid: false,
      error: `Invalid characters: ${[...new Set(invalid)].join(', ')}`,
    };
  }

  return { valid: true, cleaned };
}

/**
 * Detect file format from extension.
 */
export function detectFormat(fileName) {
  if (!fileName) return 'raw';
  if (/\.(fasta|fa)$/i.test(fileName)) return 'fasta';
  if (/\.txt$/i.test(fileName)) return 'txt';
  return 'raw';
}
