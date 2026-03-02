import { useState } from 'react';

const EXAMPLES = ['Human Heart', 'Binary Search Tree', 'Eiffel Tower', 'Democracy', 'DNA', 'Solar System'];

export function SearchBar({ onSearch, isLoading, onReset, hasResult }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isLoading) onSearch(query.trim());
  };

  return (
    <div>
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8 }}>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Try: Human Heart, Binary Tree, Eiffel Tower, Democracy..."
          disabled={isLoading}
          style={{
            flex: 1,
            padding: '12px 16px',
            fontSize: 16,
            background: '#161b22',
            border: '2px solid #30363d',
            borderRadius: 10,
            color: '#e6edf3',
            outline: 'none',
            transition: 'border-color 0.2s',
          }}
          onFocus={e => e.target.style.borderColor = '#4EA8DE'}
          onBlur={e => e.target.style.borderColor = '#30363d'}
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          style={{
            padding: '12px 28px',
            background: isLoading ? '#21262d' : 'linear-gradient(135deg, #156082, #0F9ED5)',
            color: isLoading ? '#8b949e' : '#fff',
            border: 'none',
            borderRadius: 10,
            fontSize: 15,
            fontWeight: 600,
            cursor: isLoading || !query.trim() ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
            whiteSpace: 'nowrap',
          }}
        >
          {isLoading ? 'Searching...' : '🔍 Search 3D'}
        </button>
        {hasResult && (
          <button
            type="button"
            onClick={() => { onReset(); setQuery(''); }}
            style={{
              padding: '12px 16px',
              background: 'transparent',
              color: '#8b949e',
              border: '2px solid #30363d',
              borderRadius: 10,
              fontSize: 14,
              cursor: 'pointer',
            }}
          >
            ✕ Reset
          </button>
        )}
      </form>
      <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
        <span style={{ color: '#8b949e', fontSize: 13, alignSelf: 'center' }}>Try:</span>
        {EXAMPLES.map(ex => (
          <button
            key={ex}
            onClick={() => { setQuery(ex); if (!isLoading) onSearch(ex); }}
            disabled={isLoading}
            style={{
              padding: '4px 12px',
              background: '#21262d',
              border: '1px solid #30363d',
              borderRadius: 20,
              color: '#8b949e',
              fontSize: 12,
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
            onMouseEnter={e => { e.target.style.color = '#4EA8DE'; e.target.style.borderColor = '#4EA8DE'; }}
            onMouseLeave={e => { e.target.style.color = '#8b949e'; e.target.style.borderColor = '#30363d'; }}
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}
