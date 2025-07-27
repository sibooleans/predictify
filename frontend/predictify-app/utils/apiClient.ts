import auth from '../config/authentication';

const api_baseurl = 'https://predictify-zcef.onrender.com';

interface options {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
    body?: any;
    headers?: Record<string, string>;
}
//maybe 2030 was a useful mod after all...
async function getAuthHeaders(): Promise<Record<string, string>> {
    const user = auth.currentUser;
    if (!user) {
        return {
          'Content-Type': 'application/json',  
        };
    }

    return {
        'X-User-UID': user.uid,
        'X-User-Email': user.email || '',
        'Content-Type': 'application/json',
    };
}

export async function apiCall(endpoint: string, options: options = {}) {
  const authHeaders = await getAuthHeaders();
  
  const response = await fetch(`${api_baseurl}${endpoint}`, {
    method: options.method || 'GET',
    headers: {
      ...authHeaders,
      ...options.headers,
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

export const api = {
    getPrediction: (stock: string, daysAhead: number) =>
        apiCall(`/predict?stock=${stock}&days_ahead=${daysAhead}`),
  
    getHistory: (limit: number = 50) =>
        apiCall(`/history?limit=${limit}`),
  
    getUserStats: () =>
        apiCall('/user/stats'),
    //no auth for this
    getHistoricalData: (symbol: string, period: string = '1mo') =>
        fetch(`${api_baseurl}/historical/${symbol}?period=${period}`).then(r => r.json()),
  
    healthCheck: () =>
        fetch(`${api_baseurl}/health/database`).then(r => r.json()),
};
