/**
 * API client for Lakeforge backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class ApiClient {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      let errorDetail = response.statusText;
      try {
        const errorBody = await response.json();
        if (errorBody.detail) {
          errorDetail = errorBody.detail;
        } else if (errorBody.message) {
          errorDetail = errorBody.message;
        }
      } catch (e) {
        // Could not parse error body as JSON, use statusText
      }
      throw new Error(`API Error (${response.status}): ${errorDetail}`);
    }

    return await response.json();
  }

  // Sources
  async listSources() {
    return this.request('/sources');
  }

  async getSource(id) {
    return this.request(`/sources/${id}`);
  }

  async createSource(data) {
    return this.request('/sources', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteSource(id) {
    return this.request(`/sources/${id}`, { method: 'DELETE' });
  }

  async testConnection(id) {
    return this.request(`/sources/${id}/test`, { method: 'POST' });
  }

  // Inspection
  async startInspection(data) {
    return this.request('/inspect/start', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getInspectionStatus(sessionId) {
    return this.request(`/inspect/${sessionId}/status`);
  }

  async getSchema(sessionId) {
    return this.request(`/inspect/${sessionId}/schema`);
  }

  async getProfile(sessionId) {
    return this.request(`/inspect/${sessionId}/profile`);
  }

  async getSamples(sessionId, limit = 100) {
    return this.request(`/inspect/${sessionId}/samples?limit=${limit}`);
  }

  // Q&A
  async askQuestion(data) {
    return this.request('/qa', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getQAHistory(sessionId) {
    return this.request(`/qa/${sessionId}/history`);
  }

  // Reports
  async listReports() {
    return this.request('/reports');
  }

  async generateReport(data) {
    return this.request('/reports', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // DBeaver
  async getDBeaverConnections() {
    return this.request('/dbeaver/connections');
  }

  async importDBeaverConnection(connectionId) {
    return this.request(`/dbeaver/connections/${connectionId}`, {
      method: 'POST',
    });
  }
}

export default new ApiClient();
