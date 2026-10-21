/**
 * Q&A page - Ask natural language questions about data
 */

import React, { useState } from 'react';
import api from '../services/api';

function QA() {
  const [sourceId, setSourceId] = useState('');
  const [question, setQuestion] = useState('');
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  React.useEffect(() => {
    const loadSources = async () => {
      try {
        const data = await api.listSources();
        setSources(data);
      } catch (err) {
        console.error('Failed to load sources:', err);
        setError('Failed to load sources');
      }
    };
    loadSources();
  }, []);

  const handleAsk = async () => {
    if (!sourceId || !question) {
      alert('Please select a source and enter a question');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.askQuestion({
        source_id: sourceId,
        question: question,
      });
      setResult(data);
    } catch (err) {
      console.error('Q&A failed:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="qa-page">
      <h1>Q&A - Ask Questions About Your Data</h1>

      <div className="qa-input">
        <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
          <option value="">Select a data source...</option>
          {sources.map((source) => (
            <option key={source.id} value={source.id}>
              {source.name} ({source.source_type})
            </option>
          ))}
        </select>

        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your data... e.g., 'How many customers are in the database?'"
          rows={4}
        />

        <button onClick={handleAsk} disabled={loading || !sourceId || !question}>
          {loading ? 'Processing...' : 'Ask Question'}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="qa-result">
          <div className="result-section">
            <h3>Question</h3>
            <p>{result.question}</p>
          </div>

          <div className="result-section">
            <h3>Generated SQL</h3>
            <pre><code>{result.generated_sql}</code></pre>
          </div>

          <div className="result-section">
            <h3>Results</h3>
            {result.results ? (
              <pre>{JSON.stringify(result.results, null, 2)}</pre>
            ) : (
              <p className="no-results">No results</p>
            )}
          </div>

          {result.execution_time_ms && (
            <div className="result-meta">
              <p>Execution time: {result.execution_time_ms}ms</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default QA;
