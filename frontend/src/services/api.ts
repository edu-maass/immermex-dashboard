// Servicio de API para el dashboard de Immermex

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://immermex-dashboard.vercel.app';

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // KPIs
  async getKPIs(filtros?: any) {
    const params = new URLSearchParams();
    if (filtros) {
      Object.entries(filtros).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    const queryString = params.toString();
    const endpoint = queryString ? `/api/kpis?${queryString}` : '/api/kpis';
    
    return this.request(endpoint);
  }

  // Pedidos
  async getPedidoDetalle(numeroPedido: string) {
    return this.request(`/api/pedido/${numeroPedido}`);
  }

  // Clientes
  async getClienteDetalle(cliente: string) {
    return this.request(`/api/cliente/${cliente}`);
  }

  // Gráficos
  async getGraficoAging(filtros?: any) {
    const params = new URLSearchParams();
    if (filtros) {
      Object.entries(filtros).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    const queryString = params.toString();
    const endpoint = queryString ? `/api/graficos/aging?${queryString}` : '/api/graficos/aging';
    
    return this.request(endpoint);
  }

  async getGraficoTopClientes(limite: number = 10, filtros?: any) {
    const params = new URLSearchParams();
    params.append('limite', limite.toString());
    
    if (filtros) {
      Object.entries(filtros).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    const queryString = params.toString();
    return this.request(`/api/graficos/top-clientes?${queryString}`);
  }

  async getGraficoConsumoMaterial(limite: number = 10, filtros?: any) {
    const params = new URLSearchParams();
    params.append('limite', limite.toString());
    
    if (filtros) {
      Object.entries(filtros).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    const queryString = params.toString();
    return this.request(`/api/graficos/consumo-material?${queryString}`);
  }

  // Archivos
  async uploadFile(file: File): Promise<{ registros_procesados?: number; [key: string]: any }> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<{ registros_procesados?: number; [key: string]: any }>('/api/upload', {
      method: 'POST',
      headers: {}, // No Content-Type header for FormData
      body: formData,
    });
  }

  async getArchivosProcesados(skip: number = 0, limit: number = 100) {
    return this.request(`/api/archivos?skip=${skip}&limit=${limit}`);
  }

  // Health check
  async healthCheck() {
    return this.request('/api/health');
  }
}

export const apiService = new ApiService();
export default apiService;
