/**
 * Inspector page - Data inspection interface
 */

import React, { useState } from 'react';
import api from '../services/api';
import { useInspection } from '../hooks/useInspection';

function Inspector() {
  const [sourceId, setSourceId] = useState('');
  const [sources, setSources] = useState([]);
  const { sessionId, status, schema, profile, samples, loading, fetchSchema, fetchProfile, fetchSamples } = useInspection();

  React.useEffect(() => {
    const loadSources = async () => {
      try {
        const data = await api.listSources();
        setSources(data);
      } catch (err) {
        console.error('Failed to load sources:', err);
      }
    };
    loadSources();
  }, []);

  const handleInspect = async () => {
    if (!sourceId) {
      alert('Please select a source');
      return;
    }

    try {
      const result = await api.startInspection({
        source_id: sourceId,
        include_profile: true,
      });
      // Fetch schema and profile
      await fetchSchema(result.session_id);
      await fetchProfile(result.session_id);
    } catch (err) {
      console.error('Inspection failed:', err);
      alert('Inspection failed: ' + err.message);
    }
  };

  return (
    <div className="inspector">
      <h1>Data Inspector</h1>

      <div className="inspector-controls">
        <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
          <option value="">Select a data source...</option>
          {sources.map((source) => (
            <option key={source.id} value={source.id}>
              {source.name} ({source.source_type})
            </option>
          ))}
        </select>
        <button onClick={handleInspect} disabled={loading || !sourceId}>
          {loading ? 'Inspecting...' : 'Start Inspection'}
        </button>
      </div>

      {status && (
        <div className="inspector-status">
          <p>Status: <strong>{status}</strong></p>
        </div>
      )}

      {schema && (
        <div className="inspector-results">
          <div className="schema-section">
            <h2>Schema</h2>
            <pre>{JSON.stringify(schema, null, 2)}</pre>
          </div>
        </div>
      )}

      {profile && (
        <div className="profile-section">
          <h2>Profile</h2>
          <pre>{JSON.stringify(profile, null, 2)}</pre>
        </div>
      )}

      {samples && (
        <div className="samples-section">
          <h2>Samples</h2>
          <pre>{JSON.stringify(samples, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default Inspector;
