# Troubleshooting & FAQ - Immermex Dashboard

## Common Issues and Solutions

### 1. API Issues

#### Q: API returns 500 Internal Server Error
**A:** This usually indicates a server-side error. Check the following:

1. **Database Connection**:
   ```bash
   # Check if database is accessible
   curl -X GET https://immermex-backend.onrender.com/api/health
   ```

2. **Environment Variables**:
   - Verify all required environment variables are set in Vercel
   - Check `DATABASE_URL` is correct
   - Ensure `SECRET_KEY` is configured

3. **Dependencies**:
   - Check if all Python dependencies are installed
   - Verify `requirements.txt` is up to date

4. **Logs**:
   - Check Vercel function logs for detailed error messages
   - Look for import errors or missing modules

#### Q: API returns 422 Unprocessable Entity
**A:** This indicates validation errors. Common causes:

1. **File Upload Issues**:
   - Ensure file is in Excel format (.xlsx or .xls)
   - Check file size is under 10MB
   - Verify file is not corrupted

2. **Parameter Validation**:
   - Check query parameters are correctly formatted
   - Ensure required fields are provided
   - Verify data types match expected formats

3. **Request Format**:
   - Use correct Content-Type headers
   - Ensure multipart/form-data for file uploads
   - Verify JSON format for POST requests

#### Q: API returns 429 Too Many Requests
**A:** Rate limiting is active. Solutions:

1. **Wait and Retry**:
   - Wait for the rate limit window to reset
   - Implement exponential backoff in your client

2. **Check Rate Limits**:
   - Upload endpoints: 5 requests per 5 minutes
   - KPI endpoints: 30 requests per minute
   - General endpoints: 100 requests per minute

3. **Optimize Requests**:
   - Use caching to reduce API calls
   - Batch requests when possible
   - Implement request queuing

### 2. Database Issues

#### Q: Database connection fails
**A:** Check the following:

1. **Connection String**:
   ```python
   # Verify DATABASE_URL format
   DATABASE_URL=postgresql://user:password@host:port/database
   ```

2. **Network Access**:
   - Ensure database allows connections from Vercel IPs
   - Check firewall settings
   - Verify SSL configuration

3. **Credentials**:
   - Verify username and password are correct
   - Check if user has necessary permissions
   - Ensure database exists

#### Q: Data not saving after upload
**A:** Common causes:

1. **Transaction Issues**:
   - Check if database transactions are being committed
   - Verify rollback conditions are not being triggered

2. **Validation Failures**:
   - Check if data validation is failing silently
   - Verify required fields are present
   - Ensure data types are correct

3. **Duplicate Data**:
   - Check if duplicate file hash is preventing save
   - Verify unique constraints are not violated

#### Q: KPI calculations are incorrect
**A:** Check the following:

1. **Data Relationships**:
   - Verify factura-cobranza relationships via UUID
   - Check pedido-factura relationships via folio_factura
   - Ensure data integrity

2. **Filter Logic**:
   - Check if filters are being applied correctly
   - Verify proportional calculations for pedido filters
   - Ensure date ranges are inclusive

3. **Data Quality**:
   - Verify data is complete and accurate
   - Check for missing or null values
   - Ensure currency amounts are correct

### 3. Frontend Issues

#### Q: Frontend not loading
**A:** Check the following:

1. **Build Issues**:
   ```bash
   # Check if build completed successfully
   cd frontend
   npm run build
   ```

2. **Deployment Issues**:
   - Verify GitHub Pages deployment is successful
   - Check if files are present in the `dist` folder
   - Ensure `_redirects` file is configured

3. **Network Issues**:
   - Check if API endpoints are accessible
   - Verify CORS configuration
   - Test with browser developer tools

#### Q: Charts not displaying
**A:** Common causes:

1. **Data Issues**:
   - Check if API is returning data
   - Verify data format matches chart expectations
   - Ensure data is not empty or null

2. **Component Issues**:
   - Check if chart components are imported correctly
   - Verify Recharts library is installed
   - Ensure component props are correct

