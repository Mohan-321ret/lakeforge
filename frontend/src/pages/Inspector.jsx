/**
 * Handcrafted Inspector Studio Interface
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useInspection } from '../hooks/useInspection';
import './Inspector.css';

function getTypeBadgeClass(typeStr) {
  if (!typeStr) return 'badge-text';
  const t = typeStr.toLowerCase();
  if (t.includes('int') || t.includes('numeric') || t.includes('real') || t.includes('float') || t.includes('double')) {
    return 'badge-int';
  }
  if (t.includes('char') || t.includes('text') || t.includes('str')) {
    return 'badge-text';
  }
  if (t.includes('date') || t.includes('time')) {
    return 'badge-date';
  }
  if (t.includes('bool')) {
    return 'badge-bool';
  }
  return 'badge-text';
}

function Inspector() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const urlSource = searchParams.get('source') || searchParams.get('source_id') || '';

  const [sourceId, setSourceId] = useState(urlSource);
  const [sources, setSources] = useState([]);
  const [activeTab, setActiveTab] = useState('schema'); // 'schema' | 'profile' | 'samples'
  const [selectedTable, setSelectedTable] = useState('');
  const [columnFilter, setColumnFilter] = useState('');

  const {
    sessionId,
    status,
    schema,
    profile,
    samples,
    loading,
    error,
    fetchSchema,
    fetchProfile,
    fetchSamples,
  } = useInspection();

  useEffect(() => {
    let isMounted = true;
    const loadSources = async () => {
      try {
        const data = await api.listSources();
        if (isMounted) {
          setSources(data);
          if (urlSource && data.some((s) => s.id === urlSource)) {
            setSourceId(urlSource);
            triggerInspection(urlSource);
          }
        }
      } catch (err) {
        console.error('Failed to load sources:', err);
      }
    };
    loadSources();
    return () => {
      isMounted = false;
    };
  }, [urlSource]);

  const triggerInspection = async (idToInspect) => {
    const targetId = idToInspect || sourceId;
    if (!targetId) return;

    try {
      const result = await api.startInspection({
        source_id: targetId,
        include_profile: true,
        sample_size: 100,
      });

      await fetchSchema(result.session_id);
      await fetchProfile(result.session_id);
      await fetchSamples(result.session_id, 100);
    } catch (err) {
      console.error('Inspection failed:', err);
    }
  };

  const handleInspectClick = () => {
    if (!sourceId) {
      alert('Please select a data source first.');
      return;
    }
    triggerInspection(sourceId);
  };

  const tablesList = useMemo(() => {
    if (schema?.tables) {
      return Object.keys(schema.tables);
    }
    if (profile?.tables) {
      return Object.keys(profile.tables);
    }
    return [];
  }, [schema, profile]);

  useEffect(() => {
    if (tablesList.length > 0 && (!selectedTable || !tablesList.includes(selectedTable))) {
      setSelectedTable(tablesList[0]);
    }
  }, [tablesList, selectedTable]);

  const currentTableSchema = schema?.tables?.[selectedTable];
  const currentTableProfile = profile?.tables?.[selectedTable];
  const currentTableSamples = samples?.[selectedTable] || [];

  const totalRowCount = currentTableProfile?.row_count ?? currentTableSchema?.row_count ?? 0;
  const totalCols = currentTableSchema?.columns ? Object.keys(currentTableSchema.columns).length : 0;
  const piiColumns = currentTableProfile?.pii_columns || {};
  const piiCount = Object.keys(piiColumns).length;

  // Filter columns
  const filteredColumns = useMemo(() => {
    if (!currentTableSchema?.columns) return [];
    const entries = Object.entries(currentTableSchema.columns);
    if (!columnFilter.trim()) return entries;
    const lower = columnFilter.toLowerCase();
    return entries.filter(([colName, colMeta]) => {
      const colType = (colMeta.type || colMeta.data_type || '').toLowerCase();
      return colName.toLowerCase().includes(lower) || colType.includes(lower);
    });
  }, [currentTableSchema, columnFilter]);

  return (
    <div className="inspector">
      <div className="inspector-hero">
        <h1>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <span>Data Inspector Studio</span>
        </h1>
        <p>Inspect deep structural schemas, distribution statistics, and automatic privacy compliance auditing.</p>
      </div>

      {/* Control Bar */}
      <div className="inspector-control-deck">
        <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
          <option value="">Select a data source...</option>
          {sources.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name} ({s.source_type})
            </option>
          ))}
        </select>

        <button onClick={handleInspectClick} disabled={loading || !sourceId}>
          {loading ? (
            <>
              <span className="spinner"></span> Inspecting...
            </>
          ) : (
            'Execute Inspection ⚡'
          )}
        </button>

        {sourceId && (
          <button
            type="button"
            className="btn-secondary"
            onClick={() => navigate(`/qa?source=${sourceId}`)}
          >
            💬 Open Q&A Console
          </button>
        )}

        {status && (
          <div className="session-badge-pill" style={{ marginLeft: 'auto' }}>
            STATUS: {status.toUpperCase()} {sessionId && `• ${sessionId}`}
          </div>
        )}
      </div>

      {error && <div className="alert-box alert-error">⚠️ {error}</div>}

      {tablesList.length > 0 && (
        <>
          {/* Table Selector Strip */}
          <div className="table-selector-strip">
            <span className="table-strip-label">Entities:</span>
            {tablesList.map((tName) => {
              const rCount = schema?.tables?.[tName]?.row_count ?? 0;
              return (
                <button
                  key={tName}
                  type="button"
                  className={`table-studio-pill ${selectedTable === tName ? 'active' : ''}`}
                  onClick={() => {
                    setSelectedTable(tName);
                    setColumnFilter('');
                  }}
                >
                  <span>📋 {tName}</span>
                  <span className="table-pill-count">{rCount}</span>
                </button>
              );
            })}
          </div>

          {/* Metric Overview Row */}
          <div className="inspector-metrics-grid">
            <div className="studio-stat-card">
              <div className="stat-label">Active Entity</div>
              <div className="stat-value" style={{ fontSize: '20px', fontFamily: 'var(--font-mono)' }}>
                {selectedTable}
              </div>
              <div className="stat-subtext">Table entity</div>
            </div>
            <div className="studio-stat-card">
              <div className="stat-label">Record Count</div>
              <div className="stat-value">{totalRowCount.toLocaleString()}</div>
              <div className="stat-subtext">Indexed rows</div>
            </div>
            <div className="studio-stat-card">
              <div className="stat-label">Schema Columns</div>
              <div className="stat-value">{totalCols}</div>
              <div className="stat-subtext">Typed attributes</div>
            </div>
            <div className="studio-stat-card">
              <div className="stat-label">PII Risk Flags</div>
              <div className="stat-value" style={{ color: piiCount > 0 ? '#fb7185' : '#34d399' }}>
                {piiCount}
              </div>
              <div className="stat-subtext">{piiCount > 0 ? 'Sensitive data flagged' : 'Clean of sensitive PII'}</div>
            </div>
          </div>

          {/* Studio Tab Bar */}
          <div className="inspector-tab-bar">
            <button
              type="button"
              className={`studio-tab-btn ${activeTab === 'schema' ? 'active' : ''}`}
              onClick={() => setActiveTab('schema')}
            >
              📑 Schema & Dictionary
            </button>
            <button
              type="button"
              className={`studio-tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
              onClick={() => setActiveTab('profile')}
            >
              📊 Profiling & Statistics
            </button>
            <button
              type="button"
              className={`studio-tab-btn ${activeTab === 'samples' ? 'active' : ''}`}
              onClick={() => setActiveTab('samples')}
            >
              🔬 Live Sample Grid
            </button>
          </div>

          {/* TAB 1: SCHEMA VIEW */}
          {activeTab === 'schema' && (
            <div className="studio-table-container">
              <div className="studio-table-header">
                <span className="studio-table-title">
                  <span>Schema Attributes for</span>
                  <code style={{ color: '#38bdf8' }}>{selectedTable}</code>
                </span>

                <div className="filter-input-wrap">
                  <svg className="filter-search-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                  <input
                    type="text"
                    placeholder="Filter columns..."
                    value={columnFilter}
                    onChange={(e) => setColumnFilter(e.target.value)}
                  />
                </div>
              </div>

              <div className="studio-table-wrapper">
                <table className="studio-grid">
                  <thead>
                    <tr>
                      <th>Column Identifier</th>
                      <th>Data Type</th>
                      <th>Nullability</th>
                      <th>Privacy Audit</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredColumns.map(([colName, colInfo]) => {
                      const colType = colInfo.type || colInfo.data_type || 'VARCHAR';
                      const isNullable = colInfo.nullable !== false;
                      const isPII = piiColumns[colName];

                      return (
                        <tr key={colName}>
                          <td>
                            <div className="col-ident">
                              <span>{colName}</span>
                            </div>
                          </td>
                          <td>
                            <span className={`badge ${getTypeBadgeClass(colType)}`}>
                              {colType}
                            </span>
                          </td>
                          <td>
                            <span className={`badge ${isNullable ? 'badge-nullable' : 'badge-not-null'}`}>
                              {isNullable ? 'NULLABLE' : 'NOT NULL'}
                            </span>
                          </td>
                          <td>
                            {isPII ? (
                              <span className="badge badge-pii">
                                🛡️ {isPII.toUpperCase()}
                              </span>
                            ) : (
                              <span style={{ color: '#64748b', fontSize: '12px' }}>Clean</span>
                            )}
                          </td>
                          <td style={{ color: '#94a3b8', fontSize: '13px' }}>
                            {colInfo.description || '—'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 2: PROFILE & STATS VIEW */}
          {activeTab === 'profile' && (
            <div>
              {piiCount > 0 && (
                <div className="threat-card">
                  <div className="threat-icon">🛡️</div>
                  <div className="threat-body">
                    <h4>Sensitive PII Identified in {selectedTable}</h4>
                    <p>
                      Automated privacy scanners identified {piiCount} sensitive column(s). Masking is recommended before downstream lakehouse export.
                    </p>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {Object.entries(piiColumns).map(([cName, pType]) => (
                        <span key={cName} className="badge badge-pii">
                          {cName}: {pType}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              <div className="studio-table-container">
                <div className="studio-table-header">
                  <span className="studio-table-title">
                    <span>Distribution & Cardinality Metrics</span>
                  </span>
                  <span style={{ fontSize: '12px', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                    SAMPLE: {currentTableProfile?.sample_count ?? 0} ROWS
                  </span>
                </div>

                <div className="studio-table-wrapper">
                  <table className="studio-grid">
                    <thead>
                      <tr>
                        <th>Column</th>
                        <th>Type</th>
                        <th>Null Rate</th>
                        <th>Distinct Count</th>
                        <th>Observed Range</th>
                        <th>Top Frequency Distribution</th>
                      </tr>
                    </thead>
                    <tbody>
                      {currentTableProfile?.columns &&
                        Object.entries(currentTableProfile.columns).map(([colName, colData]) => {
                          const stats = colData.stats || {};
                          const nullPct = Math.round((stats.null_rate || 0) * 100);
                          const nullClass = nullPct > 20 ? 'bad' : nullPct > 5 ? 'warn' : 'good';
                          const topVals = stats.top_values || [];

                          return (
                            <tr key={colName}>
                              <td>
                                <span className="col-ident">{colName}</span>
                              </td>
                              <td>
                                <span className={`badge ${getTypeBadgeClass(colData.type)}`}>
                                  {colData.type}
                                </span>
                              </td>
                              <td>
                                <div className="null-track">
                                  <div className="null-bar-outer">
                                    <div
                                      className={`null-bar-inner ${nullClass}`}
                                      style={{ width: `${Math.min(nullPct, 100)}%` }}
                                    ></div>
                                  </div>
                                  <span className="null-percent-label">{nullPct}%</span>
                                </div>
                              </td>
                              <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                                {stats.distinct_count !== undefined ? stats.distinct_count : '—'}
                              </td>
                              <td style={{ fontSize: '12px', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
                                {stats.min !== undefined || stats.max !== undefined
                                  ? `[${stats.min ?? '—'} .. ${stats.max ?? '—'}]`
                                  : '—'}
                              </td>
                              <td>
                                {topVals.length > 0 ? (
                                  <div className="chips-cluster">
                                    {topVals.map((item, idx) => (
                                      <span key={idx} className="freq-chip">
                                        <span>{String(item.value)}</span>
                                        <span className="freq-count">{item.count}</span>
                                      </span>
                                    ))}
                                  </div>
                                ) : (
                                  <span style={{ color: '#64748b', fontSize: '12px' }}>—</span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: DATA SAMPLES VIEW */}
          {activeTab === 'samples' && (
            <div className="studio-table-container">
              <div className="studio-table-header">
                <span className="studio-table-title">
                  <span>Sample Grid:</span>
                  <code style={{ color: '#38bdf8' }}>{selectedTable}</code>
                </span>
                <span style={{ fontSize: '12px', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                  SHOWING {currentTableSamples.length} RECORD(S)
                </span>
              </div>

              {currentTableSamples.length > 0 ? (
                <div className="studio-table-wrapper">
                  <table className="studio-grid">
                    <thead>
                      <tr>
                        <th style={{ width: '45px' }}>#</th>
                        {Object.keys(currentTableSamples[0]).map((key) => (
                          <th key={key}>{key}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {currentTableSamples.map((row, rowIdx) => (
                        <tr key={rowIdx}>
                          <td style={{ color: '#64748b', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                            {rowIdx + 1}
                          </td>
                          {Object.values(row).map((val, colIdx) => (
                            <td key={colIdx}>
                              {val === null || val === undefined ? (
                                <span style={{ color: '#475569', fontStyle: 'italic', fontFamily: 'var(--font-mono)' }}>
                                  NULL
                                </span>
                              ) : (
                                String(val)
                              )}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '48px 20px', color: '#64748b' }}>
                  No sample records loaded for table <code>{selectedTable}</code>.
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Inspector;
