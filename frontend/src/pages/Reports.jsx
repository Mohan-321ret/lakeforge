/**
 * Reports page - View and generate data inspection and privacy audit reports
 */

import React, { useState, useEffect } from 'react';
import api from '../services/api';
import './Reports.css';

function Reports() {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [reportsList, setReportsList] = useState([]);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const loadData = async () => {
      try {
        setLoading(true);
        const srcData = await api.listSources();
        if (isMounted) {
          setSources(srcData);
          // Initialize available sample reports
          const initialReports = srcData.map((s) => ({
            id: `rep_${s.id}`,
            sourceId: s.id,
            sourceName: s.name,
            sourceType: s.source_type,
            title: `${s.name} Data Audit Report`,
            description: `Automated schema catalog, statistical profile, and PII compliance audit for ${s.name}.`,
            createdAt: new Date().toLocaleDateString(),
            status: 'Ready',
          }));
          setReportsList(initialReports);
        }
      } catch (err) {
        console.error('Failed to load sources for reports:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleGenerateReport = async (source) => {
    setGenerating(true);
    try {
      // Start an inspection session to get fresh schema and profile
      const insp = await api.startInspection({
        source_id: source.id,
        include_profile: true,
        sample_size: 100,
      });

      const schemaRes = await api.getSchema(insp.session_id);
      const profileRes = await api.getProfile(insp.session_id);

      const schema = schemaRes.schema || {};
      const profile = profileRes.profile || {};
      const tables = schema.tables || {};

      // Build structured Markdown report
      let md = `# Lakeforge Source Inspection & Privacy Audit Report\n\n`;
      md += `**Data Source:** ${source.name} (${source.source_type})\n`;
      md += `**Generated Date:** ${new Date().toISOString()}\n`;
      md += `**Connection URI:** \`${source.uri}\`\n\n`;
      md += `---\n\n`;

      md += `## 1. Executive Summary\n\n`;
      const tableNames = Object.keys(tables);
      md += `- **Total Tables Discovered:** ${tableNames.length}\n`;

      let totalPiiCount = 0;
      if (profile.tables) {
        Object.values(profile.tables).forEach((tp) => {
          if (tp.pii_columns) {
            totalPiiCount += Object.keys(tp.pii_columns).length;
          }
        });
      }
      md += `- **PII Columns Flagged:** ${totalPiiCount} ${totalPiiCount > 0 ? '⚠️ (Action Required)' : '✅ (Clean)'}\n`;
      md += `- **AST Guardrails:** Enforced by Lakeforge SQLValidator\n\n`;

      md += `## 2. Table Catalog & Schema Details\n\n`;
      for (const [tName, tMeta] of Object.entries(tables)) {
        md += `### Table: \`${tName}\`\n`;
        md += `- **Estimated Rows:** ${tMeta.row_count ?? 'Unknown'}\n`;
        md += `- **Column Count:** ${tMeta.columns ? Object.keys(tMeta.columns).length : 0}\n\n`;
        md += `| Column | Data Type | Nullable | PII Type |\n`;
        md += `| :--- | :--- | :--- | :--- |\n`;

        const piiCols = profile?.tables?.[tName]?.pii_columns || {};
        if (tMeta.columns) {
          for (const [colName, colMeta] of Object.entries(tMeta.columns)) {
            const piiType = piiCols[colName] || '—';
            md += `| \`${colName}\` | ${colMeta.type || 'TEXT'} | ${colMeta.nullable !== false ? 'Yes' : 'No'} | ${piiType} |\n`;
          }
        }
        md += `\n`;
      }

      md += `## 3. Privacy & Compliance Recommendations\n\n`;
      if (totalPiiCount > 0) {
        md += `The automated privacy scanner identified sensitive columns. Recommendation:\n`;
        md += `- Apply deterministic or salt-hashed masking (\`PIIMasker\`) before staging data to analytics lakehouse.\n`;
        md += `- Restrict Text-to-SQL direct SELECT permissions on sensitive customer columns.\n`;
      } else {
        md += `No high-risk PII identifiers detected in sampled datasets.\n`;
      }

      setSelectedReport({
        title: `${source.name} Inspection Report`,
        markdown: md,
        sourceName: source.name,
      });
    } catch (err) {
      alert(`Report generation failed: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  const copyMarkdown = () => {
    if (selectedReport?.markdown) {
      navigator.clipboard.writeText(selectedReport.markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const downloadMarkdown = () => {
    if (!selectedReport?.markdown) return;
    const blob = new Blob([selectedReport.markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedReport.sourceName}_Audit_Report.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="reports-page" style={{ textAlign: 'center', padding: '60px 20px' }}>
        <span className="spinner" style={{ width: '32px', height: '32px', borderColor: 'rgba(37, 99, 235, 0.2)', borderTopColor: '#2563eb' }}></span>
        <p style={{ marginTop: '16px', color: '#64748b' }}>Loading report manager...</p>
      </div>
    );
  }

  return (
    <div className="reports-page">
      <div className="reports-header">
        <div>
          <h1>📑 Inspection & Audit Reports</h1>
          <p>Generate comprehensive technical audits, schema dictionaries, and privacy compliance summaries.</p>
        </div>
      </div>

      {sources.length === 0 ? (
        <div className="panel-card" style={{ textAlign: 'center', padding: '48px 20px' }}>
          <div style={{ fontSize: '40px', marginBottom: '12px' }}>📊</div>
          <h3>No Data Sources Available</h3>
          <p style={{ color: '#64748b', marginTop: '8px' }}>
            Add a data source under Settings to generate inspection and compliance reports.
          </p>
        </div>
      ) : (
        <div className="reports-grid">
          {sources.map((src) => (
            <div key={src.id} className="report-card">
              <div>
                <div className="report-card-header">
                  <h3 className="report-title">{src.name}</h3>
                  <span className="report-badge badge-int">{src.source_type}</span>
                </div>
                <p className="report-desc">
                  Generates an end-to-end data dictionary, column-level profiling metrics, and automated PII risk assessment.
                </p>
              </div>

              <div>
                <div className="report-meta">
                  <span>🔗 {src.source_type}</span>
                  <span>📦 {src.table_count || 'Multi'} tables</span>
                </div>
                <div className="report-actions">
                  <button
                    onClick={() => handleGenerateReport(src)}
                    disabled={generating}
                    style={{ width: '100%' }}
                  >
                    {generating ? (
                      <>
                        <span className="spinner"></span> Generating...
                      </>
                    ) : (
                      '⚡ Generate & View Audit Report'
                    )}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Report Modal */}
      {selectedReport && (
        <div className="report-modal-overlay" onClick={() => setSelectedReport(null)}>
          <div className="report-modal" onClick={(e) => e.stopPropagation()}>
            <div className="report-modal-header">
              <h3 style={{ fontSize: '18px', fontWeight: 600 }}>{selectedReport.title}</h3>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setSelectedReport(null)}
                style={{ padding: '4px 10px' }}
              >
                ✕ Close
              </button>
            </div>
            <div className="report-modal-body">
              <pre className="report-markdown-preview">
                {selectedReport.markdown}
              </pre>
            </div>
            <div className="report-modal-footer">
              <button type="button" className="btn-secondary" onClick={copyMarkdown}>
                {copied ? '✓ Copied Markdown!' : '📋 Copy Markdown'}
              </button>
              <button type="button" onClick={downloadMarkdown}>
                ⬇️ Download .md Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Reports;
