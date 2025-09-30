# Development Guide - Immermex Dashboard

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js**: Version 18.x or higher
- **Python**: Version 3.12 or higher
- **Git**: Latest version
- **PostgreSQL**: Version 13 or higher (or access to Supabase)

### Environment Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/edu-maass/immermex-dashboard.git
cd immermex-dashboard
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env_example.txt .env
# Edit .env with your database credentials
```

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your API endpoints
```

#### 4. Database Setup

```bash
# Create database tables
cd backend
python -c "from database import init_db; init_db()"

# Or use the SQL script
psql -h your_host -U your_user -d your_database -f create_tables_supabase.sql
```

## Development Workflow

### 1. Local Development

#### Backend Development

```bash
cd backend

# Start the development server
uvicorn main_with_db:app --reload --host 0.0.0.0 --port 8000

# The API will be available at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

#### Frontend Development

```bash
cd frontend

# Start the development server
npm run dev

# The frontend will be available at http://localhost:3000
```

#### Database Development

```bash
# Connect to your database
psql -h your_host -U your_user -d your_database

# Run migrations (if any)
python migrate_to_supabase.py
```

### 2. Testing

#### Backend Testing

```bash
cd backend

# Run unit tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_api.py

# Run tests with coverage
python -m pytest --cov=. tests/
```

#### Frontend Testing

```bash
cd frontend

# Run unit tests
npm test

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

#### API Testing

```bash
# Test API endpoints
curl -X GET http://localhost:8000/api/health

# Test file upload
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test_file.xlsx" \
  -F "reemplazar_datos=true"
```

### 3. Code Quality

#### Backend Code Quality

```bash
cd backend

# Run linting
flake8 .

# Run type checking
mypy .

# Run formatting
black .
```

#### Frontend Code Quality

```bash
cd frontend

# Run linting
npm run lint

# Fix linting issues
npm run lint:fix

# Run type checking
npm run type-check

# Format code
npm run format
```

## Project Structure

### Backend Structure

```
backend/
├── endpoints/              # API endpoints
│   ├── __init__.py
│   └── performance_endpoints.py
├── services/               # Business logic services
│   ├── __init__.py
│   ├── facturacion_service.py
│   ├── cobranza_service.py
│   ├── pedidos_service.py
│   └── kpi_aggregator.py
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── cache.py
│   ├── pagination.py
│   ├── validators.py
│   ├── error_handlers.py
│   ├── logging_config.py
│   └── vercel_performance_monitor.py
├── database.py             # Database models and connection
├── database_service_refactored.py  # Main database service
├── data_processor.py       # Excel processing logic
├── main_with_db.py         # FastAPI application
├── models.py               # Pydantic models
├── requirements.txt        # Python dependencies
└── vercel.json            # Vercel deployment config
```

### Frontend Structure

```
frontend/
├── src/
│   ├── components/         # React components
│   │   ├── Charts/        # Chart components
│   │   │   ├── AgingChart.tsx
│   │   │   ├── TopClientesChart.tsx
│   │   │   ├── ConsumoMaterialChart.tsx
│   │   │   └── ExpectativaCobranzaChart.tsx
│   │   ├── ui/            # UI components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   └── select.tsx
│   │   ├── Dashboard.tsx
│   │   ├── OptimizedDashboard.tsx
│   │   ├── FileUpload.tsx
│   │   ├── Filters.tsx
│   │   └── KPICard.tsx
│   ├── hooks/             # Custom React hooks
│   │   ├── useOptimizedState.ts
│   │   └── useOptimizedAPI.ts
│   ├── services/          # API services
│   │   └── api.ts
│   ├── types/             # TypeScript definitions
│   │   └── index.ts
│   ├── lib/               # Utility functions
│   │   └── utils.ts
│   ├── App.tsx            # Main application component
│   └── main.tsx           # Application entry point
├── public/                # Static assets
├── dist/                  # Build output
├── package.json           # Node.js dependencies
├── vite.config.ts         # Vite configuration
├── tailwind.config.js     # Tailwind CSS configuration
└── tsconfig.json          # TypeScript configuration
```

## API Development

### 1. Creating New Endpoints

#### Basic Endpoint Structure

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(prefix="/api/example", tags=["Example"])

