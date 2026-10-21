/**
 * Settings page - Manage data sources and configuration
 */

import React, { useState, useEffect } from 'react';
import api from '../services/api';
import './Settings.css';

function Settings() {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [showDBeaver, setShowDBeaver] = useState(false);
  const [dbeaverConnections, setDBeaverConnections] = useState([]);
  const [dbeaverLoading, setDBeaverLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    uri: '',
    description: '',
    type: 'mysql',
  });
  const [testResult, setTestResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [dbeaverPassword, setDBeaverPassword] = useState('');
  const [selectedDBeaverConnId, setSelectedDBeaverConnId] = useState(null);

  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    try {
      setLoading(true);
      const data = await api.listSources();
      setSources(data);
    } catch (err) {
      console.error('Failed to load sources:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const getURITemplate = (type) => {
    const templates = {
      mysql: 'mysql://user:password@host:3306/database',
      postgres: 'postgres://user:password@host:5432/database',
      sqlserver: 'mssql://user:password@host:1433/database',
      oracle: 'oracle://user:password@host:1521/SID',
      sqlite: 'sqlite:///path/to/database.db',
      databricks: 'databricks://workspace/catalog/schema/table',
      s3: 's3://bucket/path/to/file.parquet',
    };
    return templates[type] || '';
  };

  const loadDBeaverConnections = async () => {
    try {
      setDBeaverLoading(true);
      const response = await api.getDBeaverConnections();
      
      // Check if response has error field
      if (response.error) {
        alert('DBeaver: ' + response.error);
        setDBeaverConnections([]);
        return;
      }
      
      if (!response || response.length === 0) {
        alert('No DBeaver connections found.\n\nPlease:\n1. Open DBeaver\n2. Go to Database → New Database Connection\n3. Create and save a test connection\n4. Close DBeaver\n5. Try again');
        setDBeaverConnections([]);
        return;
      }
      
      setDBeaverConnections(response);
      setShowDBeaver(true);
    } catch (err) {
      console.error('Failed to load DBeaver connections:', err);
      alert('Failed to load DBeaver connections:\n\n' + err.message + '\n\nTry using Manual connection instead.');
    } finally {
      setDBeaverLoading(false);
    }
  };

  const importDBeaverConnection = async (connectionId) => {
    try {
      if (!dbeaverPassword) {
        alert('❌ Please enter the database password for this connection.');
        return;
      }

      setSubmitting(true);
      console.log('Importing DBeaver connection:', connectionId);
      
      const imported = await api.importDBeaverConnection(connectionId);
      
      if (!imported.uri) {
        throw new Error('Failed to generate connection URI. Connection might have unsupported database type.');
      }
      
      // Add password to the URI
      let uri = imported.uri;
      
      // Parse the URI and insert password
      // Format: scheme://[user[:password]@]host[:port][/database]
      if (uri.includes('://')) {
        const [scheme, rest] = uri.split('://');
        
        // Check if there's already a user
        if (rest.includes('@')) {
          // Replace existing credentials
          const [oldCreds, afterCreds] = rest.split('@');
          const oldUser = oldCreds.split(':')[0];
          uri = `${scheme}://${oldUser}:${dbeaverPassword}@${afterCreds}`;
        } else {
          // Add user and password - assume default users based on driver type
          const defaultUsers = {
            'postgres': 'postgres',
            'mysql': 'root',
            'mssql': 'sa',
            'oracle': 'system',
          };
          const user = defaultUsers[imported.driver] || 'root';
          uri = `${scheme}://${user}:${dbeaverPassword}@${rest}`;
        }
      }
      
      console.log('Imported connection:', imported);
      console.log('Generated URI with password:', uri);
      
      const newSource = await api.createSource({
        name: imported.name,
        uri: uri,
        description: `Imported from DBeaver (${imported.driver})`,
        tags: ['dbeaver'],
      });
      setSources([...sources, newSource]);
      setShowDBeaver(false);
      setDBeaverConnections([]);
      setDBeaverPassword('');
      setSelectedDBeaverConnId(null);
      alert('✅ DBeaver connection imported successfully!');
    } catch (err) {
      console.error('Failed to import DBeaver connection:', err);
      
      // Provide helpful error messages for specific issues
      let helpfulMessage = err.message;
      if (err.message.includes('ODBC')) {
        helpfulMessage = err.message + '\n\n💡 This might mean:\n- SQL Server isn\'t installed/running\n- Server name is incorrect\n- Connection credentials are wrong\n- Network access is blocked\n\nTry using Manual connection instead.';
      } else if (err.message.includes('Connection refused')) {
        helpfulMessage = 'Database server is not running or not accessible.\n\nMake sure your database server is online and accessible.';
      } else if (err.message.includes('Invalid source URI')) {
        helpfulMessage = err.message + '\n\nThe connection URI format might be invalid.\n\nTry using Manual connection instead.';
      }
      
      alert('Failed to import DBeaver connection:\n\n' + helpfulMessage);
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddSource = async () => {
    try {
      if (!formData.name || !formData.uri.trim()) {
        alert('Please fill in all required fields');
        return;
      }

      setSubmitting(true);
      const newSource = await api.createSource(formData);
      setSources([...sources, newSource]);
      setFormData({ name: '', uri: '', description: '', type: 'mysql' });
      setShowForm(false);
      alert('Source added successfully!');
    } catch (err) {
      console.error('Failed to add source:', err);
      alert('Failed to add source: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleTestConnection = async (sourceId) => {
    try {
      const result = await api.testConnection(sourceId);
      setTestResult(result);
      setTimeout(() => setTestResult(null), 3000);
    } catch (err) {
      console.error('Test failed:', err);
      alert('Test failed: ' + err.message);
    }
  };

  const handleDeleteSource = async (sourceId) => {
    if (!window.confirm('Are you sure you want to delete this source?')) {
      return;
    }

    try {
      await api.deleteSource(sourceId);
      setSources(sources.filter((s) => s.id !== sourceId));
      alert('Source deleted successfully!');
    } catch (err) {
      console.error('Failed to delete source:', err);
      alert('Failed to delete source: ' + err.message);
    }
  };

  if (loading) return <div className="loading">Loading settings...</div>;

  return (
    <div className="settings-page">
      <h1>Settings</h1>

      <div className="settings-header">
        <h2>Data Sources</h2>
        <div className="header-actions">
          <button 
            onClick={loadDBeaverConnections}
            className="btn-dbeaver"
            disabled={loading || dbeaverLoading}
            title="Import connections from DBeaver"
          >
            🔗 DBeaver
          </button>
          <button 
            onClick={() => {
              setShowForm(!showForm);
              setShowDBeaver(false);
            }}
            className="btn-primary"
          >
            {showForm ? '✕ Cancel' : '+ Add Source'}
          </button>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {testResult && (
        <div className={testResult.status === 'success' ? 'success' : 'error'}>
          {testResult.message}
        </div>
      )}

      {showForm && (
        <div className="source-form-card">
          <h3>Add New Data Source</h3>
          
          <div className="form-group">
            <label>Source Name *</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleFormChange}
              placeholder="e.g., Production MySQL"
              disabled={submitting}
            />
          </div>

          <div className="form-group">
            <label>Database Type *</label>
            <select
              name="type"
              value={formData.type}
              onChange={(e) => {
                handleFormChange(e);
                setFormData(prev => ({ ...prev, uri: getURITemplate(e.target.value) }));
              }}
              disabled={submitting}
            >
              <option value="mysql">MySQL / MariaDB</option>
              <option value="postgres">PostgreSQL</option>
              <option value="sqlserver">SQL Server</option>
              <option value="oracle">Oracle Database</option>
              <option value="sqlite">SQLite</option>
              <option value="databricks">Databricks</option>
              <option value="s3">S3 / Parquet / CSV</option>
            </select>
          </div>

          <div className="form-group">
            <label>Connection URI *</label>
            <input
              type="text"
              name="uri"
              value={formData.uri}
              onChange={handleFormChange}
              placeholder={getURITemplate(formData.type)}
              disabled={submitting}
            />
            <small>
              <strong>Template:</strong> {getURITemplate(formData.type)}
            </small>
          </div>

          <div className="form-group">
            <label>Description (Optional)</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleFormChange}
              placeholder="e.g., Main production database for customer data"
              rows={2}
              disabled={submitting}
            />
          </div>

          <div className="form-actions">
            <button 
              onClick={handleAddSource} 
              className="btn-primary"
              disabled={submitting || !formData.name || !formData.uri.trim()}
            >
              {submitting ? 'Adding...' : 'Add Source'}
            </button>
            <button 
              onClick={() => {
                setShowForm(false);
                setFormData({ name: '', uri: '', description: '', type: 'mysql' });
              }} 
              className="btn-secondary"
              disabled={submitting}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {showDBeaver && (
        <div className="dbeaver-panel">
          <div className="dbeaver-header">
            <h3>🔗 Import from DBeaver</h3>
            <button 
              onClick={() => {
                setShowDBeaver(false);
                setDBeaverPassword('');
                setSelectedDBeaverConnId(null);
              }}
              className="btn-close"
              disabled={dbeaverLoading || submitting}
            >
              ✕
            </button>
          </div>
          
          {dbeaverLoading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading DBeaver connections...</p>
            </div>
          ) : dbeaverConnections.length === 0 ? (
            <div className="empty-state">
              <p>No DBeaver connections found</p>
              <small>Make sure DBeaver is installed and has saved connections</small>
            </div>
          ) : (
            <div className="dbeaver-list">
              {dbeaverConnections.map((conn) => (
                <div key={conn.id} className="dbeaver-item">
                  <div className="dbeaver-info">
                    <strong>{conn.name}</strong>
                    <small>{conn.driver} • Host: {conn.host}</small>
                  </div>
                  <div className="dbeaver-password-input">
                    <input
                      type="password"
                      placeholder="Database password (required)"
                      value={selectedDBeaverConnId === conn.id ? dbeaverPassword : ''}
                      onChange={(e) => {
                        setSelectedDBeaverConnId(conn.id);
                        setDBeaverPassword(e.target.value);
                      }}
                      disabled={submitting}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && dbeaverPassword) {
                          importDBeaverConnection(conn.id);
                        }
                      }}
                    />
                    <button
                      onClick={() => importDBeaverConnection(conn.id)}
                      className="btn-import"
                      disabled={submitting || !dbeaverPassword}
                    >
                      {submitting ? 'Importing...' : '✓ Import'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="sources-list">
        {sources.length === 0 ? (
          <div className="empty-state">
            <p>No data sources configured</p>
            <p>
              <button onClick={() => setShowForm(true)}>Add your first source</button>
            </p>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Connection</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((source) => (
                <tr key={source.id}>
                  <td>{source.name}</td>
                  <td>{source.source_type}</td>
                  <td>
                    <code>{source.uri}</code>
                  </td>
                  <td>
                    <button
                      onClick={() => handleTestConnection(source.id)}
                      className="secondary"
                    >
                      Test
                    </button>
                    <button
                      onClick={() => handleDeleteSource(source.id)}
                      className="secondary"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default Settings;
