# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

LJWX BigScreen is a Python Flask-based health monitoring dashboard system for wearable device data. It provides real-time monitoring, data analytics, and alerting for health metrics from wearable devices deployed in industrial environments.

**Architecture**: 
- **Backend**: Flask + SQLAlchemy + Redis + MySQL
- **Frontend**: HTML templates with ECharts.js for visualization
- **Real-time**: Flask-SocketIO for live updates
- **Deployment**: Docker multi-architecture support (AMD64/ARM64)

## Development Commands

### Start Application
```bash
# Primary method - from bigscreen/bigScreen/
cd bigscreen/bigScreen && python run_bigscreen.py

# Alternative method - from bigscreen/
cd bigscreen && python run.py

# All services (includes Celery workers and monitoring)
cd bigscreen && ./start_all.sh
```

### Database Operations
```bash
# Apply migrations
mysql -u root -p < database_migration.sql

# Optimize database indexes
mysql -u root -p < optimize_database_indexes.sql
```

### Testing
```bash
# Performance testing
cd bigscreen && ./performance_test.sh

# Health data system tests
python test_health_fix.py
python test_performance_optimization.py

# Device integration tests
python test_device_bind_integration.py

# Alert system tests
python test_alert_fix.py
```

### Docker Multi-Architecture Build
```bash
# Local build and push to Aliyun
./scripts/deploy-aliyun.sh

# Using GitHub Actions
git push origin main  # Triggers CI/CD pipeline
```

### Performance Monitoring
```bash
# System monitoring
python monitor.py

# Performance stress testing
python performance_stress_test.py
python queue_stress_test.py

# View performance report
# Navigate to http://localhost:5225/performance_test_report (local) or http://localhost:5001/performance_test_report (Docker)
```

## Core Architecture

### Main Application Structure
- **`bigscreen/bigScreen/bigScreen.py`**: Primary Flask application with API endpoints
- **`bigscreen/run.py`**: Application entry point with environment setup
- **`bigscreen/config.py`**: Central configuration management
- **`bigscreen/bigScreen/models.py`**: SQLAlchemy database models

### Key Modules
- **`user_health_data.py`**: Health metrics processing and analytics
- **`device.py`**: Device management and binding
- **`alert.py`**: Alert generation and WeChat notifications
- **`org.py`**: Organization and user management
- **`redis_helper.py`**: Redis caching layer
- **`optimized_health_data.py`**: High-performance data processing

### Database Schema
Primary tables:
- `t_user_health_data`: Health metrics from wearable devices
- `t_device_info`: Device registration and status
- `t_alert_info`: System alerts and notifications
- `t_user_info`: User management
- `t_org_info`: Organization structure

### API Endpoints Structure
- `/api/*`: RESTful API endpoints
- `/upload_*`: Data ingestion endpoints
- `/get_*`: Data retrieval endpoints
- Health dashboards: `/health_main`, `/health_table`, `/health_trends`
- Device monitoring: `/device_dashboard`, `/device_analysis`

## Configuration Management

### Environment Variables
Key variables in `.env` or environment:
- `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
- `APP_PORT` (default 5225 for local debug, 5001 for Docker)
- `WECHAT_APP_ID`, `WECHAT_APP_SECRET` for alerts

### UI Customization
Environment variables for branding:
- `BIGSCREEN_TITLE`, `COMPANY_NAME`, `COMPANY_LOGO_URL`
- `THEME_COLOR`, `BACKGROUND_COLOR`

## Performance Optimizations

### Known Performance Issues Resolved
- **N+1 Query Problem**: Fixed in `get_all_health_data_by_orgIdAndUserId` - now uses batch queries
- **Connection Timeout**: Optimized from 181s to <5s response times
- **Cache Implementation**: Redis caching with 3-5 minute TTL for frequently accessed data

### Performance Testing
The system includes comprehensive performance testing:
- **Target Performance**: 1000 devices, <3s response time
- **Achieved Performance**: 2000 devices, QPS >1400, 100% success rate
- **Monitoring**: Real-time system metrics and database performance tracking

### Memory and Resource Management
- Connection pooling: 30 base + 50 overflow connections
- Batch processing: 200 records per batch
- Redis pipeline: 100 operations per batch
- Async workers: 20 threads for non-critical operations

## Testing Patterns

### Test Categories
1. **Unit Tests**: `test_*.py` files for individual modules
2. **Integration Tests**: `test_*_integration.py` for cross-module functionality
3. **Performance Tests**: `performance_*.py` and `stress_test.py`
4. **API Tests**: Testing data upload/retrieval endpoints

### Test Data Generation
- `mock_health_data.py`: Generate test health data
- `demo_batch_insert.py`: Large dataset for testing
- `simulate_health_data.py`: Real-time simulation

## Deployment

### Docker Configuration
- **Multi-architecture**: Supports AMD64 and ARM64
- **Registry**: Aliyun Container Registry
- **Files**: `Dockerfile.multiarch`, `docker-compose.yml`

### CI/CD Pipeline
- **GitHub Actions**: `.github/workflows/build.yml`
- **Auto-build**: Triggered on push to main branch
- **Multi-arch build**: Uses Docker Buildx
- **Registry push**: Automated push to Aliyun registry

## Debugging and Troubleshooting

### Common Issues
1. **JavaScript Errors**: Fixed with global error handling in `fix_js_errors.html`
2. **Import Errors**: Use `run_bigscreen.py` for proper Python path setup
3. **Database Connection**: Check `config.py` MySQL settings
4. **Performance**: Monitor with `/system_monitor` endpoint

### Logging
- **Main logs**: `bigscreen.log`, `system.log`
- **API logs**: Structured logging with different levels
- **Performance logs**: `performance_data.json` for metrics

### Monitoring Endpoints
- `/api/realtime_stats`: System statistics
- `/system_monitor`: Performance monitoring dashboard
- `/performance_test_report`: Load testing interface
- `/health` or `/api/health`: Health check endpoints (added in v1.3.3)

## Code Style Notes

- **Chinese Comments**: Code uses Chinese comments for business logic
- **Compact Style**: Golf-style coding with minimal line count
- **Error Handling**: Comprehensive try-catch with graceful degradation
- **Security**: Non-root Docker user, input validation, SQL injection prevention

## Important: Performance-Critical Functions

When modifying these functions, always test performance impact:
- `fetch_health_data_by_orgIdAndUserId`
- `get_all_health_data_by_orgIdAndUserId`
- `optimized_upload_health_data`
- Any database query functions in high-traffic endpoints

## Version Management

Current version: 1.3.3
- Port configuration update: Local debug uses 5225, Docker uses 5001
- Added health check endpoints: `/health` and `/api/health`
- Health checks validate database and Redis connections
- Docker configuration remains unchanged for deployment consistency

Previous versions:
- 1.3.2: Multi-architecture Docker support, Radar chart sleep data fix
- Performance optimizations for ConnectionResetError/BrokenPipeError
- JavaScript error handling improvements

## Port Configuration

### Local Development
- **Port**: 5225 (configured in `config.py`)
- **Access**: http://localhost:5225
- **Health Check**: http://localhost:5225/health

### Docker Deployment
- **Port**: 5001 (configured in `docker-compose.yml`)
- **Access**: http://localhost:5001
- **Health Check**: http://localhost:5001/health

### Important Notes
- **DO NOT STOP** ljwx-bigscreen service when making configuration changes
- Health endpoints return JSON with service status, database, and Redis connection status
- Port changes are backward compatible with existing deployment scripts