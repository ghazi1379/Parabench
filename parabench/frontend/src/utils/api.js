import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  timeout: 60000,
});

// Dashboard
export const getDashboardStats = () => api.get('/api/dashboard/stats');
export const getTopBrands = (limit = 10) => api.get(`/api/dashboard/top-brands?limit=${limit}`);
export const getTopCategories = (limit = 10) => api.get(`/api/dashboard/top-categories?limit=${limit}`);
export const getPriceDistribution = () => api.get('/api/dashboard/price-distribution');
export const getPromotions = (limit = 20) => api.get(`/api/dashboard/promotions?limit=${limit}`);
export const getPriceEvolution = (days = 30) => api.get(`/api/dashboard/price-evolution?days=${days}`);

// Products
export const getProducts = (params) => api.get('/api/products', { params });
export const getProduct = (id) => api.get(`/api/products/${id}`);
export const getBrands = () => api.get('/api/products/filters/brands');
export const getCategories = () => api.get('/api/products/filters/categories');

// Benchmark
export const getBenchmark = (params) => api.get('/api/benchmark', { params });
export const refreshBenchmark = () => api.post('/api/benchmark/refresh');

// Scraping
export const startScraping = (sites) => api.post(`/api/scraping/start?${sites.map(s => `sites=${s}`).join('&')}`);
export const getScrapingJobs = () => api.get('/api/scraping/jobs');
export const getScrapingJob = (jobId) => api.get(`/api/scraping/jobs/${jobId}`);
export const getScrapingLogs = (jobId, limit = 100) => api.get(`/api/scraping/logs/${jobId}?limit=${limit}`);
export const getScrapingStatus = () => api.get('/api/scraping/status');

// Exports
export const exportCSV = (params = {}) => {
  const query = new URLSearchParams(params).toString();
  window.open(`${API_URL}/api/export/csv${query ? '?' + query : ''}`, '_blank');
};
export const exportExcel = (params = {}) => {
  const query = new URLSearchParams(params).toString();
  window.open(`${API_URL}/api/export/excel${query ? '?' + query : ''}`, '_blank');
};
export const exportPDF = (params = {}) => {
  const query = new URLSearchParams(params).toString();
  window.open(`${API_URL}/api/export/pdf${query ? '?' + query : ''}`, '_blank');
};
export const exportBenchmarkExcel = () => {
  window.open(`${API_URL}/api/export/benchmark/excel`, '_blank');
};

// Health
export const getHealth = () => api.get('/api/health');

export default api;
