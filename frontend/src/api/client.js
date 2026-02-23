import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const articlesAPI = {
  getAll: (params = {}) => {
    return apiClient.get('/articles/', { params });
  },

  getById: (id) => {
    return apiClient.get(`/articles/${id}/`);
  },

  search: (query, filters = {}) => {
    return apiClient.get('/articles/', {
      params: {
        search: query,
        ...filters,
      },
    });
  },
};

export default apiClient;
