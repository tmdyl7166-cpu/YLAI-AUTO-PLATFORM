import os
import importlib
import pkgutil
from .logger import logger

class ScriptRegistry:
    def __init__(self):
        self.scripts = {}

    def register(self, name: str):
        def decorator(cls):
            if name in self.scripts:
                raise ValueError(f"脚本 '{name}' 已存在")
            self.scripts[name] = cls()
            logger.info(f"📝 注册脚本: {name} -> {cls.__name__}")
            return cls
        return decorator

    def get(self, name: str):
        return self.scripts.get(name)

    def list_all(self):
        return list(self.scripts.keys())

    def auto_register(self, package: str):
        """
        以包名递归扫描模块进行自动注册。
        兼容 "backend.scripts" 这类包名，避免将其误当作磁盘路径。
        """
        logger.info(f"🔍 开始扫描脚本目录: {package}")
        try:
            pkg = importlib.import_module(package)
            paths = getattr(pkg, '__path__', [])  # 命名空间包可能包含多个路径
        except Exception as e:
            logger.warning(f"⚠️ 包不可导入: {package} | {e}")
            return

        for _, mod_name, ispkg in pkgutil.walk_packages(paths, package + "."):
            # 跳过子包与私有模块
            if ispkg or mod_name.split('.')[-1].startswith('_'):
                continue
            try:
                importlib.import_module(mod_name)
                logger.info(f"✅ 加载模块: {mod_name}")
            except Exception as e:
                logger.error(f"❌ 加载失败: {mod_name} | 错误: {e}")

registry = ScriptRegistry()
