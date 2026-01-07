"""
后端 API 路由统一注册表
提供一个中央位置管理所有 API 路由，便于维护和自动化生成文档

使用方式:
    from backend.api.router_registry import register_routers
    register_routers(app)
"""

from typing import Dict, Any, Type
import importlib
from fastapi import FastAPI
from fastapi.routing import APIRouter

# 路由注册表：定义所有后端路由及其元数据
ROUTER_REGISTRY: Dict[str, Dict[str, Any]] = {
    # 认证与权限
    "auth": {
        "module": "backend.api.auth",
        "prefix": "/api/auth",
        "tags": ["auth"],
        "description": "Authentication and authorization endpoints"
    },
    # 基础路由
    "base": {
        "module": "backend.api.base_router",
        "prefix": "/api",
        "tags": ["base"],
        "description": "Base API endpoints"
    },
    # 流水线与 DAG
    "pipeline": {
        "module": "backend.api.pipeline",
        "prefix": "/api/pipeline",
        "tags": ["pipeline"],
        "description": "DAG pipeline management"
    },
    # 任务管理
    "tasks": {
        "module": "backend.api.tasks_router",
        "prefix": "/api/tasks",
        "tags": ["tasks"],
        "description": "Task execution and management"
    },
    # 监控与健康检查
    "monitor": {
        "module": "backend.api.monitor",
        "prefix": "/api/monitor",
        "tags": ["monitor"],
        "description": "System monitoring and health checks"
    },
    # 仪表板
    "dashboard": {
        "module": "backend.api.dashboard",
        "prefix": "/api/dashboard",
        "tags": ["dashboard"],
        "description": "Dashboard data and statistics"
    },
    # 策略与规则
    "policy": {
        "module": "backend.api.policy",
        "prefix": "/api/policy",
        "tags": ["policy"],
        "description": "Policy and rule management"
    },
    # 安全与权限
    "security": {
        "module": "backend.api.security",
        "prefix": "/api/security",
        "tags": ["security"],
        "description": "Security management"
    },
    # AI 优化
    "ai_optimize": {
        "module": "backend.api.ai_optimize",
        "prefix": "/api/ai",
        "tags": ["ai"],
        "description": "AI-driven optimization"
    },
    # 插件管理
    "plugins": {
        "module": "backend.api.plugins_router",
        "prefix": "/api/plugins",
        "tags": ["plugins"],
        "description": "Plugin management"
    },
    # 文档
    "docs": {
        "module": "backend.api.docs_router",
        "prefix": "/api/docs",
        "tags": ["docs"],
        "description": "API documentation"
    },
}

# 可选路由（根据环境或配置条件加载）
OPTIONAL_ROUTERS = {
    "demo": {
        "module": "backend.api.demo_router",
        "prefix": "/api/demo",
        "tags": ["demo"],
        "description": "Demo endpoints (development only)",
        "enabled": True  # 可根据环境变量控制
    },
    "phone": {
        "module": "backend.api.phone_router",
        "prefix": "/api/phone",
        "tags": ["phone"],
        "description": "Phone-related operations",
        "enabled": True
    },
}


def register_routers(app: FastAPI, include_optional: bool = True) -> Dict[str, Any]:
    """
    注册所有路由到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
        include_optional: 是否包含可选路由

    Returns:
        注册结果汇总（包含成功/失败的路由）

    使用示例:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> register_routers(app)
    """
    result = {
        "registered": [],
        "failed": [],
        "skipped": [],
    }

    # 注册主路由表
    for name, config in ROUTER_REGISTRY.items():
        try:
            module = importlib.import_module(config["module"])
            
            # 尝试获取 router 对象
            if not hasattr(module, "router"):
                result["failed"].append({
                    "name": name,
                    "reason": f"Module {config['module']} has no 'router' attribute"
                })
                continue

            router: APIRouter = module.router
            app.include_router(
                router,
                prefix=config["prefix"],
                tags=config["tags"]
            )
            result["registered"].append(name)

        except ImportError as e:
            result["failed"].append({
                "name": name,
                "reason": f"ImportError: {str(e)}"
            })
        except Exception as e:
            result["failed"].append({
                "name": name,
                "reason": f"Error: {str(e)}"
            })

    # 注册可选路由
    if include_optional:
        for name, config in OPTIONAL_ROUTERS.items():
            if not config.get("enabled", True):
                result["skipped"].append(name)
                continue

            try:
                module = importlib.import_module(config["module"])

                if not hasattr(module, "router"):
                    result["failed"].append({
                        "name": name,
                        "reason": f"Module {config['module']} has no 'router' attribute"
                    })
                    continue

                router: APIRouter = module.router
                app.include_router(
                    router,
                    prefix=config["prefix"],
                    tags=config["tags"]
                )
                result["registered"].append(name)

            except ImportError:
                result["skipped"].append(name)
            except Exception as e:
                result["failed"].append({
                    "name": name,
                    "reason": f"Error: {str(e)}"
                })

    return result


def get_router_info() -> Dict[str, Any]:
    """
    获取路由信息汇总（用于文档生成、监控等）

    Returns:
        包含所有路由的信息字典
    """
    all_routers = {**ROUTER_REGISTRY, **OPTIONAL_ROUTERS}
    
    return {
        "total": len(all_routers),
        "routers": all_routers,
        "prefixes": [config["prefix"] for config in all_routers.values()],
        "tags": list(set(config["tags"][0] for config in all_routers.values())),
    }
