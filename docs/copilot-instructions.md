# YLAI-AUTO-PLATFORM Copilot Instructions

## Architecture Overview

**Enterprise automated crawler platform** with unified kernel architecture:
- **Backend**: FastAPI (async) + script registry system + WebSocket real-time comms
- **Frontend**: Vue3 SPA with hash routing + component-based UI
- **AI Services**: Local model integration + inference pipelines
- **Deployment**: Docker Compose orchestration + multi-environment configs

**Key structural decisions**:
- Node-based API routing (`/api/node.*`) for modular service boundaries
- Script auto-registration via `@registry.register()` decorators
- Function registry JSON mapping frontend components to backend APIs
- Unified interface mapping table (`frontend/pages/统一接口映射表.md`) as API contract

## Critical Developer Workflows

### Multi-Service Startup (Essential)
```bash
# Full stack development
./start.sh all                    # API (8001) + Frontend (8080) background
./start.sh dev-frontend          # Hot-reload frontend dev server
./start.sh dev-backend           # Uvicorn --reload backend

# Production deployment
./start.sh docker-up             # Full container stack (api+web+ai)
./start.sh containers            # Build and start all services

# Health verification (always run after startup)
./start.sh full-checks           # API + pages + WebSocket validation
curl http://localhost:8001/health # Basic health check
```

### Script Development Pattern
```python
# backend/YLAI-AUTO-PLATFORM/scripts/your_script.py
from backend.core.base import BaseScript
from backend.core.registry import registry

@registry.register("your_script_name")  # ← Required for auto-discovery
class YourScript(BaseScript):
    def run(self, **kwargs):
        # Business logic here
        return {"result": "data"}
```

### API Development Pattern
```python
# backend/api/your_router.py
from fastapi import APIRouter
from backend.api.auth import require_perm

router = APIRouter()

@router.post("/your/endpoint")
async def your_endpoint(data: dict, user=Depends(require_perm("your:permission"))):
    # Implementation
    pass
```

## Project-Specific Conventions

### Configuration Hierarchy (Read in order)
1. `config/function_registry.json` - Frontend-backend function mapping
2. `config/modules_policy.json` - RBAC permission policies
3. `config/核心指向.json` - Core system pointers
4. `config/规则.md` - Business rules (Chinese)
5. Environment variables override all configs

### API Patterns
- **Node-based routing**: `/api/node.ai/*`, `/api/node.crawler/*`, etc.
- **Permission guards**: `require_perm("module:action")` on all endpoints
- **WebSocket channels**: `/ws/pipeline/{task_id}`, `/ws/logs`, `/ws/monitor`
- **Response format**: `{"status": "success", "data": {...}}` or error details

### Frontend Patterns
- **Hash routing**: Vue Router with `createWebHashHistory()`
- **Component structure**: `/static/js/components/` + `/static/js/pages/`
- **State management**: Pinia stores in `/static/js/stores/`
- **API calls**: Direct fetch to backend (no proxy in dev mode)

### Error Handling
- **Backend**: Structured error responses with error codes
- **Frontend**: Toast notifications + error boundaries
- **WebSocket**: Automatic reconnection with exponential backoff

## Integration Points

### Cross-Component Communication
- **WebSocket Manager**: `backend/ws/manager.py` coordinates real-time updates
- **Task Manager**: `backend/ws/task_manager.py` handles async job lifecycle
- **Plugin System**: `backend/services/plugin_manager.py` for hot-loaded extensions

### External Dependencies
- **AI Bridge**: `backend/ai_bridge.py` interfaces with local AI models
- **Docker Services**: `ai-docker/`, `docker/` for containerized components
- **Frontend Assets**: Served from `/static/` with version query params

## Key Files for Understanding

### Architecture Foundation
- `backend/core/registry.py` - Script auto-registration system
- `backend/app.py` - FastAPI application with all routers
- `frontend/static/js/app.js` - Vue app with routing setup
- `config/function_registry.json` - Frontend-backend mapping contract

### Developer Workflows
- `start.sh` - Multi-mode deployment script (read this first)
- `YLAI-AUTO-PLATFORM/scripts/hx.py` - File monitoring and AI optimization
- `docs/PROJECT_FUNCTIONALITY_DESCRIPTION.md` - Complete feature overview

### Configuration Examples
- `frontend/pages/统一接口映射表.md` - API contract specification
- `config/modules_policy.json` - Permission structure
- `docker/docker-compose.yml` - Service orchestration

## Common Pitfalls

- **Script registration**: Always use `@registry.register("unique_name")` or scripts won't be discovered
- **Permission checks**: Add `require_perm()` to all API endpoints or they'll be unsecured
- **WebSocket connections**: Use the centralized `ws_manager` instead of direct WebSocket creation
- **Configuration loading**: Respect the config hierarchy order (function_registry → modules_policy → core pointers)

## Development Best Practices

- **Testing**: Run `./start.sh full-checks` after any backend changes
- **Frontend dev**: Use `./start.sh dev-frontend` for hot-reload development
- **API docs**: Update `frontend/pages/统一接口映射表.md` when adding new endpoints
- **Configuration**: Test config changes across all environments (dev/test/prod)

Remember: This is a complex enterprise platform. Always run health checks after changes and consult the unified interface mapping table for API contracts.