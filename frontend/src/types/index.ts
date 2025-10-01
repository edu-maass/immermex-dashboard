// Tipos para el dashboard de Immermex

export interface KPIs {
  // Facturación
  facturacion_total: number;
  facturacion_sin_iva: number;
  total_facturas: number;
  clientes_unicos: number;
  
  // Cobranza
  cobranza_total: number;
  cobranza_general_total: number;
  cobranza_sin_iva: number;
  porcentaje_cobrado: number;
  porcentaje_cobrado_general: number;
  
  // Anticipos
  anticipos_total: number;
  porcentaje_anticipos: number;
  
  // Pedidos
  total_pedidos: number;
  total_pedidos_count: number;
  pedidos_unicos: number;
  cantidad_total_pedidos: number;
  toneladas_total: number;
  
  // Precios y Costos
  precio_unitario_promedio: number;
  costo_unitario_promedio: number;
  
  // Inventario
  rotacion_inventario: number;
  dias_cxc_ajustado: number;
  ciclo_efectivo: number;
  
  // Gráficos
  aging_cartera: Record<string, number>;
  top_clientes: Record<string, number>;
  consumo_material: Record<string, number>;
  expectativa_cobranza: Record<string, {cobranza_esperada: number, cobranza_real: number}>;
  analisis_pedidos: PedidoAnalisis[];
  clientes_analisis: Record<string, ClienteAnalisis>;
}

export interface PedidoAnalisis {
  numero_pedido: string;
  cliente: string;
  kg: number;
  importe: number;
  ticket_promedio: number;
  margen: number;
  estado_cobro: string;
  dias_credito: number;
}

export interface ClienteAnalisis {
  facturacion: number;
  cobranza: number;
  puntualidad: number;
  ticket_promedio: number;
  facturas_count: number;
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
