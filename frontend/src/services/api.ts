import axios, { AxiosResponse } from 'axios';
import { ChatRequest, ChatResponse } from '../../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export class ApiService {
  static async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response: AxiosResponse<ChatResponse> = await apiClient.post('/chat', request);
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw new ApiError(error.response.data);
      }
      throw new ApiError({
        error: {
          code: 'NETWORK_ERROR',
          message: 'Failed to connect to the server',
          details: error.message
        },
        requestId: 'unknown',
        timestamp: new Date().toISOString()
      });
    }
  }

  static async healthCheck(): Promise<boolean> {
    try {
      await apiClient.get('/health');
      return true;
    } catch (error) {
      return false;
    }
  }
}

export class ApiError extends Error {
  public code: string;
  public details: any;
  public requestId: string;
  public timestamp: string;

  constructor(errorData: any) {
    super(errorData.error?.message || 'Unknown API error');
    this.name = 'ApiError';
    this.code = errorData.error?.code || 'UNKNOWN_ERROR';
    this.details = errorData.error?.details;
    this.requestId = errorData.requestId || 'unknown';
    this.timestamp = errorData.timestamp || new Date().toISOString();
  }
}