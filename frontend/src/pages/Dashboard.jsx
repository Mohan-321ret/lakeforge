/**
 * Handcrafted Dashboard Cockpit
 */

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import './Dashboard.css';

function Dashboard() {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [testingId, setTestingId] = useState(null);
  const [testResults, setTestResults] = useState({});

  useEffect(() => {
    let isMounted = true;
    const fetchSources = async () => {
      try {
        const data = await api.listSources();
        if (isMounted) setSources(data);
      } catch (err) {
        if (isMounted) setError(err.message);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchSources();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleTestPing = async (id, e) => {
    e.preventDefault();
    setTestingId(id);
    try {
      const res = await api.testConnection(id);
      setTestResults(prev => ({ ...prev, [id]: res.status === 'connected' ? '✓ Online' : '⚠️ Offline' }));
    } catch (err) {
      setTestResults(prev => ({ ...prev, [id]: '✗ Failed' }));
    } finally {
      setTestingId(null);
    }
  };

  if (loading) {
    return (
      <div className="dashboard" style={{ textAlign: 'center', padding: '100px 24px' }}>
        <span className="spinner" style={{ width: '28px', height: '28px' }}></span>
        <p style={{ marginTop: '16px', color: '#94a3b8', fontSize: '14px' }}>
          Initializing Lakeforge studio session...
        </p>
      </div>
    );
  }

  const totalTables = sources.reduce((acc, s) => acc + (s.table_count || 0), 0);

  return (
    <div className="dashboard">
      {/* Hero Bar */}
      <div className="dashboard-hero">
        <div className="hero-copy">
          <h1>
            <span>Data Platform Cockpit</span>
          </h1>
          <p>
            Local-first inspection, statistical profiling, privacy auditing, and natural-language Text-to-SQL.
          </p>
        </div>

        <div className="hero-actions">
          <Link to="/settings">
            <button>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              <span>Connect Database</span>
            </button>
          </Link>
        </div>
      </div>

      {error && <div className="alert-box alert-error">⚠️ {error}</div>}

      {/* Cockpit Metrics */}
      <div className="cockpit-grid">
        <div className="cockpit-card">
          <div className="cockpit-card-header">
            <span className="cockpit-card-title">Connected Sources</span>
            <div className="cockpit-card-icon">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>
            </div>
          </div>
          <div className="cockpit-card-value">{sources.length}</div>
          <div className="cockpit-card-sub">
            <span className="live-indicator"></span>
            <span>Active database connectors</span>
          </div>
        </div>

        <div className="cockpit-card">
          <div className="cockpit-card-header">
            <span className="cockpit-card-title">Tracked Tables</span>
            <div className="cockpit-card-icon">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>
            </div>
          </div>
          <div className="cockpit-card-value">{totalTables > 0 ? totalTables : 'Live'}</div>
          <div className="cockpit-card-sub">
            <span>Discovered schema entities</span>
          </div>
        </div>

        <div className="cockpit-card">
          <div className="cockpit-card-header">
            <span className="cockpit-card-title">AST Safety Guardrails</span>
            <div className="cockpit-card-icon" style={{ color: '#34d399' }}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
            </div>
          </div>
          <div className="cockpit-card-value" style={{ color: '#34d399' }}>100%</div>
          <div className="cockpit-card-sub">
            <span>Read-only SELECT / WITH enforced</span>
          </div>
        </div>

        <div className="cockpit-card">
          <div className="cockpit-card-header">
            <span className="cockpit-card-title">Query Reflection Loop</span>
            <div className="cockpit-card-icon" style={{ color: '#38bdf8' }}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
            </div>
          </div>
          <div className="cockpit-card-value" style={{ color: '#38bdf8' }}>2x Retry</div>
          <div className="cockpit-card-sub">
            <span>Self-correction on syntax/column errors</span>
          </div>
        </div>
      </div>

      {/* Multi-Dialect Support Launchpad */}
      <div className="dialect-banner">
        <div className="dialect-label">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><polygon points="10 8 16 12 10 16 10 8"></polygon></svg>
          <span>Multi-Engine Connector Grid:</span>
        </div>
        <div className="dialect-chips">
          <span className="dialect-chip">SQLite</span>
          <span className="dialect-chip">PostgreSQL</span>
          <span className="dialect-chip">MySQL</span>
          <span className="dialect-chip">SQL Server</span>
          <span className="dialect-chip">Oracle</span>
          <span className="dialect-chip">Databricks</span>
          <span className="dialect-chip">DuckDB</span>
          <span className="dialect-chip">DBeaver Sync</span>
        </div>
      </div>

      {/* Connected Sources */}
      <div className="sources-section">
        <div className="section-title-row">
          <h2>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>
            <span>Configured Data Sources ({sources.length})</span>
          </h2>
          <Link to="/settings" style={{ fontSize: '13px', fontWeight: 600 }}>
            Manage Connectors →
          </Link>
        </div>

        {sources.length === 0 ? (
          <div className="empty-hero-card">
            <div className="empty-icon-wrap">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#ffffff', marginBottom: '8px' }}>
              No Data Sources Configured
            </h3>
            <p style={{ color: '#94a3b8', fontSize: '14px', maxWidth: '480px', margin: '0 auto 20px' }}>
              Connect your local SQLite file, PostgreSQL, MySQL database, or import your saved DBeaver connections with one click.
            </p>
            <Link to="/settings">
              <button>+ Add Your First Source</button>
            </Link>
          </div>
        ) : (
          <div className="sources-grid">
            {sources.map((source) => {
              const testStatus = testResults[source.id];
              return (
                <div key={source.id} className="source-studio-card">
                  <div>
                    <div className="source-top-meta">
                      <span className="badge badge-int">{source.source_type}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {testStatus && (
                          <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: testStatus.includes('Online') ? '#34d399' : '#f87171' }}>
                            {testStatus}
                          </span>
                        )}
                        <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: '#64748b' }}>
                          {source.id}
                        </span>
                      </div>
                    </div>

                    <h3 className="source-name">{source.name}</h3>

                    <div className="source-uri-box" title={source.uri}>
                      <span>{source.uri}</span>
                    </div>

                    <p className="source-desc">
                      {source.description || 'Configured database connector ready for discovery and Q&A.'}
                    </p>
                  </div>

                  <div>
                    <div className="source-footer-metrics">
                      <span>📦 {source.table_count || 'Multi'} tables</span>
                      <button
                        type="button"
                        onClick={(e) => handleTestPing(source.id, e)}
                        disabled={testingId === source.id}
                        style={{
                          background: 'none',
                          border: 'none',
                          boxShadow: 'none',
                          padding: 0,
                          fontSize: '12px',
                          color: '#38bdf8',
                          cursor: 'pointer',
                        }}
                      >
                        {testingId === source.id ? 'Pinging...' : '⚡ Ping Connection'}
                      </button>
                    </div>

                    <div className="source-btn-row">
                      <Link to={`/inspect?source=${source.id}`}>
                        <button style={{ width: '100%' }}>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                          <span>Inspect</span>
                        </button>
                      </Link>
                      <Link to={`/qa?source=${source.id}`}>
                        <button type="button" className="btn-secondary" style={{ width: '100%' }}>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                          <span>Ask Q&A</span>
                        </button>
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
