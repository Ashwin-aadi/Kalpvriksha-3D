import { useState } from 'react';

const SUGGESTIONS = [
  'Binary Search Tree', 'DNA Double Helix', 'Solar System',
  'Human Heart', 'Neural Network', 'Glucose Molecule',
  'Inclined Plane', 'Democracy', 'Black Hole', 'Mitochondria',
  'Stack', 'Linked List', 'CPU Architecture', 'Cell Biology',
];

export function SearchBar({ onSearch, isLoading, onReset }) {
  const [query, setQuery] = useState('');
  const [focused, setFocused] = useState(false);

  function handleSubmit(e) {
    e.preventDefault();
    if (query.trim() && !isLoading) onSearch(query.trim());
  }

  function handleSuggestion(s) {
    setQuery(s);
    if (!isLoading) onSearch(s);
  }

  return (
    <div style={{ width: '100%', maxWidth: 720 }}>
      <form onSubmit={handleSubmit} style={{ position: 'relative' }}>
        <div style={{
          display: 'flex',
          background: focused ? '#1a2332' : '#131c2e',
          border: `2px solid ${focused ? '#4EA8DE' : '#2d3f5a'}`,
          borderRadius: 16,
          overflow: 'hidden',
          transition: 'all 0.2s ease',
          boxShadow: focused ? '0 0 0 4px rgba(78,168,222,0.15)' : 'none',
        }}>
          <span style={{
            padding: '14px 16px',
            fontSize: 20,
            display: 'flex',
            alignItems: 'center',
            color: '#4EA8DE',
          }}>🔮</span>
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="Type any concept: DNA, Black Hole, Democracy, Stack..."
            disabled={isLoading}
            style={{
              flex: 1,
              padding: '14px 8px',
              fontSize: 16,
              border: 'none',
              background: 'transparent',
              color: '#e6edf3',
              outline: 'none',
              fontFamily: 'Inter, sans-serif',
            }}
          />
          {query && (
            <button
              type="button"
              onClick={() => { setQuery(''); onReset?.(); }}
              style={{
                padding: '14px 12px',
                background: 'transparent',
                border: 'none',
                color: '#8b949e',
                cursor: 'pointer',
                fontSize: 18,
              }}
            >✕</button>
          )}
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            style={{
              padding: '14px 28px',
              background: isLoading ? '#2d3f5a' : 'linear-gradient(135deg, #0F9ED5, #156082)',
              color: '#fff',
              border: 'none',
              fontSize: 15,
              fontWeight: 600,
              cursor: isLoading || !query.trim() ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              fontFamily: 'Inter, sans-serif',
              letterSpacing: '0.3px',
              minWidth: 120,
            }}
          >
            {isLoading ? '⟳ Searching' : 'Visualize 3D →'}
          </button>
        </div>
      </form>

      {/* Suggestion chips */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 8,
        marginTop: 14,
      }}>
        {SUGGESTIONS.map(s => (
          <button
            key={s}
            onClick={() => handleSuggestion(s)}
            disabled={isLoading}
            style={{
              padding: '5px 14px',
              background: '#131c2e',
              border: '1px solid #2d3f5a',
              borderRadius: 20,
              color: '#8b949e',
              fontSize: 12,
              cursor: 'pointer',
              fontFamily: 'Inter, sans-serif',
              transition: 'all 0.15s',
            }}
            onMouseEnter={e => {
              e.target.style.borderColor = '#4EA8DE';
              e.target.style.color = '#4EA8DE';
            }}
            onMouseLeave={e => {
              e.target.style.borderColor = '#2d3f5a';
              e.target.style.color = '#8b949e';
            }}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