@router.get("/")
async def get_example_data(db: Session = Depends(get_db)):
    """Get example data from database"""
    try:
        # Your business logic here
        return {"success": True, "data": "example"}
    except Exception as e:
        logger.error(f"Error getting example data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### Adding to Main Application

```python
# In main_with_db.py
from endpoints.example_endpoints import example_router

app.include_router(example_router)
```

### 2. Database Operations

#### Using the Database Service

```python
from database_service_refactored import DatabaseService

def get_data_example(db: Session):
    db_service = DatabaseService(db)
    
    # Get data
    data = db_service.get_facturacion_data()
    
    # Process data
    processed_data = process_data(data)
    
    return processed_data
```

#### Direct Database Queries

```python
from database import Facturacion, Cobranza, Pedido

def get_facturacion_by_date(db: Session, start_date, end_date):
    return db.query(Facturacion).filter(
        Facturacion.fecha_factura.between(start_date, end_date)
    ).all()
```

### 3. Data Validation

#### Using Pydantic Models

```python
from pydantic import BaseModel, validator
from typing import Optional
from datetime import date

class FacturacionCreate(BaseModel):
    fecha_factura: date
    folio_factura: str
    cliente: str
    monto_total: float
    
    @validator('monto_total')
    def validate_monto_total(cls, v):
        if v <= 0:
            raise ValueError('Monto total must be positive')
        return v

class FacturacionResponse(BaseModel):
    id: int
    fecha_factura: date
    folio_factura: str
    cliente: str
    monto_total: float
```

#### Using Custom Validators

```python
from utils.validators import DataValidator

def validate_facturacion_data(data):
    validator = DataValidator()
    
    # Validate required fields
    required_fields = ['fecha_factura', 'folio_factura', 'cliente', 'monto_total']
    validator.validate_required_fields(data, required_fields)
    
    # Validate data types
    validator.validate_data_types(data, {
        'monto_total': float,
        'fecha_factura': str
    })
    
    return validator.get_validation_results()
```

## Frontend Development

### 1. Creating New Components

#### Component Structure

```tsx
import { FC, useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card } from './ui/card';

interface ExampleComponentProps {
  title: string;
  data: any[];
  onAction?: () => void;
}

export const ExampleComponent: FC<ExampleComponentProps> = ({ 
  title, 
  data, 
  onAction 
}) => {
  const [loading, setLoading] = useState(false);
  
  const handleAction = async () => {
    setLoading(true);
    try {
      await onAction?.();
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold mb-4">{title}</h2>
      <div className="space-y-4">
        {data.map((item, index) => (
          <div key={index} className="p-3 bg-gray-50 rounded">
            {JSON.stringify(item)}
          </div>
        ))}
      </div>
      <Button 
        onClick={handleAction}
        disabled={loading}
        className="mt-4"
      >
        {loading ? 'Loading...' : 'Action'}
      </Button>
    </Card>
  );
};
```

### 2. Creating Custom Hooks

#### Custom Hook Structure

```tsx
import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';

export function useExampleData() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiService.getExampleData();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  return { data, loading, error, refetch: fetchData };
}
```

### 3. API Integration

#### API Service Methods

```tsx
// In services/api.ts
export const apiService = {
  async getExampleData(): Promise<any> {
    const response = await fetch('/api/example');
    if (!response.ok) {
      throw new Error('Failed to fetch example data');
    }
    return response.json();
  },
  
  async postExampleData(data: any): Promise<any> {
    const response = await fetch('/api/example', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error('Failed to post example data');
    }
    
    return response.json();
  }
};
```

## Testing

### 1. Backend Testing

#### Unit Tests

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from main_with_db import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_upload_endpoint():
    with open("test_file.xlsx", "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": f},
            params={"reemplazar_datos": True}
        )
    assert response.status_code == 200
    assert response.json()["success"] is True
```

#### Integration Tests

```python
# tests/test_database.py
import pytest
from sqlalchemy.orm import Session
from database import get_db, Facturacion
from database_service_refactored import DatabaseService

def test_database_connection(db: Session):
    # Test database connection
    assert db is not None
    
    # Test query
    facturas = db.query(Facturacion).all()
    assert isinstance(facturas, list)

def test_database_service(db: Session):
    db_service = DatabaseService(db)
    summary = db_service.get_data_summary()
    assert "has_data" in summary
```

### 2. Frontend Testing

#### Component Tests

```tsx
// tests/ExampleComponent.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ExampleComponent } from '../src/components/ExampleComponent';

describe('ExampleComponent', () => {
  const mockData = [
    { id: 1, name: 'Test 1' },
    { id: 2, name: 'Test 2' }
  ];
  
  it('renders component with data', () => {
    render(<ExampleComponent title="Test Title" data={mockData} />);
    
    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('Test 1')).toBeInTheDocument();
  });
  
  it('calls onAction when button is clicked', () => {
    const mockAction = jest.fn();
    render(
      <ExampleComponent 
        title="Test Title" 
        data={mockData} 
        onAction={mockAction} 
      />
    );
    
    fireEvent.click(screen.getByText('Action'));
    expect(mockAction).toHaveBeenCalled();
  });
});
```

#### API Tests

```tsx
// tests/api.test.ts
import { apiService } from '../src/services/api';

// Mock fetch
global.fetch = jest.fn();

