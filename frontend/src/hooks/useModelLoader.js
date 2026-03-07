import { useState } from 'react';
import { extractConcept, retrieveModels, runFallback } from '../services/api';

export function useModelLoader() {
  const [status,   setStatus]   = useState('idle');
  const [concept,  setConcept]  = useState(null);
  const [models,   setModels]   = useState([]);
  const [fallback, setFallback] = useState(null);
  const [error,    setError]    = useState(null);
  const [step,     setStep]     = useState('');

  async function search(query) {
    setStatus('loading');
    setError(null);
    setModels([]);
    setFallback(null);
    setConcept(null);

    try {
      setStep('Extracting concept structure...');
      const cRes = await extractConcept(query);
      setConcept(cRes.data);

      setStep('Searching Sketchfab & 3D databases...');
      const rRes = await retrieveModels(cRes.data);

      const hasGoodModel = (
        rRes.data.models.length > 0 &&
        !rRes.data.fallback_triggered &&
        rRes.data.models[0]?.embed_url &&
        rRes.data.best_confidence >= 60
      );

      if (hasGoodModel) {
        setStep('Found 3D model!');
        setModels(rRes.data.models);
        setStatus('success');
      } else {
        setStep('Generating procedural 3D visualization...');
        const fRes = await runFallback(cRes.data);
        setFallback(fRes.data);
        setStatus('success');
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Unknown error';
      setError(msg);
      setStatus('error');
    }
  }

  function reset() {
    setStatus('idle');
    setConcept(null);
    setModels([]);
    setFallback(null);
    setError(null);
    setStep('');
  }

  return { status, concept, models, fallback, error, step, search, reset };
}