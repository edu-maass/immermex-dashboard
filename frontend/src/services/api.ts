// Servicio de API para el dashboard de Immermex

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://immermex-backend.onrender.com';
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
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error('Request timeout - El servidor tardó demasiado en responder');
        }
        throw error;
      }
      console.error('API request failed:', error);
      throw new Error('Unknown error occurred');
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

  // Método genérico para obtener datos de gráficos
  async getChartData(chartType: string, filtros?: any) {
    switch (chartType) {
      case 'aging':
        return this.getGraficoAging(filtros);
      case 'top-clientes':
        return this.getGraficoTopClientes(10, filtros);
      case 'consumo-material':
        return this.getGraficoConsumoMaterial(10, filtros);
      default:
        throw new Error(`Tipo de gráfico no soportado: ${chartType}`);
    }
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

  // ==================== COMPRAS_V2 ENDPOINTS ====================
  
  async getComprasV2KPIs(filtros?: any): Promise<any> {
    const params = new URLSearchParams();
    if (filtros?.mes) params.append('mes', filtros.mes.toString());
    if (filtros?.año) params.append('año', filtros.año.toString());
    if (filtros?.proveedor) params.append('proveedor', filtros.proveedor);
    if (filtros?.material) params.append('material', filtros.material);
    
    const queryString = params.toString();
    const endpoint = queryString ? `/compras-v2/kpis?${queryString}` : '/compras-v2/kpis';
    
    return this.request(endpoint);
  }

  async getComprasV2Data(filtros?: any, limit: number = 100, offset: number = 0): Promise<any> {
    const params = new URLSearchParams();
    if (filtros?.mes) params.append('mes', filtros.mes.toString());
    if (filtros?.año) params.append('año', filtros.año.toString());
    if (filtros?.proveedor) params.append('proveedor', filtros.proveedor);
    if (filtros?.material) params.append('material', filtros.material);
    if (limit) params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    
    const queryString = params.toString();
    const endpoint = queryString ? `/compras-v2/data?${queryString}` : '/compras-v2/data';
    
    return this.request(endpoint);
  }

  async getMaterialesByCompra(imi: number): Promise<any> {
    return this.request(`/compras-v2/materiales/${imi}`);
  }

  async getComprasV2EvolucionPrecios(material?: string, moneda: string = 'USD'): Promise<any> {
    const params = new URLSearchParams();
    if (material) params.append('material', material);
    params.append('moneda', moneda);
    
    const queryString = params.toString();
    const endpoint = queryString ? `/compras-v2/evolucion-precios?${queryString}` : '/compras-v2/evolucion-precios';
    
    return this.request(endpoint);
  }

  async getComprasV2FlujoPagos(filtros?: any, moneda: string = 'USD'): Promise<any> {
    const params = new URLSearchParams();
    if (filtros?.mes) params.append('mes', filtros.mes.toString());
    if (filtros?.año) params.append('año', filtros.año.toString());
    if (filtros?.proveedor) params.append('proveedor', filtros.proveedor);
    if (filtros?.material) params.append('material', filtros.material);
    params.append('moneda', moneda);
    
    const queryString = params.toString();
    const endpoint = queryString ? `/compras-v2/flujo-pagos?${queryString}` : '/compras-v2/flujo-pagos';
    
    return this.request(endpoint);
  }

  async getComprasV2AgingCuentasPagar(filtros?: any): Promise<any> {
    const params = new URLSearchParams();
    if (filtros?.mes) params.append('mes', filtros.mes.toString());
    if (filtros?.año) params.append('año', filtros.año.toString());
    if (filtros?.proveedor) params.append('proveedor', filtros.proveedor);
    if (filtros?.material) params.append('material', filtros.material);
    
    const queryString = params.toString();
    const endpoint = queryString ? `/compras-v2/aging-cuentas-pagar?${queryString}` : '/compras-v2/aging-cuentas-pagar';
    
    return this.request(endpoint);
  }

  async getComprasV2MaterialesList(): Promise<string[]> {
    return this.request('/compras-v2/materiales');
  }

  async getComprasV2Proveedores(): Promise<string[]> {
    return this.request('/compras-v2/proveedores');
  }

  async getComprasV2AñosDisponibles(): Promise<number[]> {
    return this.request('/compras-v2/anios-disponibles');
  }

  async updateComprasV2FechasEstimadas(): Promise<any> {
    return this.request('/compras-v2/update-fechas-estimadas', {
      method: 'POST',
    });
  }

  async getComprasV2TopProveedores(limite: number = 10, filtros?: any): Promise<any> {
    const params = new URLSearchParams();
    params.append('limite', limite.toString());
    if (filtros?.mes) params.append('mes', filtros.mes.toString());
    if (filtros?.año) params.append('año', filtros.año.toString());
    if (filtros?.proveedor) params.append('proveedor', filtros.proveedor);
    
    const queryString = params.toString();
    const endpoint = queryString ? `/compras-v2/top-proveedores?${queryString}` : '/compras-v2/top-proveedores';
    
    return this.request(endpoint);
  }

  async getComprasV2PorMaterial(limite: number = 10, filtros?: any): Promise<any> {
    const params = new URLSearchParams();
    params.append('limite', limite.toString());
    if (filtros?.mes) params.append('mes', filtros.mes.toString());
    if (filtros?.año) params.append('año', filtros.año.toString());
    if (filtros?.material) params.append('material', filtros.material);
    
    const queryString = params.toString();
    const endpoint = queryString ? `/compras-v2/compras-por-material?${queryString}` : '/compras-v2/compras-por-material';
    
    return this.request(endpoint);
  }

  async validateComprasFile(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request('/compras-v2/validate-file', {
      method: 'POST',
      headers: {}, // No Content-Type header for FormData
      body: formData,
    });
  }

  async uploadComprasV2File(file: File): Promise<{ 
    compras_guardadas?: number; 
    materiales_guardados?: number;
    total_procesados?: number;
    [key: string]: any 
  }> {
    const formData = new FormData();
    formData.append('file', file);

    console.log('🚀 COMPRAS_V2: Enviando archivo a endpoint /upload/compras-v2');
    console.log('📁 Archivo:', file.name, 'Tamaño:', file.size);

    return this.request<{ 
      compras_guardadas?: number; 
      materiales_guardados?: number;
      total_procesados?: number;
      [key: string]: any 
    }>('/upload/compras-v2', {
      method: 'POST',
      headers: {}, // No Content-Type header for FormData
      body: formData,
    });
  }

  async downloadComprasV2Layout(): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/compras-v2/download-layout`);
    if (!response.ok) {
      throw new Error('Error descargando layout de compras');
    }
    return response.blob();
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

  // Nuevos endpoints para persistencia de datos
  async getDataSummary() {
    return this.request('/data/summary');
  }

  async eliminarArchivo(archivoId: number) {
    return this.request(`/archivos/${archivoId}`, {
      method: 'DELETE'
    });
  }

  async getFiltrosDisponibles() {
    return this.request('/filtros/disponibles');
  }

  // ==================== MÉTODOS DE PEDIDOS ====================

  async getTopProveedores(limite: number = 10, filtros?: any) {
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
    return this.request(`/pedidos/top-proveedores?${queryString}`);
  }

  async getVentasPorMaterial(limite: number = 10, filtros?: any) {
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
    return this.request(`/pedidos/ventas-por-material?${queryString}`);
  }

  // ==================== MÉTODOS DE COMPRAS_V2 ====================

  async getTopProveedoresComprasV2(limite: number = 10, filtros?: any): Promise<any> {
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
    return this.request(`/compras-v2/top-proveedores?${queryString}`);
  }

  async getComprasPorMaterialV2(limite: number = 10, filtros?: any): Promise<any> {
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
    return this.request(`/compras-v2/compras-por-material?${queryString}`);
  }

  async getMaterialesComprasV2(): Promise<string[]> {
    return this.request('/compras-v2/materiales');
  }

  async getProveedoresComprasV2(): Promise<string[]> {
    return this.request('/compras-v2/proveedores');
  }

  async getEvolucionPreciosPedidos(filtros?: any) {
    const params = new URLSearchParams();
    
    if (filtros) {
      Object.entries(filtros).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    const queryString = params.toString();
    const endpoint = queryString ? `/pedidos/evolucion-precios?${queryString}` : '/pedidos/evolucion-precios';
    return this.request(endpoint);
  }

  async getFlujoPagosSemanal(filtros?: any) {
    const params = new URLSearchParams();
    
    if (filtros) {
      Object.entries(filtros).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    const queryString = params.toString();
    const endpoint = queryString ? `/pedidos/flujo-pagos-semanal?${queryString}` : '/pedidos/flujo-pagos-semanal';
    return this.request(endpoint);
  }

  async getDatosFiltrados(filtros?: any) {
    const params = new URLSearchParams();
    
    if (filtros) {
      Object.entries(filtros).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    const queryString = params.toString();
    const endpoint = queryString ? `/pedidos/datos-filtrados?${queryString}` : '/pedidos/datos-filtrados';
    return this.request(endpoint);
  }
}

export const apiService = new ApiService();
export default apiService;