describe('API Service', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
  });
  
  it('fetches example data successfully', async () => {
    const mockData = { success: true, data: 'test' };
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });
    
    const result = await apiService.getExampleData();
    expect(result).toEqual(mockData);
    expect(fetch).toHaveBeenCalledWith('/api/example');
  });
  
  it('handles API errors', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
    });
    
    await expect(apiService.getExampleData()).rejects.toThrow(
      'Failed to fetch example data'
    );
  });
});
```

## Deployment

### 1. Backend Deployment (Vercel)

#### Configuration

```json
// vercel.json
{
  "version": 2,
  "builds": [
    {
      "src": "main_with_db.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main_with_db.py"
    }
  ],
  "env": {
    "DATABASE_URL": "@database-url",
    "SECRET_KEY": "@secret-key"
  }
}
```

#### Environment Variables

```bash
# Set in Vercel dashboard
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-secret-key
VERCEL_ENV=production
```

#### Deployment Commands

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel --prod
```

### 2. Frontend Deployment (GitHub Pages)

#### Configuration

```json
// package.json
{
  "scripts": {
    "build": "vite build",
    "preview": "vite preview",
    "deploy": "gh-pages -d dist"
  },
  "homepage": "https://edu-maass.github.io/immermex-dashboard"
}
```

#### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '18'
        
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
        
    - name: Build
      run: |
        cd frontend
        npm run build
        
    - name: Deploy
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./frontend/dist
```

### 3. Database Deployment (Supabase)

#### Migration Script

```python
# migrate_to_supabase.py
import os
from database import engine, Base
from sqlalchemy import create_engine

def migrate_to_supabase():
    """Migrate database schema to Supabase"""
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate_to_supabase()
```

## Debugging

### 1. Backend Debugging

#### Logging Configuration

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Use in code
logger.info("Processing started")
logger.error(f"Error occurred: {str(e)}")
```

#### Debug Endpoints

```python
@app.get("/api/debug/test")
async def debug_test():
    """Debug endpoint for testing"""
    return {
        "status": "debug",
        "message": "Debug endpoint working",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### 2. Frontend Debugging

#### React Developer Tools

```bash
# Install React Developer Tools browser extension
# Available for Chrome, Firefox, and Edge
```

#### Console Debugging

```tsx
// Add debugging to components
useEffect(() => {
  console.log('Component mounted', { data, loading });
}, [data, loading]);

// Debug API calls
const fetchData = async () => {
  console.log('Fetching data...');
  try {
    const result = await apiService.getData();
    console.log('Data fetched successfully:', result);
  } catch (error) {
    console.error('Error fetching data:', error);
  }
};
```

## Performance Optimization

### 1. Backend Optimization

#### Database Optimization

```python
# Use indexes for frequently queried columns
from sqlalchemy import Index

class Facturacion(Base):
    __tablename__ = 'facturacion'
    
    __table_args__ = (
        Index('idx_facturacion_fecha', 'fecha_factura'),
        Index('idx_facturacion_cliente', 'cliente'),
        Index('idx_facturacion_uuid', 'uuid_factura'),
    )
```

#### Caching

```python
from functools import lru_cache
from utils.cache import cache_result

@cache_result(ttl=300)  # Cache for 5 minutes
def get_expensive_data():
    # Expensive operation
    return processed_data
```

### 2. Frontend Optimization

#### Component Optimization

```tsx
import { memo, useMemo, useCallback } from 'react';

export const OptimizedComponent = memo(({ data, onAction }) => {
  const processedData = useMemo(() => {
    return data.map(item => processItem(item));
  }, [data]);
  
  const handleAction = useCallback((id) => {
    onAction(id);
  }, [onAction]);
  
  return (
    <div>
      {processedData.map(item => (
        <div key={item.id} onClick={() => handleAction(item.id)}>
          {item.name}
        </div>
      ))}
    </div>
  );
});
```

#### Bundle Optimization

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'ui-vendor': ['@radix-ui/react-dialog', '@radix-ui/react-select'],
          'chart-vendor': ['recharts'],
        }
      }
    }
  }
});
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```python
# Check database connection
from database import engine
from sqlalchemy import text

def check_database_connection():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")
```

#### 2. CORS Issues

```python
# Check CORS configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://edu-maass.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 3. File Upload Issues

```python
# Check file upload configuration
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    # Check file type
    if not file.content_type.startswith('application/vnd.openxmlformats'):
        raise HTTPException(400, "Only Excel files are allowed")
    
    # Check file size
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(400, "File too large")
```

### Getting Help

#### Resources

- **Documentation**: Check the `/docs` folder for detailed documentation
- **API Docs**: Visit `/docs` endpoint when running locally
- **GitHub Issues**: Create an issue on the GitHub repository
- **Logs**: Check application logs for error details

#### Support

For technical support or questions:

1. Check the documentation first
2. Search existing GitHub issues
3. Create a new issue with detailed information
4. Include logs and error messages
5. Provide steps to reproduce the issue

This development guide provides comprehensive information for developing, testing, and deploying the Immermex Dashboard system. Follow the guidelines and best practices outlined here for optimal development experience.
