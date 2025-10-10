# System Architecture - Immermex Dashboard

## Overview

The Immermex Dashboard is a comprehensive financial data analysis platform built with modern web technologies. The system processes Excel files containing financial data and provides real-time analytics through an intuitive web interface.

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (React/Vite)  │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
│                 │    │                 │    │   (Supabase)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Pages  │    │     Render      │    │   Supabase      │
│   (Static Host) │    │  (Web Service)  │    │   (Managed DB)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Technology Stack

### Frontend
- **Framework**: React 19.1.1
- **Build Tool**: Vite 7.1.2
- **Styling**: Tailwind CSS 3.4.13
- **UI Components**: Radix UI
- **Charts**: Recharts 3.2.1
- **Icons**: Lucide React
- **State Management**: React Hooks + localStorage
- **HTTP Client**: Fetch API
- **Deployment**: GitHub Pages

### Backend
- **Framework**: FastAPI 0.104.1
- **Runtime**: Python 3.12
- **ASGI Server**: Uvicorn 0.24.0
- **ORM**: SQLAlchemy 2.0.23
- **Database Driver**: psycopg2-binary 2.9.9
- **Data Processing**: Pandas 2.1.4, openpyxl 3.1.2
- **Validation**: Pydantic 2.5.0
- **Deployment**: Render

### Database
- **Type**: PostgreSQL
- **Provider**: Supabase (Managed)
- **Connection**: Connection pooling
- **Backup**: Automated backups
- **Scaling**: Horizontal scaling available

## System Components

### 1. Frontend Application

#### Structure
```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── Charts/         # Chart components
│   │   ├── ui/             # UI components
│   │   └── *.tsx           # Main components
│   ├── hooks/              # Custom React hooks
│   ├── services/           # API services
│   ├── types/              # TypeScript definitions
│   └── lib/                # Utility functions
├── public/                 # Static assets
└── dist/                   # Build output
```

#### Key Features
- **Responsive Design**: Mobile-first approach
- **Component Architecture**: Modular, reusable components
- **State Management**: Optimized state with localStorage persistence
- **Performance**: Lazy loading, code splitting, memoization
- **Error Handling**: Comprehensive error boundaries
- **Loading States**: User-friendly loading indicators

#### Optimization Features
- **Bundle Splitting**: Manual chunks for vendor libraries
- **Lazy Loading**: Dynamic imports for chart components
- **Caching**: API response caching with TTL
- **Debouncing**: Debounced state updates
- **Memoization**: React.memo for expensive components

### 2. Backend API

#### Structure
```
backend/
├── endpoints/              # API endpoints
├── services/               # Business logic services
├── utils/                  # Utility functions
├── database.py             # Database models
├── main_with_db.py         # FastAPI application
└── data_processor.py       # Excel processing logic
```

#### Key Features
- **RESTful API**: Standard REST endpoints
- **Data Validation**: Comprehensive input validation
- **Error Handling**: Centralized error management
- **Security**: Rate limiting, CORS, input sanitization
- **Performance**: Caching, compression, pagination
- **Monitoring**: Health checks, performance metrics

#### Service Architecture
- **Database Service**: Data access layer
- **Processing Service**: Excel file processing
- **Validation Service**: Data validation
- **Cache Service**: In-memory caching
- **Security Service**: Authentication and authorization

### 3. Database Layer

#### Schema Design
```sql
-- Core Tables
CREATE TABLE facturacion (
    id SERIAL PRIMARY KEY,
    fecha_factura DATE,
    folio_factura VARCHAR(255),
    cliente VARCHAR(255),
    monto_total DECIMAL(15,2),
    uuid_factura UUID UNIQUE,
    -- Additional fields...
);

CREATE TABLE cobranza (
    id SERIAL PRIMARY KEY,
    fecha_pago DATE,
    cliente VARCHAR(255),
    importe_pagado DECIMAL(15,2),
    uuid_factura_relacionada UUID,
    -- Additional fields...
);

CREATE TABLE pedidos (
    id SERIAL PRIMARY KEY,
    folio_factura VARCHAR(255),
    pedido VARCHAR(255),
    material VARCHAR(255),
    importe_sin_iva DECIMAL(15,2),
    -- Additional fields...
);

CREATE TABLE archivos_procesados (
    id SERIAL PRIMARY KEY,
    nombre_archivo VARCHAR(255),
    fecha_procesamiento TIMESTAMP,
    hash_archivo VARCHAR(255) UNIQUE,
    registros_procesados INTEGER
);
```

#### Indexes
- **Composite Indexes**: For common query patterns
- **Unique Indexes**: For data integrity
- **Performance Indexes**: For frequently accessed columns

