import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

const api = {
  async analyze(sequence, format) {
    const { data } = await client.post('/api/analyze', { sequence, format });
    return data;
  },

  async crisprDesign(snp, surroundingSequence, windowSize = 50) {
    const { data } = await client.post('/api/crispr-design', { snp, surroundingSequence, windowSize });
    return data;
  },

  async refineGrna(grnaSequence, newLength, snpPosition, referenceContext) {
    const { data } = await client.post('/api/refine-grna', { grnaSequence, newLength, snpPosition, referenceContext });
    return data;
  },

  async getBindingSite(grna, snp, windowSize = 100) {
    const { data } = await client.post('/api/binding-site', { grna, snp, windowSize });
    return data;
  },

  async getReferenceInfo() {
    const { data } = await client.get('/api/reference-info');
    return data;
  },

  async getSequences() {
    const { data } = await client.get('/api/sequences');
    return data;
  },

  async addSequence(sequenceData) {
    const { data } = await client.post('/api/sequences', sequenceData);
    return data;
  },

  async getConfig() {
    const { data } = await client.get('/api/config');
    return data;
  },

  async saveConfig(configData) {
    const { data } = await client.post('/api/config', configData);
    return data;
  },

  async getDbStatus() {
    const { data } = await client.get('/api/database/status');
    return data;
  },

  async buildDatabase(fastaText) {
    const { data } = await client.post(
      '/api/database/build',
      { fasta_text: fastaText },
      { timeout: 120000 },
    );
    return data;
  },

  async addToDatabase(fastaText) {
    const { data } = await client.post(
      '/api/database/add',
      { fasta_text: fastaText },
      { timeout: 120000 },
    );
    return data;
  },
};

export default api;