3. **Styling Issues**:
   - Check if CSS is loading correctly
   - Verify Tailwind CSS is configured
   - Ensure component dimensions are set

#### Q: File upload not working
**A:** Check the following:

1. **File Format**:
   - Ensure file is Excel format (.xlsx or .xls)
   - Check file is not corrupted
   - Verify file size is under 10MB

2. **Network Issues**:
   - Check if API endpoint is accessible
   - Verify CORS configuration
   - Test with browser developer tools

3. **Component Issues**:
   - Check if FileUpload component is working
   - Verify event handlers are attached
   - Ensure form submission is correct

### 4. Performance Issues

#### Q: Slow API responses
**A:** Optimize the following:

1. **Database Queries**:
   - Check if indexes are being used
   - Optimize complex queries
   - Use connection pooling

2. **Caching**:
   - Implement response caching
   - Use database query caching
   - Cache expensive calculations

3. **Data Processing**:
   - Optimize Excel processing logic
   - Use batch processing for large files
   - Implement pagination for large datasets

#### Q: Frontend is slow
**A:** Optimize the following:

1. **Bundle Size**:
   - Check bundle size with webpack-bundle-analyzer
   - Implement code splitting
   - Remove unused dependencies

2. **Component Performance**:
   - Use React.memo for expensive components
   - Implement useMemo and useCallback
   - Optimize re-renders

3. **API Calls**:
   - Implement request caching
   - Use debouncing for search inputs
   - Batch API requests when possible

### 5. Deployment Issues

#### Q: Vercel deployment fails
**A:** Check the following:

1. **Build Errors**:
   - Check build logs in Vercel dashboard
   - Verify all dependencies are in requirements.txt
   - Ensure Python version is compatible

2. **Environment Variables**:
   - Verify all required environment variables are set
   - Check variable names and values
   - Ensure sensitive data is properly configured

3. **Function Limits**:
   - Check if function execution time exceeds limits
   - Verify memory usage is within limits
   - Ensure file size limits are respected

#### Q: GitHub Pages deployment fails
**A:** Check the following:

1. **Build Process**:
   - Check GitHub Actions workflow logs
   - Verify Node.js version is compatible
   - Ensure all dependencies are installed

2. **Repository Settings**:
   - Verify GitHub Pages is enabled
   - Check if source branch is correct
   - Ensure repository is public (for free accounts)

3. **File Issues**:
   - Check if build output is in correct directory
   - Verify `_redirects` file is present
   - Ensure all assets are included

### 6. Data Processing Issues

#### Q: Excel file processing fails
**A:** Check the following:

1. **File Format**:
   - Ensure file is valid Excel format
   - Check if file is password protected
   - Verify file is not corrupted

2. **Sheet Structure**:
   - Verify required sheets exist (Facturacion, Cobranza, Pedidos)
   - Check if column names match expected format
   - Ensure data is in correct format

3. **Data Validation**:
   - Check if data validation is failing
   - Verify required fields are present
   - Ensure data types are correct

#### Q: Data relationships are incorrect
**A:** Check the following:

1. **UUID Matching**:
   - Verify factura UUIDs match between sheets
   - Check if UUIDs are unique and consistent
   - Ensure UUID format is correct

2. **Foreign Keys**:
   - Check folio_factura relationships
   - Verify cliente names match between sheets
   - Ensure date formats are consistent

3. **Data Integrity**:
   - Check for duplicate records
   - Verify data completeness
   - Ensure business logic is correct

## Debugging Techniques

### 1. Backend Debugging

#### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug endpoints
@app.get("/api/debug/test")
async def debug_test():
    return {"status": "debug", "timestamp": datetime.utcnow()}
```

#### Check Database Connection
```python
from database import engine
from sqlalchemy import text

def check_db_connection():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Database connected successfully")
    except Exception as e:
        print(f"Database connection failed: {e}")
```

#### Monitor API Performance
```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return wrapper
```

### 2. Frontend Debugging

#### Enable Debug Mode
```typescript
// Add to your component
const [debugMode, setDebugMode] = useState(false);

