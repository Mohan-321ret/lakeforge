/**
 * Handcrafted Natural Language Q&A Studio Console
 */

import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../services/api';
import './QA.css';

const SAMPLE_PROMPTS = [
  'How many customers are in the database?',
  'What is the total amount of all orders?',
  'List top 5 orders by amount with their details',
  'Show me customer names and their email addresses',
  'How many orders were placed by each customer?',
];

function QueryCardItem({ item, index }) {
  const [copied, setCopied] = useState(false);

  const copySql = () => {
    if (item.generated_sql) {
      navigator.clipboard.writeText(item.generated_sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const resultsData = Array.isArray(item.results) ? item.results : [];
  const resultColumns = resultsData.length > 0 && typeof resultsData[0] === 'object'
    ? Object.keys(resultsData[0])
    : [];

  const downloadCSV = () => {
    if (resultsData.length === 0 || resultColumns.length === 0) return;
    const header = resultColumns.join(',');
    const rows = resultsData.map((row) =>
      resultColumns.map((col) => JSON.stringify(row[col] ?? '')).join(',')
    );
    const csvContent = [header, ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query_result_${index + 1}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="query-card">
      <div className="query-card-top">
        <div className="question-text">
          <span className="turn-pill">TURN #{index + 1}</span>
          <span>"{item.question}"</span>
        </div>

        <div className="meta-chips-row">
          {item.self_corrected && (
            <span className="chip-status chip-corrected">
              ⚡ AUTO-CORRECTED ({item.attempts} ATTEMPTS)
            </span>
          )}
          <span
            className={`chip-status ${
              item.execution_status === 'success' ? 'chip-success' : 'chip-error'
            }`}
          >
            {item.execution_status === 'success' ? '✓ EXECUTED' : '✗ FAILED'}
          </span>
          {item.execution_time_ms !== undefined && (
            <span className="chip-status chip-time">
              ⏱️ {Number(item.execution_time_ms).toFixed(1)} ms
            </span>
          )}
        </div>
      </div>

      {item.corrections && item.corrections.length > 0 && (
        <div className="corrections-ribbon">
          <span>🛠️ <strong>Reflection Fix Applied:</strong> {item.corrections.join('; ')}</span>
        </div>
      )}

      {item.error_message && (
        <div style={{ padding: '14px 22px', backgroundColor: 'rgba(239, 68, 68, 0.1)', borderBottom: '1px solid rgba(239, 68, 68, 0.25)', color: '#fca5a5', fontSize: '13.5px' }}>
          <strong>Execution Error:</strong> {item.error_message}
        </div>
      )}

      {item.generated_sql && (
        <div className="sql-deck">
          <div className="sql-deck-bar">
            <span>VERIFIED AST-SAFE SQL</span>
            <button type="button" className="btn-secondary" onClick={copySql} style={{ padding: '4px 10px', fontSize: '11.5px' }}>
              {copied ? '✓ Copied!' : '📋 Copy Query'}
            </button>
          </div>
          <pre className="sql-view-code">
            <code>{item.generated_sql}</code>
          </pre>
        </div>
      )}

      <div className="results-deck">
        <div className="results-deck-toolbar">
          <h3>
            <span>Query Results</span>
            <span style={{ fontSize: '12.5px', color: '#64748b', marginLeft: '10px', fontWeight: 500 }}>
              ({resultsData.length} records returned)
            </span>
          </h3>

          {resultsData.length > 0 && (
            <button type="button" className="btn-secondary" onClick={downloadCSV} style={{ padding: '5px 12px', fontSize: '12px' }}>
              ⬇️ Export CSV
            </button>
          )}
        </div>

        {resultsData.length > 0 && resultColumns.length > 0 ? (
          <div className="results-table-shell">
            <table className="studio-grid">
              <thead>
                <tr>
                  <th style={{ width: '45px' }}>#</th>
                  {resultColumns.map((col) => (
                    <th key={col}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {resultsData.map((row, rowIdx) => (
                  <tr key={rowIdx}>
                    <td style={{ color: '#64748b', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                      {rowIdx + 1}
                    </td>
                    {resultColumns.map((col) => {
                      const val = row[col];
                      return (
                        <td key={col}>
                          {val === null || val === undefined ? (
                            <span style={{ color: '#475569', fontStyle: 'italic', fontFamily: 'var(--font-mono)' }}>
                              NULL
                            </span>
                          ) : (
                            String(val)
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '36px 16px', color: '#64748b', fontSize: '13.5px' }}>
            {item.execution_status === 'success'
              ? 'Query executed cleanly but returned zero rows.'
              : 'No results available due to query error.'}
          </div>
        )}
      </div>
    </div>
  );
}

function QA() {
  const [searchParams] = useSearchParams();
  const urlSource = searchParams.get('source') || searchParams.get('source_id') || '';

  const [sourceId, setSourceId] = useState(urlSource);
  const [sessionId, setSessionId] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [question, setQuestion] = useState('');
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const loadSources = async () => {
      try {
        const data = await api.listSources();
        if (isMounted) {
          setSources(data);
          if (urlSource && data.some((s) => s.id === urlSource)) {
            setSourceId(urlSource);
          } else if (data.length > 0 && !sourceId) {
            setSourceId(data[0].id);
          }
        }
      } catch (err) {
        if (isMounted) setError('Failed to load data sources');
      }
    };
    loadSources();
    return () => {
      isMounted = false;
    };
  }, [urlSource]);

  const handleNewChat = () => {
    setSessionId(null);
    setChatHistory([]);
    setQuestion('');
    setError(null);
  };

  const handleAsk = async () => {
    if (!sourceId || !question.trim()) {
      alert('Please select a data source and enter a question.');
      return;
    }

    setLoading(true);
    setError(null);

    const questionToSend = question.trim();

    try {
      const data = await api.askQuestion({
        source_id: sourceId,
        question: questionToSend,
        session_id: sessionId,
      });

      if (data.session_id) {
        setSessionId(data.session_id);
      }

      setChatHistory((prev) => [data, ...prev]);
      setQuestion('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleAsk();
    }
  };

  return (
    <div className="qa-page">
      <div className="qa-hero">
        <h1>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth="2.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
          <span>Natural Language SQL Studio</span>
        </h1>
        <p>Ask plain English questions — Lakeforge generates verified, AST-safe SQL and executes directly against your live database.</p>
      </div>

      <div className="qa-console-box">
        <div className="qa-source-strip">
          <select
            id="qa-source-select"
            value={sourceId}
            onChange={(e) => {
              setSourceId(e.target.value);
              handleNewChat();
            }}
          >
            <option value="">Select data source connector...</option>
            {sources.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.source_type})
              </option>
            ))}
          </select>

          {chatHistory.length > 0 && (
            <button type="button" className="btn-secondary" onClick={handleNewChat}>
              ✨ Clear & New Session
            </button>
          )}
        </div>

        <div className="qa-query-field">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              chatHistory.length > 0
                ? "Ask a follow-up query (e.g. 'filter for completed status only', 'sort by total amount desc')..."
                : "Ask anything about your data... e.g. 'What is the total order amount per customer?'"
            }
            rows={3}
          />
        </div>

        {/* Suggested Prompts */}
        <div className="suggested-prompts-row">
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#64748b' }}>Quick prompts:</span>
          {SAMPLE_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              className="prompt-badge-chip"
              onClick={() => setQuestion(p)}
            >
              {p}
            </button>
          ))}
        </div>

        <div className="qa-console-actions">
          <span className="keyboard-shortcut-hint">
            Shortcut: <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to execute
          </span>
          <button onClick={handleAsk} disabled={loading || !sourceId || !question.trim()}>
            {loading ? (
              <>
                <span className="spinner"></span> Generating & Executing...
              </>
            ) : (
              'Execute Query 🚀'
            )}
          </button>
        </div>
      </div>

      {error && <div className="alert-box alert-error">⚠️ {error}</div>}

      {/* Conversation Thread */}
      {chatHistory.length > 0 && (
        <div className="thread-container">
          {chatHistory.map((item, idx) => (
            <QueryCardItem key={idx} item={item} index={chatHistory.length - 1 - idx} />
          ))}
        </div>
      )}
    </div>
  );
}

export default QA;
