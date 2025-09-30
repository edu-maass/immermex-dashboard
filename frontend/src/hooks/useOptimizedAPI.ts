import { useState, useCallback, useRef, useEffect } from 'react';
import { apiService } from '../services/api';

// Hook para requests con cache y retry automático
export function useOptimizedAPI() {
  const cacheRef = useRef<Map<string, { data: any; timestamp: number }>>(new Map());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getCachedData = useCallback((key: string, ttl: number = 300000) => { // 5 minutos por defecto
    const cached = cacheRef.current.get(key);
    if (cached && Date.now() - cached.timestamp < ttl) {
      return cached.data;
    }
    return null;
  }, []);

  const setCachedData = useCallback((key: string, data: any) => {
    cacheRef.current.set(key, {
      data,
      timestamp: Date.now()
    });
  }, []);

  const makeRequest = useCallback(async <T>(
    requestFn: () => Promise<T>,
    cacheKey?: string,
    options: { ttl?: number; retries?: number; retryDelay?: number } = {}
  ): Promise<T | null> => {
    const { ttl = 300000, retries = 3, retryDelay = 1000 } = options;
    
    // Verificar cache si existe la clave
    if (cacheKey) {
      const cachedData = getCachedData(cacheKey, ttl);
      if (cachedData) {
        return cachedData as T;
      }
    }

    setLoading(true);
    setError(null);

    let lastError: Error | null = null;
    
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const result = await requestFn();
        
        // Guardar en cache si existe la clave
        if (cacheKey) {
          setCachedData(cacheKey, result);
        }
        
        setLoading(false);
        return result;
      } catch (err) {
        lastError = err as Error;
        
        if (attempt < retries) {
          // Esperar antes del siguiente intento
          await new Promise(resolve => setTimeout(resolve, retryDelay * Math.pow(2, attempt)));
        }
      }
    }

    setError(lastError?.message || 'Error desconocido');
    setLoading(false);
    return null;
  }, [getCachedData, setCachedData]);

  const clearCache = useCallback((key?: string) => {
    if (key) {
      cacheRef.current.delete(key);
    } else {
      cacheRef.current.clear();
    }
  }, []);

  return { makeRequest, loading, error, clearCache };
}

// Hook específico para KPIs con cache optimizado
export function useKPIs() {
  const { makeRequest, loading, error } = useOptimizedAPI();
  const [kpis, setKpis] = useState(null);

  const fetchKPIs = useCallback(async (filtros?: any) => {
    const cacheKey = filtros ? `kpis-${JSON.stringify(filtros)}` : 'kpis-general';
    
    const result = await makeRequest(
      () => apiService.getKPIs(filtros),
      cacheKey,
      { ttl: 300000 } // 5 minutos
    );
    
    if (result) {
      setKpis(result);
    }
    
    return result;
  }, [makeRequest]);

  return { kpis, fetchKPIs, loading, error };
}

// Hook para datos de gráficos con cache
export function useChartData() {
  const { makeRequest, loading, error } = useOptimizedAPI();
  const [chartData, setChartData] = useState<Record<string, any>>({});

  const fetchChartData = useCallback(async (chartType: string, filtros?: any) => {
    const cacheKey = `chart-${chartType}-${JSON.stringify(filtros || {})}`;
    
    const result = await makeRequest(
      () => apiService.getChartData(chartType, filtros),
      cacheKey,
      { ttl: 600000 } // 10 minutos para gráficos
    );
    
    if (result) {
      setChartData(prev => ({
        ...prev,
        [chartType]: result
      }));
    }
    
    return result;
  }, [makeRequest]);

  const fetchAllCharts = useCallback(async (filtros?: any) => {
    const chartTypes = ['aging', 'top-clientes', 'consumo-material'];
    const promises = chartTypes.map(type => fetchChartData(type, filtros));
    
    await Promise.all(promises);
  }, [fetchChartData]);

  return { chartData, fetchChartData, fetchAllCharts, loading, error };
}

// Hook para filtros con cache
export function useFilters() {
  const { makeRequest, loading, error } = useOptimizedAPI();
  const [filters, setFilters] = useState<any>(null);

  const fetchFilters = useCallback(async () => {
    const result = await makeRequest(
      () => apiService.getFilters(),
      'filters',
      { ttl: 1800000 } // 30 minutos para filtros
    );
    
    if (result) {
      setFilters(result);
    }
    
    return result;
  }, [makeRequest]);

  return { filters, fetchFilters, loading, error };
}
