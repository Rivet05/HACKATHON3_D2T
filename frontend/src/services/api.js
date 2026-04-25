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
};

export default api;
