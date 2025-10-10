# API Documentation - Immermex Dashboard

## Overview

The Immermex Dashboard API is a RESTful service built with FastAPI that provides comprehensive financial data processing and analysis capabilities. The API handles Excel file uploads, processes financial data, and provides real-time KPIs and analytics.

## Base URL

- **Production**: `https://immermex-backend.onrender.com`
- **Development**: `http://localhost:8000`

## Authentication

Currently, the API does not require authentication. However, rate limiting and input validation are implemented for security.

## Rate Limiting

- **Default**: 100 requests per minute per IP
- **Upload endpoints**: 5 requests per 5 minutes per IP
- **KPI endpoints**: 30 requests per minute per IP

## CORS Configuration

The API supports CORS for the following origins:
- `http://localhost:3000` (development)
- `http://127.0.0.1:3000` (local development)
- `https://edu-maass.github.io` (production frontend)

## Data Models

### KPIs Response
```json
{
  "facturacion_total": 7126506.22,
  "facturacion_sin_iva": 6143791.58,
  "cobranza_total": 742019.09,
  "cobranza_general_total": 3833260.33,
  "cobranza_sin_iva": 639671.63,
  "anticipos_total": 364331.96,
  "porcentaje_anticipos": 5.11,
  "total_facturas": 179,
  "clientes_unicos": 25,
  "pedidos_unicos": 722,
  "toneladas_total": 1500.75,
  "porcentaje_cobrado": 10.41,
  "porcentaje_cobrado_general": 53.78,
  "expectativa_cobranza": {
    "Semana 1": {
      "cobranza_esperada": 50000,
      "cobranza_real": 45000
    }
  }
}
```

### Data Summary Response
```json
{
  "has_data": true,
  "archivo": {
    "id": 19,
    "nombre": "0925_material_pedido (5).xlsx",
    "fecha_procesamiento": "2025-09-30T18:43:40.943277",
    "registros_procesados": 1075
  },
  "conteos": {
    "facturas": 179,
    "cobranzas": 108,
    "pedidos": 722
  }
}
```

## Endpoints

### 1. Data Upload

#### Upload Excel File
**POST** `/api/upload`

Upload and process an Excel file containing financial data.

**Parameters:**
- `file` (multipart/form-data): Excel file (.xlsx or .xls)
- `reemplazar_datos` (query, optional): Boolean to replace existing data (default: true)

**Request:**
```bash
curl -X POST "https://immermex-backend.onrender.com/api/upload" \
  -F "file=@data.xlsx" \
  -F "reemplazar_datos=true"
```

**Response:**
```json
{
  "success": true,
  "message": "Archivo procesado exitosamente",
  "filename": "data.xlsx",
  "processed_data": {
    "facturacion": 179,
    "cobranza": 108,
    "pedidos": 722
  },
  "validation_results": {
    "facturacion": {"is_valid": true, "message": "Basic validation passed"},
    "cobranza": {"is_valid": true, "message": "Basic validation passed"},
    "pedidos": {"is_valid": true, "message": "Basic validation passed"}
  },
  "file_info": {
    "nombre_archivo": "data.xlsx",
    "tipo_archivo": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "reemplazar_datos": true
  }
}
```

### 2. KPIs and Analytics

#### Get KPIs
**GET** `/api/kpis`

Retrieve key performance indicators with optional filtering.

**Parameters:**
- `mes` (query, optional): Filter by month (1-12)
- `año` (query, optional): Filter by year
- `pedidos` (query, optional): Comma-separated list of pedido IDs

**Request:**
```bash
curl -X GET "https://immermex-backend.onrender.com/api/kpis?mes=9&año=2025"
```

