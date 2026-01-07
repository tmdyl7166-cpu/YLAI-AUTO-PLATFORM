"""
插件市场系统
提供插件的自动发现、安装、版本管理和依赖解决
"""

import json
import os
import hashlib
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import aiohttp
import zipfile
import tempfile

class PluginMarket:
    """插件市场管理器"""

    def __init__(self, plugins_dir: str = "plugins", registry_file: str = "config/plugin_registry.json"):
        self.plugins_dir = Path(plugins_dir)
        self.registry_file = Path(registry_file)
        self.installed_plugins: Dict[str, Dict[str, Any]] = {}
        self.available_plugins: Dict[str, Dict[str, Any]] = {}
        self.plugins_dir.mkdir(exist_ok=True)
        self.load_registry()

    def load_registry(self):
        """加载插件注册表"""
        if self.registry_file.exists():
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.installed_plugins = data.get('installed', {})
                self.available_plugins = data.get('available', {})

    def save_registry(self):
        """保存插件注册表"""
        data = {
            'installed': self.installed_plugins,
            'available': self.available_plugins,
            'last_updated': datetime.now().isoformat()
        }
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def discover_plugins(self) -> List[Dict[str, Any]]:
        """自动发现本地插件"""
        discovered = []
        if not self.plugins_dir.exists():
            return discovered

        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('.'):
                plugin_info = self._analyze_plugin(plugin_dir)
                if plugin_info:
                    discovered.append(plugin_info)

        return discovered

    def _analyze_plugin(self, plugin_dir: Path) -> Optional[Dict[str, Any]]:
        """分析插件信息"""
        # 查找插件配置文件
        config_files = ['plugin.json', 'manifest.json', '__init__.py']

        for config_file in config_files:
            config_path = plugin_dir / config_file
            if config_path.exists():
                try:
                    if config_file.endswith('.json'):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                    else:
                        # 从__init__.py中提取信息
                        config = self._extract_from_init(config_path)

                    return {
                        'id': plugin_dir.name,
                        'name': config.get('name', plugin_dir.name),
                        'version': config.get('version', '1.0.0'),
                        'description': config.get('description', ''),
                        'author': config.get('author', 'Unknown'),
                        'dependencies': config.get('dependencies', []),
                        'path': str(plugin_dir),
                        'status': 'installed' if plugin_dir.name in self.installed_plugins else 'available'
                    }
                except Exception as e:
                    print(f"Error analyzing plugin {plugin_dir.name}: {e}")

        return None

    def _extract_from_init(self, init_file: Path) -> Dict[str, Any]:
        """从__init__.py中提取插件信息"""
        config = {}
        try:
            with open(init_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 简单的模式匹配提取信息
            import re
            patterns = {
                'name': r'PLUGIN_NAME\s*=\s*[\'"](.*?)[\'"]',
                'version': r'PLUGIN_VERSION\s*=\s*[\'"](.*?)[\'"]',
                'description': r'PLUGIN_DESCRIPTION\s*=\s*[\'"](.*?)[\'"]',
                'author': r'PLUGIN_AUTHOR\s*=\s*[\'"](.*?)[\'"]'
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    config[key] = match.group(1)

        except Exception as e:
            print(f"Error extracting from {init_file}: {e}")

        return config

    def install_plugin(self, plugin_id: str, source_url: Optional[str] = None) -> bool:
        """安装插件"""
        try:
            if source_url:
                # 从URL安装
                import asyncio
                return asyncio.run(self._install_from_url(plugin_id, source_url))
            else:
                # 从本地安装
                return self._install_from_local(plugin_id)
        except Exception as e:
            print(f"Failed to install plugin {plugin_id}: {e}")
            return False

    def _install_from_local(self, plugin_id: str) -> bool:
        """从本地安装插件"""
        plugin_dir = self.plugins_dir / plugin_id
        if not plugin_dir.exists():
            print(f"Plugin {plugin_id} not found locally")
            return False

        plugin_info = self._analyze_plugin(plugin_dir)
        if not plugin_info:
            print(f"Invalid plugin structure for {plugin_id}")
            return False

        # 检查依赖
        if not self._check_dependencies(plugin_info.get('dependencies', [])):
            print(f"Dependencies not satisfied for {plugin_id}")
            return False

        # 注册插件
        self.installed_plugins[plugin_id] = {
            **plugin_info,
            'installed_at': datetime.now().isoformat(),
            'status': 'active'
        }

        self.save_registry()
        print(f"Successfully installed plugin: {plugin_id}")
        return True

    async def _install_from_local_async(self, plugin_id: str) -> bool:
        """异步版本的本地安装"""
        return self._install_from_local(plugin_id)

    async def _install_from_url(self, plugin_id: str, source_url: str) -> bool:
        """从URL安装插件"""
        try:
            # 下载并解压插件
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / f"{plugin_id}.zip"

                # 下载
                async with aiohttp.ClientSession() as session:
                    async with session.get(source_url) as response:
                        if response.status != 200:
                            print(f"Failed to download plugin from {source_url}")
                            return False

                        with open(zip_path, 'wb') as f:
                            f.write(await response.read())

                # 解压
                plugin_dir = self.plugins_dir / plugin_id
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(plugin_dir)

            return await self._install_from_local_async(plugin_id)

        except Exception as e:
            print(f"Failed to install from URL: {e}")
            return False

    def uninstall_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        if plugin_id not in self.installed_plugins:
            print(f"Plugin {plugin_id} not installed")
            return False

        try:
            # 移除插件目录
            plugin_dir = self.plugins_dir / plugin_id
            if plugin_dir.exists():
                import shutil
                shutil.rmtree(plugin_dir)

            # 从注册表移除
            del self.installed_plugins[plugin_id]
            self.save_registry()

            print(f"Successfully uninstalled plugin: {plugin_id}")
            return True

        except Exception as e:
            print(f"Failed to uninstall plugin {plugin_id}: {e}")
            return False

    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """检查依赖是否满足"""
        # 简化的依赖检查逻辑
        # 在实际实现中，这里应该检查Python包、其他插件等
        for dep in dependencies:
            # 这里可以实现更复杂的依赖检查
            pass
        return True

    def get_installed_plugins(self) -> Dict[str, Dict[str, Any]]:
        """获取已安装的插件"""
        return self.installed_plugins

    def get_available_plugins(self) -> Dict[str, Dict[str, Any]]:
        """获取可用插件"""
        return self.available_plugins

    def load_plugin_module(self, plugin_id: str) -> Optional[Any]:
        """加载插件模块"""
        if plugin_id not in self.installed_plugins:
            return None

        try:
            plugin_info = self.installed_plugins[plugin_id]
            plugin_path = plugin_info.get('path', f"plugins/{plugin_id}")

            # 添加插件路径到Python路径
            import sys
            if plugin_path not in sys.path:
                sys.path.insert(0, plugin_path)

            # 动态导入插件模块
            module = __import__(plugin_id)
            return module

        except Exception as e:
            print(f"Failed to load plugin module {plugin_id}: {e}")
            return None

    def get_plugin_capabilities(self, plugin_id: str) -> List[str]:
        """获取插件能力"""
        module = self.load_plugin_module(plugin_id)
        if module and hasattr(module, 'get_available_sources'):
            return module.get_available_sources()
        elif module and hasattr(module, 'get_available_processors'):
            return module.get_available_processors()
        elif module and hasattr(module, 'get_available_handlers'):
            return module.get_available_handlers()
        return []

    async def execute_plugin_function(self, plugin_id: str, function_name: str, *args, **kwargs):
        """执行插件函数"""
        module = self.load_plugin_module(plugin_id)
        if module and hasattr(module, function_name):
            func = getattr(module, function_name)
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return None

    def update_plugin_registry(self):
        """更新插件注册表"""
        discovered = self.discover_plugins()
        for plugin in discovered:
            plugin_id = plugin['id']
            if plugin_id not in self.available_plugins:
                self.available_plugins[plugin_id] = plugin

        self.save_registry()
# 全局插件市场实例
plugin_market = PluginMarket()
