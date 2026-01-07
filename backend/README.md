# Backend Documentation

This document describes the backend module of the YLAI-AUTO-PLATFORM project.

## Overview

The backend is built with FastAPI and provides REST APIs, WebSocket support, and various services for AI automation platform.

## Main Entry Points

### app.py
**Purpose**: Main FastAPI application with all routes and middleware.

**Startup Command**:
```bash
YLAI-AUTO-PLATFORM/backend/app.py --host 0.0.0.0 --port 8001 --reload
```

**Features**:
- CORS middleware
- Static file serving
- WebSocket endpoints
- API routes for various functionalities
- Authentication and authorization
- Monitoring and logging

### main.py
**Purpose**: Enhanced startup script with AI coordination and automated processing pipeline.

**Startup Command**:
```bash
YLAI-AUTO-PLATFORM/backend/main.py
```

**Features**:
- Initializes AI coordinator
- Starts web console on port 9001
- Runs automated processing pipeline
- Integrates AI enhancement for processing results

### proxy_main.py
**Purpose**: Ollama proxy server for AI model interactions.

**Startup Command**:
```bash
YLAI-AUTO-PLATFORM/backend/proxy_main.py --host 0.0.0.0 --port 8002
```

**Features**:
- Proxies requests to Ollama API
- Model validation
- Serves frontend files

### web_console.py
**Purpose**: Web console application for system management.

**Startup Command**:
```bash
YLAI-AUTO-PLATFORM/backend/web_console.py --host 0.0.0.0 --port 9001
```

**Features**:
- Scheduled task triggering
- System monitoring
- AI coordinator integration

## Directory Structure

### api/
Contains API route handlers:
- `advanced_router.py`: Advanced operations
- `auth.py`: Authentication and authorization
- `dashboard.py`: Dashboard endpoints
- `monitor.py`: Monitoring APIs
- `pipeline.py`: Pipeline management
- `tasks_router.py`: Task management
- And many more specialized routers

### core/
Core business logic:
- `kernel.py`: Main kernel for script execution
- `pipeline.py`: DAG pipeline processing
- `logger.py`: Logging utilities
- `task.py`: Task definitions
- `registry.py`: Script registry

### services/
Background services:
- `ai_service.py`: AI model services
- `cache_service.py`: Caching layer
- `database_service.py`: Database operations
- `monitoring_service.py`: System monitoring
- `plugin_manager.py`: Plugin system

### scripts/
Executable scripts for various tasks:
- `ai_coordinator.py`: AI model coordination
- `auto_heal.py`: Auto-healing mechanisms
- `data_collector.py`: Data collection
- `monitor.py`: Monitoring scripts
- `proxy_manager.py`: Proxy management
- And many more utility scripts

### models/
Data models and schemas.

### config/
Configuration files.

### tests/
Unit and integration tests.

## Key Components

### Kernel
The core execution engine that loads and runs scripts from the registry.

### Pipeline
DAG-based processing pipeline for complex workflows.

### AI Bridge
Integration with AI models for intelligent processing.

### WebSocket Manager
Real-time communication for monitoring and updates.

### Plugin System
Extensible plugin architecture for additional functionalities.

## Dependencies

See `requirements.txt` for Python dependencies.

## Testing

Run tests with:
```bash
YLAI-AUTO-PLATFORM/backend/tests/
```

## Notes

- All entry points are independent and serve different purposes
- Main application is `app.py` for standard API usage
- `main.py` provides enhanced automation features
- Proxy and console apps are optional components
- No duplicate functionality across modules</content>
<parameter name="filePath">/home/yldaima/桌面/编程/YLAI-AUTO-PLATFORM/backend/README.md