**Response:**
```json
{
  "facturacion_total": 7126506.22,
  "facturacion_sin_iva": 6143791.58,
  "cobranza_total": 742019.09,
  "cobranza_general_total": 3833260.33,
  "cobranza_sin_iva": 639671.63,
  "anticipos_total": 364331.96,
  "porcentaje_anticipos": 5.11,
  "total_facturas": 179,
  "clientes_unicos": 25,
  "pedidos_unicos": 722,
  "toneladas_total": 1500.75,
  "porcentaje_cobrado": 10.41,
  "porcentaje_cobrado_general": 53.78,
  "expectativa_cobranza": {
    "Semana 1": {
      "cobranza_esperada": 50000,
      "cobranza_real": 45000
    },
    "Semana 2": {
      "cobranza_esperada": 45000,
      "cobranza_real": 42000
    }
  }
}
```

### 3. Data Management

#### Get Data Summary
**GET** `/api/data/summary`

Get a summary of available data in the system.

**Request:**
```bash
curl -X GET "https://immermex-backend.onrender.com/api/data/summary"
```

**Response:**
```json
{
  "has_data": true,
  "archivo": {
    "id": 19,
    "nombre": "0925_material_pedido (5).xlsx",
    "fecha_procesamiento": "2025-09-30T18:43:40.943277",
    "registros_procesados": 1075
  },
  "conteos": {
    "facturas": 179,
    "cobranzas": 108,
    "pedidos": 722
  }
}
```

#### Get Available Filters
**GET** `/api/filtros/pedidos`

Get a list of available pedidos for filtering.

**Request:**
```bash
curl -X GET "https://immermex-backend.onrender.com/api/filtros/pedidos"
```

**Response:**
```json
[
  "1585",
  "1875",
  "1739",
  "1801",
  "1830",
  "1770",
  "1903",
  "1777",
  "1624",
  "1732"
]
```

#### Apply Pedido Filters
**POST** `/api/filtros/pedidos/aplicar`

Apply filters to KPI calculations for specific pedidos.

**Request:**
```json
{
  "pedidos": ["1585", "1875", "1739"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Filtros aplicados correctamente",
  "filtros_aplicados": {
    "pedidos": ["1585", "1875", "1739"]
  },
  "kpis_filtrados": {
    "facturacion_total": 1500000.00,
    "cobranza_total": 150000.00,
    "pedidos_unicos": 3
  }
}
```

### 4. Chart Data

#### Get Aging Chart Data
**GET** `/api/graficos/aging`

Get data for the aging chart showing invoice aging.

**Request:**
```bash
curl -X GET "https://immermex-backend.onrender.com/api/graficos/aging"
```

**Response:**
```json
{
  "0-30": 45000,
  "31-60": 25000,
  "61-90": 15000,
  "91-120": 8000,
  "120+": 5000
}
```

#### Get Top Clients Chart Data
**GET** `/api/graficos/top-clientes`

Get data for the top clients chart.

**Parameters:**
- `limit` (query, optional): Number of top clients to return (default: 10)

**Request:**
```bash
curl -X GET "https://immermex-backend.onrender.com/api/graficos/top-clientes?limit=5"
```

**Response:**
```json
{
  "Cliente A": 500000,
  "Cliente B": 450000,
  "Cliente C": 300000,
  "Cliente D": 250000,
  "Cliente E": 200000
}
```

#### Get Material Consumption Chart Data
**GET** `/api/graficos/consumo-material`

Get data for the material consumption chart.

**Parameters:**
- `limit` (query, optional): Number of materials to return (default: 10)

**Request:**
```bash
curl -X GET "https://immermex-backend.onrender.com/api/graficos/consumo-material?limit=5"
```

**Response:**
```json
{
  "Material A": 150.5,
  "Material B": 120.3,
  "Material C": 95.7,
  "Material D": 80.2,
  "Material E": 65.1
}
```

### 5. System Information

#### Health Check
**GET** `/api/health`

Check the health status of the API.

**Request:**
```bash
curl -X GET "https://immermex-backend.onrender.com/api/health"
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-30T22:00:00Z",
  "database": "connected",
  "version": "2.0.0"
}
```

#### System Performance
**GET** `/api/system/performance`

Get system performance metrics.

**Request:**
```bash
curl -X GET "https://immermex-backend.onrender.com/api/system/performance"
```

