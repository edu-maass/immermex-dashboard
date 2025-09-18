// Tipos para el dashboard de Immermex

export interface KPIs {
  facturacion_total: number;
  cobranza_total: number;
  anticipos_total: number;
  porcentaje_cobrado: number;
  rotacion_inventario: number;
  total_facturas: number;
  clientes_unicos: number;
  aging_cartera: Record<string, number>;
  top_clientes: Record<string, number>;
  consumo_material: Record<string, number>;
}

export interface FiltrosDashboard {
  fecha_inicio?: string;
  fecha_fin?: string;
  cliente?: string;
  agente?: string;
  numero_pedido?: string;
  material?: string;
  mes?: number;
  año?: number;
}

export interface PedidoDetalle {
  numero_pedido: string;
  cliente: string;
  agente: string;
  fecha_factura: string;
  materiales: Array<{
    material: string;
    cantidad_kg: number;
    precio_unitario: number;
    subtotal: number;
  }>;
  total_pedido: number;
  importe_cobrado: number;
  anticipos: number;
  margen: number;
  estado_cobro: string;
  dias_vencimiento?: number;
}

export interface ClienteDetalle {
  cliente: string;
  facturacion_total: number;
  cobros_total: number;
  anticipos_total: number;
  facturas_pendientes: number;
  ticket_promedio: number;
  puntualidad_pago: number;
  ultima_factura?: string;
  ultimo_cobro?: string;
}

export interface GraficoDatos {
  labels: string[];
  data: number[];
  titulo: string;
}

export interface ArchivoProcesado {
  id: number;
  nombre_archivo: string;
  fecha_procesamiento: string;
  registros_procesados: number;
  estado: string;
  mes?: number;
  año?: number;
}
