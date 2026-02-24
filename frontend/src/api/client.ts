import axios from 'axios';
import { z } from 'zod';

import { ArticleSchema, CveDetailsSchema, type FilterParams, type Article, type CveDetailsType } from '../types';

const API_BASE_URL = (import.meta.env['VITE_API_URL'] as string | undefined) ?? 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const articlesAPI = {
  getAll: async (params: FilterParams = {}): Promise<{ data: Article[] }> => {
    const response = await apiClient.get('/articles/', { params });
    // Parse at the boundary
    const parsedData = z.array(ArticleSchema).parse(response.data);
    return { ...response, data: parsedData };
  },

  getById: async (id: string | number): Promise<{ data: Article }> => {
    const response = await apiClient.get(`/articles/${id}/`);
    const parsedData = ArticleSchema.parse(response.data);
    return { ...response, data: parsedData };
  },

  search: async (query: string, filters: Record<string, unknown> = {}): Promise<{ data: Article[] }> => {
    const response = await apiClient.get('/articles/', {
      params: {
        search: query,
        ...filters,
      },
    });
    const parsedData = z.array(ArticleSchema).parse(response.data);
    return { ...response, data: parsedData };
  },
};

export const iocAPI = {
  getCveDetails: async (cveId: string, signal?: AbortSignal): Promise<{ data: CveDetailsType }> => {
    const response = await apiClient.get(`/articles/cves/${cveId}/`, { ...(signal !== undefined ? { signal } : {}) });
    const parsedData = CveDetailsSchema.parse(response.data);
    return { ...response, data: parsedData };
  },
};

export default apiClient;
