from fastapi import APIRouter

router = APIRouter()


@router.get("/api/security/rbac")
def get_rbac_matrix():
    roles = [
        {
            "role": "admin",
            "description": "平台管理员，拥有全部权限",
            "permissions": [
                "read:pages", "read:apis", "run:scripts", "pipeline:run", "pipeline:monitor",
                "scheduler:config", "scheduler:circuit", "ai:invoke", "logs:read"
            ]
        },
        {
            "role": "operator",
            "description": "运维/操作人员，执行与监控",
            "permissions": [
                "read:pages", "read:apis", "run:scripts", "pipeline:run", "pipeline:monitor",
                "ai:invoke", "logs:read"
            ]
        },
        {
            "role": "viewer",
            "description": "只读观察者，访问页面与基础健康",
            "permissions": [
                "read:pages", "read:apis", "logs:read"
            ]
        }
    ]
    endpoints = [
        {"path": "/health", "methods": ["GET"], "required": ["read:apis"]},
        {"path": "/scripts", "methods": ["GET"], "required": ["read:apis"]},
        {"path": "/api/modules", "methods": ["GET"], "required": ["read:apis"]},
        {"path": "/api/run", "methods": ["POST"], "required": ["run:scripts"]},
        {"path": "/api/pipeline/run", "methods": ["POST"], "required": ["pipeline:run"]},
        {"path": "/ws/pipeline/{task_id}", "methods": ["WS"], "required": ["pipeline:monitor"]},
        {"path": "/api/scheduler/config", "methods": ["GET","POST"], "required": ["scheduler:config"]},
        {"path": "/api/scheduler/circuit", "methods": ["GET"], "required": ["scheduler:circuit"]},
        {"path": "/ai/pipeline", "methods": ["POST"], "required": ["ai:invoke"]},
        {"path": "/ws/logs", "methods": ["WS"], "required": ["logs:read"]},
    ]
    return {"code": 0, "data": {"roles": roles, "endpoints": endpoints}}