### 4. Data Processing Pipeline

#### Excel Processing Flow
```
Excel File Upload
       ↓
File Validation
       ↓
Content Extraction
       ↓
Data Transformation
       ↓
Validation & Cleaning
       ↓
Database Storage
       ↓
KPI Calculation
       ↓
Response Generation
```

#### Processing Features
- **Multi-sheet Support**: Processes multiple Excel sheets
- **Data Validation**: Comprehensive data validation
- **Error Handling**: Graceful error handling
- **Progress Tracking**: Real-time processing updates
- **Data Integrity**: Ensures data consistency

### 5. Security Architecture

#### Security Layers
1. **Network Security**: HTTPS, CORS configuration
2. **Input Validation**: Comprehensive input sanitization
3. **Rate Limiting**: API rate limiting
4. **File Security**: File type and size validation
5. **Data Security**: SQL injection prevention
6. **Error Security**: No sensitive data in error messages

#### Security Features
- **CORS**: Configured for specific origins
- **Rate Limiting**: Per-endpoint rate limits
- **Input Sanitization**: All inputs sanitized
- **File Validation**: Strict file type validation
- **SQL Injection Prevention**: Parameterized queries
- **XSS Prevention**: Output encoding

## Deployment Architecture

### 1. Frontend Deployment (GitHub Pages)

#### Configuration
- **Repository**: GitHub repository
- **Build Process**: GitHub Actions
- **Deployment**: Automatic on push to main
- **Domain**: Custom domain support
- **SSL**: Automatic SSL certificates

#### Build Process
```yaml
# GitHub Actions workflow
- Install dependencies
- Run linting
- Build application
- Deploy to GitHub Pages
```

### 2. Backend Deployment (Render)

#### Configuration
- **Runtime**: Python 3.11
- **Framework**: FastAPI
- **Scaling**: Automatic scaling based on load
- **Environment**: Production environment variables
- **Monitoring**: Built-in Render metrics and logs

#### Deployment Process
```bash
# Render deployment
- Connect GitHub repository
- Configure environment variables
- Automatic deploy on push to main
- Health checks and monitoring
```

### 3. Database (Supabase)

#### Configuration
- **Type**: Managed PostgreSQL
- **Scaling**: Automatic scaling
- **Backup**: Automated backups
- **Security**: Network security, encryption
- **Monitoring**: Built-in monitoring

## Performance Architecture

### 1. Frontend Performance

#### Optimization Strategies
- **Bundle Splitting**: Separate vendor chunks
- **Lazy Loading**: Dynamic component loading
- **Caching**: Browser and API caching
- **Compression**: GZIP compression
- **CDN**: GitHub Pages CDN

#### Performance Metrics
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Time to Interactive**: < 3.5s
- **Bundle Size**: < 500KB gzipped

### 2. Backend Performance

#### Optimization Strategies
- **Database Indexing**: Optimized indexes
- **Query Optimization**: Efficient queries
- **Caching**: In-memory caching
- **Compression**: Response compression
- **Connection Pooling**: Database connection pooling

#### Performance Metrics
- **Response Time**: < 200ms average
- **Throughput**: 1000+ requests/minute
- **Memory Usage**: < 512MB
- **CPU Usage**: < 80%

### 3. Database Performance

#### Optimization Strategies
- **Indexing**: Strategic indexes
- **Query Optimization**: Optimized queries
- **Connection Pooling**: Efficient connections
- **Caching**: Query result caching

## Monitoring and Observability

### 1. Application Monitoring

#### Metrics
- **Response Times**: API endpoint response times
- **Error Rates**: Error frequency and types
- **Throughput**: Requests per second
- **Resource Usage**: Memory and CPU usage

#### Logging
- **Structured Logging**: JSON-formatted logs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Context**: Request context and metadata
- **Aggregation**: Centralized log aggregation

### 2. Infrastructure Monitoring

#### Render Monitoring
- **Service Health**: Uptime and response time
- **Error Tracking**: Application errors and exceptions
- **Resource Usage**: CPU, memory, and network metrics
- **Usage Analytics**: Request patterns and volume
- **Performance**: Response time distributions

#### Database Monitoring
- **Query Performance**: Slow query identification
- **Connection Usage**: Connection pool metrics
- **Storage Usage**: Database size and growth
- **Backup Status**: Backup success and timing

### 3. User Experience Monitoring

#### Frontend Monitoring
- **Page Load Times**: Core Web Vitals
- **Error Tracking**: JavaScript errors
- **User Interactions**: Click tracking and analytics
- **Performance**: Real user monitoring

