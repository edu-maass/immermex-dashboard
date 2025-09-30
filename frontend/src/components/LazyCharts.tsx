import { lazy, Suspense, FC } from 'react';
import { ChartLoader } from './LoadingSpinner';
import { GraficoDatos } from '../types';

// Lazy load de componentes de gráficas
const AgingChart = lazy(() => import('./Charts/AgingChart').then(module => ({ default: module.AgingChart })));
const TopClientesChart = lazy(() => import('./Charts/TopClientesChart').then(module => ({ default: module.TopClientesChart })));
const ConsumoMaterialChart = lazy(() => import('./Charts/ConsumoMaterialChart').then(module => ({ default: module.ConsumoMaterialChart })));
const ExpectativaCobranzaChart = lazy(() => import('./Charts/ExpectativaCobranzaChart').then(module => ({ default: module.ExpectativaCobranzaChart })));

// Props interfaces
interface ChartProps {
  data: GraficoDatos;
}

interface ExpectativaCobranzaProps {
  data: Array<{ semana: string; cobranza_esperada: number; cobranza_real: number }>;
}

// Componentes wrapper con Suspense
export const LazyAgingChart: FC<ChartProps> = (props) => (
  <Suspense fallback={<ChartLoader />}>
    <AgingChart {...props} />
  </Suspense>
);

export const LazyTopClientesChart: FC<ChartProps> = (props) => (
  <Suspense fallback={<ChartLoader />}>
    <TopClientesChart {...props} />
  </Suspense>
);

export const LazyConsumoMaterialChart: FC<ChartProps> = (props) => (
  <Suspense fallback={<ChartLoader />}>
    <ConsumoMaterialChart {...props} />
  </Suspense>
);

export const LazyExpectativaCobranzaChart: FC<ExpectativaCobranzaProps> = (props) => (
  <Suspense fallback={<ChartLoader />}>
    <ExpectativaCobranzaChart {...props} />
  </Suspense>
);