**Response:**
```json
{
  "memory_usage": {
    "total": 1073741824,
    "available": 536870912,
    "percent": 50.0
  },
  "cache_stats": {
    "hits": 150,
    "misses": 25,
    "hit_rate": 85.7
  },
  "uptime": "2 days, 5 hours, 30 minutes"
}
```

### 6. File Management

#### Delete Processed File
**DELETE** `/api/data/archivo/{archivo_id}`

Delete a processed file and its associated data.

**Parameters:**
- `archivo_id` (path): ID of the file to delete

**Request:**
```bash
curl -X DELETE "https://immermex-backend.onrender.com/api/data/archivo/19"
```

**Response:**
```json
{
  "success": true,
  "message": "Archivo y datos asociados eliminados correctamente",
  "archivo_eliminado": {
    "id": 19,
    "nombre": "0925_material_pedido (5).xlsx"
  }
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Solo se permiten archivos Excel (.xlsx, .xls)"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "file"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

### 429 Too Many Requests
```json
{
  "detail": "Too many requests. Please try again after 60 seconds."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal Server Error"
}
```

## Data Processing

### Excel File Structure

The API expects Excel files with the following sheets:

1. **Facturacion**: Invoice data
   - Required columns: `fecha_factura`, `folio_factura`, `cliente`, `monto_total`, `uuid_factura`
   - Optional columns: `monto_neto`, `saldo_pendiente`, `dias_credito`, `importe_cobrado`

2. **Cobranza**: Collection data
   - Required columns: `fecha_pago`, `cliente`, `importe_pagado`, `uuid_factura_relacionada`
   - Optional columns: `tipo_cambio`, `numero_parcialidades`

3. **Pedidos**: Order data
   - Required columns: `folio_factura`, `pedido`, `material`, `importe_sin_iva`, `fecha_factura`
   - Optional columns: `kg`, `precio_unitario`, `dias_credito`

### Data Validation

The API performs the following validations:

- **File type**: Only .xlsx and .xls files are accepted
- **File size**: Maximum 10MB
- **Required columns**: All required columns must be present
- **Data types**: Numeric fields must contain valid numbers
- **Date formats**: Date fields must be in valid format
- **Unique constraints**: UUIDs must be unique where required

### Proportional Calculations

When filtering by pedidos, the system applies proportional calculations:

- **Formula**: `Monto_Factura × %_Cobrado × %_Proporción_Pedido`
- **Application**: Each pedido's contribution to a factura is calculated proportionally
- **Cobranza**: Only the proportional amount of collection is attributed to filtered pedidos

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **General endpoints**: 100 requests per minute
- **Upload endpoints**: 5 requests per 5 minutes
- **KPI endpoints**: 30 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Security Features

- **CORS**: Configured for specific origins
- **Input validation**: All inputs are validated and sanitized
- **File type validation**: Only Excel files are accepted
- **Size limits**: File size is limited to 10MB
- **Rate limiting**: Prevents abuse and ensures fair usage
- **Error handling**: Comprehensive error handling without information disclosure

## Performance Considerations

- **Database indexing**: Optimized indexes for common queries
- **Caching**: In-memory caching for frequently accessed data
- **Pagination**: Large datasets are paginated
- **Compression**: GZIP compression for API responses
- **Async processing**: Non-blocking I/O operations

## Deployment

The API is deployed on Render with the following configuration:

- **Runtime**: Python 3.12
- **Framework**: FastAPI
- **Database**: PostgreSQL (Supabase)
- **Storage**: Stateless (no persistent file storage)
- **Scaling**: Automatic scaling based on demand

## Monitoring

The system includes comprehensive monitoring:

- **Health checks**: Regular health status monitoring
- **Performance metrics**: Response times and throughput
- **Error tracking**: Centralized error logging and tracking
- **Usage analytics**: API usage patterns and statistics

## Support

For technical support or questions about the API:

- **Documentation**: This file and inline API documentation
- **Health endpoint**: `/api/health` for system status
- **Error responses**: Detailed error messages for debugging
- **Logging**: Comprehensive logging for troubleshooting
