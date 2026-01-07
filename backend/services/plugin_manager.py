import json
import os
import importlib.util
from typing import Dict, Any, List
from pathlib import Path

class PluginManager:
    def __init__(self, registry_path: str = "function_registry.json"):
        self.registry_path = Path(registry_path)
        self.plugins: Dict[str, Any] = {}
        self.functions: List[Dict[str, Any]] = []
        self.load_registry()

    def load_registry(self):
        """加载插件注册表"""
        if not self.registry_path.exists():
            print(f"Registry file not found: {self.registry_path}")
            return

        with open(self.registry_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.functions = data.get('functions', [])
        plugins_data = data.get('plugins', {})

        for plugin_id, plugin_info in plugins_data.items():
            if plugin_info.get('enabled', False):
                self.load_plugin(plugin_id, plugin_info)

    def load_plugin(self, plugin_id: str, plugin_info: Dict[str, Any]):
        """动态加载插件"""
        plugin_path = plugin_info.get('path')
        if not plugin_path:
            print(f"No path for plugin {plugin_id}")
            return

        plugin_dir = Path(plugin_path)
        if not plugin_dir.exists():
            print(f"Plugin directory not found: {plugin_dir}")
            return

        # 查找插件主文件（假设是__init__.py或main.py）
        main_file = plugin_dir / '__init__.py'
        if not main_file.exists():
            main_file = plugin_dir / 'main.py'
        if not main_file.exists():
            print(f"No main file found for plugin {plugin_id}")
            return

        try:
            spec = importlib.util.spec_from_file_location(plugin_id, main_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.plugins[plugin_id] = module
            print(f"Loaded plugin: {plugin_id}")
        except Exception as e:
            print(f"Failed to load plugin {plugin_id}: {e}")

    def get_plugin(self, plugin_id: str):
        """获取已加载的插件"""
        return self.plugins.get(plugin_id)

    def get_functions(self) -> List[Dict[str, Any]]:
        """获取所有函数定义"""
        return self.functions

    def execute_plugin_function(self, plugin_id: str, func_name: str, *args, **kwargs):
        """执行插件中的函数"""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not loaded")

        func = getattr(plugin, func_name, None)
        if not func:
            raise ValueError(f"Function {func_name} not found in plugin {plugin_id}")

        return func(*args, **kwargs)

# 全局插件管理器实例
plugin_manager = PluginManager()