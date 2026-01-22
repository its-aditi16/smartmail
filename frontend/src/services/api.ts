import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Email-related API calls
export const emailApi = {
  processVoiceCommand: async (command: string) => {
    try {
      const response = await api.post('/voice/process', { command });
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  getEmails: async (params: { folder?: string; query?: string }) => {
    try {
      const response = await api.get('/emails', { params });
      return response.data;
    } catch (error) {
      throw error;
    }
  },
};

// Auth-related API calls
export const authApi = {
  googleSignIn: async (token: string) => {
    try {
      const response = await api.post('/auth/google', { token });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  logout: async () => {
    try {
      await api.post('/auth/logout');
      localStorage.removeItem('token');
    } catch (error) {
      throw error;
    }
  },
};

export default api; 