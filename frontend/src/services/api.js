import axios from 'axios';

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const extractConcept = (query) =>
  axios.post(`${BASE}/api/concept`, { query });

export const retrieveModels = (concept) =>
  axios.post(`${BASE}/api/retrieve`, { concept });

export const runFallback = (concept) =>
  axios.post(`${BASE}/api/fallback`, { concept });

export const healthCheck = () =>
  axios.get(`${BASE}/health`);
