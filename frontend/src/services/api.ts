// Servicio de API para el dashboard de Immermex

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://immermex-dashboard.vercel.app';
const STORED_PREFIX_KEY = 'immermex_api_prefix';
function getInitialPrefix(): string {
  const stored = typeof window !== 'undefined' ? window.localStorage.getItem(STORED_PREFIX_KEY) : null;
  if (stored === '' || stored === '/api') return stored;
  return ''; // Start without prefix, will auto-detect
}

let apiPrefix = getInitialPrefix();

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const buildUrl = (prefix: string) => `${this.baseUrl}${prefix}${endpoint}`;
    let url = buildUrl(apiPrefix ?? '');
    const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
    const mergedHeaders: Record<string, string> = {
      ...(options.headers as Record<string, string> | undefined),
    };
    if (!isFormData && !('Content-Type' in (mergedHeaders || {}))) {
      mergedHeaders['Content-Type'] = 'application/json';
    }
    
    // Agregar timeout de 30 segundos
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    
    const config: RequestInit = { 
      ...options, 
      headers: mergedHeaders,
      signal: controller.signal
    };

    try {
      let response = await fetch(url, config);
      clearTimeout(timeoutId);
      
      // Auto-detect API prefix: if 404 without '/api', retry with prefix once
      if (response.status === 404 && apiPrefix === '') {
        console.log('Retrying with /api prefix...');
        const retryUrl = buildUrl('/api');
        const retry = await fetch(retryUrl, config);
        if (retry.ok) {
          apiPrefix = '/api';
          try { window.localStorage.setItem(STORED_PREFIX_KEY, '/api'); } catch {}
          return await retry.json();
        }
        response = retry; // fall through to error handling
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('Request timeout - El servidor tardó demasiado en responder');
      }
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
    const endpoint = queryString ? `/kpis?${queryString}` : '/kpis';
    
    return this.request(endpoint);
  }

  // Pedidos
  async getPedidoDetalle(numeroPedido: string) {
    return this.request(`/pedido/${numeroPedido}`);
  }

  // Clientes
  async getClienteDetalle(cliente: string) {
    return this.request(`/cliente/${cliente}`);
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
    const endpoint = queryString ? `/graficos/aging?${queryString}` : '/graficos/aging';
    
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
    return this.request(`/graficos/top-clientes?${queryString}`);
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
    return this.request(`/graficos/consumo-material?${queryString}`);
  }

  // Archivos
  async uploadFile(file: File): Promise<{ registros_procesados?: number; [key: string]: any }> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<{ registros_procesados?: number; [key: string]: any }>('/upload', {
      method: 'POST',
      headers: {}, // No Content-Type header for FormData
      body: formData,
    });
  }

  async getArchivosProcesados(skip: number = 0, limit: number = 100) {
    return this.request(`/archivos?skip=${skip}&limit=${limit}`);
  }

  // Filtros
  async getClientesFiltro() {
    return this.request<string[]>('/filtros/clientes');
  }

  async getMaterialesFiltro() {
    return this.request<string[]>('/filtros/materiales');
  }

  async getPedidosFiltro() {
    return this.request<string[]>('/filtros/pedidos');
  }

  async aplicarFiltros(filtros: { mes?: number; año?: number }) {
    const params = new URLSearchParams();
    if (filtros.mes) params.append('mes', filtros.mes.toString());
    if (filtros.año) params.append('año', filtros.año.toString());
    
    return this.request<{ message: string; datos_filtrados: any }>(`/filtros/aplicar?${params.toString()}`, {
      method: 'POST'
    });
  }

  async aplicarFiltrosPedido(pedidos: string[]) {
    const params = new URLSearchParams();
    pedidos.forEach(pedido => params.append('pedidos', pedido));
    
    return this.request<{ message: string; datos_filtrados: any }>(`/filtros/pedidos/aplicar?${params.toString()}`, {
      method: 'POST'
    });
  }

  // Health check
  async healthCheck() {
    return this.request('/health');
  }
}

export const apiService = new ApiService();
export default apiService;
