import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_URL,
});

export const routingService = {
    getRoute: (data) => api.post('/route/', data),
    getHospitals: () => api.get('/hospitals/'),
    updateHospital: (id, data) => api.patch(`/hospitals/${id}/`, data),
    getAuditLogs: () => api.get('/audit/'),
    injectBlockage: (data) => api.post('/traffic/inject_blockage/', data),
    resetTraffic: () => api.post('/traffic/reset/'),
    checkIntegrity: (data) => api.post('/route/integrity/', data),
    sabotageHospital: (id) => api.post(`/hospitals/${id}/sabotage/`),
};

export default api;
