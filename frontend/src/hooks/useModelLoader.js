import { useState } from 'react';
import { extractConcept, retrieveModels, runFallback } from '../services/api';
import heartMock from '../assets/mock_responses/heart.json';

const DEMO_MODE = false; // Set true to use mock data without backend

export function useModelLoader() {
  const [status, setStatus] = useState('idle');
  const [concept, setConcept] = useState(null);
  const [models, setModels] = useState([]);
  const [fallback, setFallback] = useState(null);
  const [error, setError] = useState(null);

  async function search(query) {
    setStatus('loading');
    setError(null);
    setConcept(null);
    setModels([]);
    setFallback(null);
    try {
      if (DEMO_MODE) {
        await new Promise(r => setTimeout(r, 1200)); // fake delay
        setConcept(heartMock.concept);
        setModels(heartMock.models);
        setStatus('success');
        return;
      }
      const cRes = await extractConcept(query);
      setConcept(cRes.data);
      const rRes = await retrieveModels(cRes.data);
      if (rRes.data.models.length > 0 && !rRes.data.fallback_triggered) {
        setModels(rRes.data.models);
      } else {
        const fRes = await runFallback(cRes.data);
        setFallback(fRes.data);
      }
      setStatus('success');
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      setStatus('error');
    }
  }

  function reset() {
    setStatus('idle');
    setConcept(null);
    setModels([]);
    setFallback(null);
    setError(null);
  }

  return { status, concept, models, fallback, error, search, reset };
}
