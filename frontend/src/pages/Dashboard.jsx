/**
 * Dashboard page - Overview of sources and reports
 */

import React, { useEffect, useState } from 'react';
import api from '../services/api';
import './Dashboard.css';

function Dashboard() {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSources = async () => {
      try {
        const data = await api.listSources();
        setSources(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchSources();
  }, []);

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p>Overview of your data sources and recent activity</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-number">{sources.length}</div>
          <div className="stat-label">Data Sources</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">0</div>
          <div className="stat-label">Reports</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">0</div>
          <div className="stat-label">Q&A Sessions</div>
        </div>
      </div>

      <div className="sources-section">
        <div className="section-header">
          <h2>Data Sources</h2>
          <a href="/settings" className="action-button">
            + Add Source
          </a>
        </div>

        {sources.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📊</div>
            <div className="empty-state-title">No data sources yet</div>
            <div className="empty-state-description">
              Get started by adding your first data source
            </div>
            <a href="/settings">Add Data Source</a>
          </div>
        ) : (
          <div className="sources-grid">
            {sources.map((source) => (
              <div key={source.id} className="source-card">
                <div className="source-card-header">
                  <h3 className="source-card-title">{source.name}</h3>
                  <span className="source-card-type">{source.source_type}</span>
                </div>
                <p className="source-card-description">
                  {source.description || 'No description provided'}
                </p>
                <div className="source-card-meta">
                  <span>📦 {source.table_count || 0} tables</span>
                  <span>📝 {source.row_count || 0} rows</span>
                </div>
                <div className="source-card-actions">
                  <a href={`/inspect?source=${source.id}`}>
                    <button>Inspect</button>
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
