/**
 * Reports page - View and manage generated reports
 */

import React, { useState, useEffect } from 'react';
import api from '../services/api';

function Reports() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadReports = async () => {
      try {
        setLoading(true);
        // TODO: Implement reports API endpoint
        // const data = await api.listReports();
        setReports([]);
      } catch (err) {
        console.error('Failed to load reports:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadReports();
  }, []);

  if (loading) return <div className="loading">Loading reports...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="reports-page">
      <h1>Reports</h1>

      {reports.length === 0 ? (
        <div className="empty-state">
          <p>No reports generated yet</p>
          <p>
            <small>Reports are generated from inspection and Q&A sessions</small>
          </p>
        </div>
      ) : (
        <div className="reports-list">
          {reports.map((report) => (
            <div key={report.id} className="report-item">
              <h3>{report.title}</h3>
              <p>{report.description}</p>
              <p>Created: {new Date(report.created_at).toLocaleDateString()}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Reports;
