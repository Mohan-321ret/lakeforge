/**
 * React hook for managing inspection state
 */

import { useState, useCallback } from 'react';
import api from '../services/api';

export function useInspection() {
  const [sessionId, setSessionId] = useState(null);
  const [status, setStatus] = useState(null);
  const [schema, setSchema] = useState(null);
  const [profile, setProfile] = useState(null);
  const [samples, setSamples] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const startInspection = useCallback(async (sourceId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.startInspection({
        source_id: sourceId,
        include_profile: true,
      });
      setSessionId(response.session_id);
      setStatus(response.status);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchSchema = useCallback(async (sid) => {
    try {
      const data = await api.getSchema(sid || sessionId);
      setSchema(data.schema);
    } catch (err) {
      setError(err.message);
    }
  }, [sessionId]);

  const fetchProfile = useCallback(async (sid) => {
    try {
      const data = await api.getProfile(sid || sessionId);
      setProfile(data.profile);
    } catch (err) {
      setError(err.message);
    }
  }, [sessionId]);

  const fetchSamples = useCallback(async (sid, limit = 100) => {
    try {
      const data = await api.getSamples(sid || sessionId, limit);
      setSamples(data.samples);
    } catch (err) {
      setError(err.message);
    }
  }, [sessionId]);

  return {
    sessionId,
    status,
    schema,
    profile,
    samples,
    loading,
    error,
    startInspection,
    fetchSchema,
    fetchProfile,
    fetchSamples,
  };
}