## Scalability Architecture

### 1. Horizontal Scaling

#### Frontend Scaling
- **CDN**: Global content delivery
- **Static Assets**: Optimized static file serving
- **Caching**: Aggressive caching strategies

#### Backend Scaling
- **Web Service**: Persistent service on Render
- **Auto-scaling**: Based on CPU and memory usage
- **Database Pooling**: Efficient connection management with Supabase pooler

### 2. Vertical Scaling

#### Performance Optimization
- **Code Optimization**: Efficient algorithms
- **Memory Management**: Optimized memory usage
- **Database Optimization**: Query and index optimization

### 3. Future Scaling Considerations

#### Potential Improvements
- **Microservices**: Service decomposition
- **Message Queues**: Async processing
- **Caching Layers**: Redis caching
- **Load Balancing**: Multiple deployment regions

## Data Flow Architecture

### 1. Data Ingestion

```
Excel File → Validation → Processing → Storage → Analytics
```

### 2. Data Processing

```
Raw Data → Cleaning → Validation → Transformation → Storage
```

### 3. Data Retrieval

```
Query → Cache Check → Database → Processing → Response
```

### 4. Data Analytics

```
Stored Data → Aggregation → Calculation → Visualization
```

## Error Handling Architecture

### 1. Error Classification

#### Error Types
- **Validation Errors**: Input validation failures
- **Processing Errors**: Data processing failures
- **Database Errors**: Database operation failures
- **System Errors**: Infrastructure failures

#### Error Severity
- **Low**: Non-critical errors
- **Medium**: Significant errors
- **High**: Critical errors
- **Critical**: System-breaking errors

### 2. Error Response Strategy

#### Error Responses
- **Structured Responses**: Consistent error format
- **Error Codes**: Standardized error codes
- **Context**: Relevant error context
- **Recovery**: Suggested recovery actions

### 3. Error Monitoring

#### Error Tracking
- **Error Aggregation**: Grouped error reporting
- **Error Trends**: Error frequency analysis
- **Error Impact**: Business impact assessment
- **Error Resolution**: Tracking resolution status

## Security Architecture

### 1. Threat Model

#### Potential Threats
- **Injection Attacks**: SQL injection, XSS
- **File Upload Attacks**: Malicious file uploads
- **Rate Limiting Bypass**: API abuse
- **Data Exposure**: Sensitive data leakage

#### Mitigation Strategies
- **Input Validation**: Comprehensive validation
- **File Security**: Strict file type validation
- **Rate Limiting**: API rate limiting
- **Data Encryption**: Sensitive data encryption

### 2. Security Controls

#### Implementation
- **Authentication**: Future authentication system
- **Authorization**: Role-based access control
- **Audit Logging**: Security event logging
- **Monitoring**: Security monitoring and alerting

## Backup and Recovery

### 1. Data Backup

#### Backup Strategy
- **Automated Backups**: Daily automated backups
- **Point-in-time Recovery**: Transaction log backups
- **Geographic Redundancy**: Multi-region backups
- **Backup Testing**: Regular backup verification

### 2. Disaster Recovery

#### Recovery Procedures
- **Recovery Time Objective**: < 4 hours
- **Recovery Point Objective**: < 1 hour
- **Failover Procedures**: Automated failover
- **Testing**: Regular disaster recovery testing

## Development Workflow

### 1. Development Process

#### Workflow
```
Development → Testing → Code Review → Deployment → Monitoring
```

#### Tools
- **Version Control**: Git with GitHub
- **CI/CD**: GitHub Actions and Render auto-deploy
- **Code Quality**: ESLint, Prettier
- **Testing**: Unit and integration tests

### 2. Deployment Process

#### Deployment Pipeline
```
Code Commit → Automated Testing → Build → Deploy → Verify
```

#### Environments
- **Development**: Local development
- **Staging**: Pre-production testing
- **Production**: Live environment

## Maintenance and Operations

### 1. Regular Maintenance

#### Tasks
- **Security Updates**: Regular security patches
- **Dependency Updates**: Keeping dependencies current
- **Performance Monitoring**: Regular performance reviews
- **Capacity Planning**: Resource usage analysis

### 2. Operational Procedures

#### Monitoring
- **Health Checks**: Regular health monitoring
- **Performance Monitoring**: Continuous performance tracking
- **Error Monitoring**: Real-time error tracking
- **Capacity Monitoring**: Resource usage monitoring

This architecture provides a robust, scalable, and maintainable foundation for the Immermex Dashboard system, ensuring high performance, security, and reliability.
