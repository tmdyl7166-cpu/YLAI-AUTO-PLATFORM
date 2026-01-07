from fastapi import APIRouter, HTTPException
from backend.services.plugin_market import plugin_market
from typing import Dict, Any
import json

router = APIRouter()

@router.get("/api/plugins")
def list_plugins():
    """列出所有已安装的插件"""
    # 自动发现插件
    discovered = plugin_market.discover_plugins()
    for plugin in discovered:
        plugin_id = plugin['id']
        if plugin_id not in plugin_market.available_plugins:
            plugin_market.available_plugins[plugin_id] = plugin

    installed = plugin_market.get_installed_plugins()
    available = plugin_market.get_available_plugins()

    return {
        "code": 0,
        "data": {
            "installed": installed,
            "available": available,
            "total_installed": len(installed),
            "total_available": len(available)
        }
    }

@router.get("/api/plugins/{plugin_id}")
def get_plugin_info(plugin_id: str):
    """获取插件详细信息"""
    installed = plugin_market.get_installed_plugins()
    available = plugin_market.get_available_plugins()

    plugin_info = installed.get(plugin_id) or available.get(plugin_id)
    if not plugin_info:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")

    # 获取插件能力
    capabilities = plugin_market.get_plugin_capabilities(plugin_id)

    return {
        "code": 0,
        "data": {
            **plugin_info,
            "capabilities": capabilities
        }
    }

@router.post("/api/plugins/{plugin_id}/install")
def install_plugin(plugin_id: str, source_url: str = None):
    """安装插件"""
    try:
        success = plugin_market.install_plugin(plugin_id, source_url)
        if success:
            return {"code": 0, "message": f"Plugin {plugin_id} installed successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to install plugin {plugin_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Installation failed: {e}")

@router.delete("/api/plugins/{plugin_id}")
def uninstall_plugin(plugin_id: str):
    """卸载插件"""
    try:
        success = plugin_market.uninstall_plugin(plugin_id)
        if success:
            return {"code": 0, "message": f"Plugin {plugin_id} uninstalled successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found or uninstall failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Uninstallation failed: {e}")

@router.post("/api/plugins/{plugin_id}/{function_name}")
async def execute_plugin_function(plugin_id: str, function_name: str, data: Dict[str, Any] = None):
    """执行插件中的函数"""
    try:
        result = await plugin_market.execute_plugin_function(plugin_id, function_name, **(data or {}))
        return {"code": 0, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plugin execution failed: {e}")

@router.post("/api/plugins/discover")
def discover_plugins():
    """重新发现插件"""
    try:
        plugin_market.update_plugin_registry()
        return {"code": 0, "message": "Plugin registry updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {e}")

@router.get("/api/plugins/{plugin_id}/capabilities")
def get_plugin_capabilities(plugin_id: str):
    """获取插件能力列表"""
    try:
        capabilities = plugin_market.get_plugin_capabilities(plugin_id)
        return {"code": 0, "data": capabilities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {e}")