useEffect(() => {
  if (debugMode) {
    console.log('Debug mode enabled');
    console.log('Component state:', { data, loading, error });
  }
}, [debugMode, data, loading, error]);
```

#### Monitor API Calls
```typescript
// Add to your API service
const originalFetch = window.fetch;
window.fetch = async (...args) => {
  console.log('API Call:', args[0]);
  const start = Date.now();
  const response = await originalFetch(...args);
  const end = Date.now();
  console.log(`API Response: ${response.status} (${end - start}ms)`);
  return response;
};
```

#### Check Component Performance
```typescript
import { Profiler } from 'react';

function onRenderCallback(id, phase, actualDuration) {
  console.log('Component render:', { id, phase, actualDuration });
}

<Profiler id="MyComponent" onRender={onRenderCallback}>
  <MyComponent />
</Profiler>
```

### 3. Database Debugging

#### Check Query Performance
```sql
-- Enable query logging
SET log_statement = 'all';
SET log_duration = on;

-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

#### Monitor Database Connections
```sql
-- Check active connections
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE state = 'active';

-- Check connection limits
SHOW max_connections;
```

## Performance Monitoring

### 1. API Performance

#### Response Time Monitoring
```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

#### Error Rate Monitoring
```python
from collections import defaultdict
import time

error_counts = defaultdict(int)
request_counts = defaultdict(int)

@app.middleware("http")
async def monitor_errors(request: Request, call_next):
    endpoint = request.url.path
    request_counts[endpoint] += 1
    
    try:
        response = await call_next(request)
        if response.status_code >= 400:
            error_counts[endpoint] += 1
        return response
    except Exception as e:
        error_counts[endpoint] += 1
        raise
```

### 2. Frontend Performance

#### Core Web Vitals Monitoring
```typescript
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToAnalytics(metric) {
  console.log('Web Vital:', metric);
  // Send to your analytics service
}

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

#### Bundle Size Monitoring
```typescript
// Add to your build process
import { bundleAnalyzer } from 'webpack-bundle-analyzer';

if (process.env.ANALYZE) {
  bundleAnalyzer({
    analyzerMode: 'static',
    openAnalyzer: true,
  });
}
```

## Getting Help

### 1. Documentation Resources

- **API Documentation**: `/docs` endpoint when running locally
- **System Architecture**: `docs/SYSTEM_ARCHITECTURE.md`
- **Development Guide**: `docs/DEVELOPMENT_GUIDE.md`
- **API Reference**: `docs/API_DOCUMENTATION.md`

### 2. Community Support

- **GitHub Issues**: Create an issue with detailed information
- **GitHub Discussions**: Ask questions and share solutions
- **Code Review**: Request code review for complex changes

### 3. Creating Effective Bug Reports

When reporting issues, include:

1. **Environment Information**:
   - Operating system and version
   - Node.js and Python versions
   - Browser and version (for frontend issues)

2. **Steps to Reproduce**:
   - Clear, numbered steps
   - Expected vs actual behavior
   - Screenshots or error messages

3. **Error Information**:
   - Full error messages
   - Stack traces
   - Log files (if applicable)

4. **Additional Context**:
   - When the issue started
   - What changed recently
   - Workarounds (if any)

### 4. Emergency Procedures

#### System Down
1. Check health endpoint: `/api/health`
2. Verify database connectivity
3. Check Vercel deployment status
4. Review recent changes and rollback if necessary

#### Data Corruption
1. Stop all data processing
2. Backup current database state
3. Identify the source of corruption
4. Restore from last known good backup
5. Re-process affected data

#### Security Incident
1. Immediately revoke compromised credentials
2. Check access logs for suspicious activity
3. Update all security keys and tokens
4. Review and update security configurations
5. Notify relevant stakeholders

This troubleshooting guide should help resolve most common issues with the Immermex Dashboard system. For issues not covered here, please create a detailed GitHub issue with all relevant information.
