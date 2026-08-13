export interface ApiResponse<T = any> {
  data: T | null;
  error: {
    code: string;
    message: string;
  } | null;
  meta: Record<string, any>;
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('access_token');
    }
    return null;
  }

  async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const token = this.getAuthToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const json: ApiResponse<T> = await response.json();

      if (!response.ok && !json.error) {
        return {
          data: null,
          error: {
            code: `HTTP_${response.status}`,
            message: response.statusText || 'An error occurred during request execution.',
          },
          meta: {},
        };
      }

      return json;
    } catch (err: any) {
      return {
        data: null,
        error: {
          code: 'NETWORK_ERROR',
          message: err.message || 'Failed to connect to the backend API.',
        },
        meta: {},
      };
    }
  }

  get<T = any>(endpoint: string, options?: RequestInit) {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  post<T = any>(endpoint: string, body?: any, options?: RequestInit) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(body),
    });
  }
}

export const apiClient = new ApiClient();
