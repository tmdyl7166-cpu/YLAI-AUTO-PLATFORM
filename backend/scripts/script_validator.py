#!/usr/bin/env python3
"""
脚本注册验证器
用于验证所有脚本的注册完整性和健康状态
"""

import os
import sys
import json
import importlib
import inspect
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.core.base import BaseScript

logger = logging.getLogger(__name__)

class ScriptRegistryValidator:
    """脚本注册验证器"""

    def __init__(self):
        self.scripts_dir = Path(__file__).parent
        self.registry_file = project_root / "function_registry.json"
        self.yl_rules_file = project_root / "YL-copilot-rules.json"
        self.issues = []
        self.valid_scripts = []

    def scan_scripts(self) -> List[Dict[str, Any]]:
        """扫描所有脚本文件"""
        scripts = []

        # 扫描scripts目录
        for file_path in self.scripts_dir.rglob("*.py"):
            if file_path.name.startswith("__"):
                continue

            try:
                # 转换为模块路径
                relative_path = file_path.relative_to(project_root)
                module_path = str(relative_path).replace("/", ".").replace("\\", ".").replace(".py", "")

                # 动态导入模块
                module = importlib.import_module(module_path)

                # 查找脚本类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and
                        issubclass(obj, BaseScript) and
                        obj != BaseScript):

                        scripts.append({
                            "name": obj.name,
                            "class_name": name,
                            "module": module_path,
                            "file_path": str(file_path),
                            "class": obj
                        })
                        break

            except Exception as e:
                self.issues.append({
                    "type": "import_error",
                    "file": str(file_path),
                    "error": str(e)
                })

        return scripts

    def validate_script_class(self, script_info: Dict[str, Any]) -> Dict[str, Any]:
        """验证脚本类"""
        issues = []
        script_class = script_info["class"]

        # 检查必需属性
        required_attrs = ["name", "description", "version"]
        for attr in required_attrs:
            if not hasattr(script_class, attr):
                issues.append(f"缺少必需属性: {attr}")

        # 检查run方法
        if not hasattr(script_class, "run"):
            issues.append("缺少run方法")
        else:
            run_method = getattr(script_class, "run")
            if not inspect.iscoroutinefunction(run_method):
                issues.append("run方法必须是async函数")

        # 检查生命周期方法
        lifecycle_methods = ["pre_run", "post_run", "on_error", "cleanup"]
        for method in lifecycle_methods:
            if hasattr(script_class, method):
                method_obj = getattr(script_class, method)
                if not inspect.iscoroutinefunction(method_obj):
                    issues.append(f"{method}方法必须是async函数")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

    def load_registry(self) -> Optional[Dict[str, Any]]:
        """加载注册表"""
        # 优先使用独立的 function_registry.json，如果不存在则从 YL-copilot-rules.json 中读取 functionRegistry
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.issues.append({
                    "type": "registry_load_error",
                    "error": f"无法加载注册表 {self.registry_file}: {e}"
                })
                return None

        # 尝试从 YL-copilot-rules.json 中加载
        if self.yl_rules_file.exists():
            try:
                with open(self.yl_rules_file, 'r', encoding='utf-8') as f:
                    yl = json.load(f)
                fr = yl.get("functionRegistry") or yl.get("functionRegistry", None)
                if fr:
                    return fr
                else:
                    self.issues.append({
                        "type": "missing_registry_in_yl",
                        "error": "YL-copilot-rules.json 中未包含 functionRegistry 字段"
                    })
                    return None
            except Exception as e:
                self.issues.append({
                    "type": "registry_load_error",
                    "error": f"无法从 YL-copilot-rules.json 加载注册表: {e}"
                })
                return None

        self.issues.append({
            "type": "missing_registry",
            "error": "function_registry.json 和 YL-copilot-rules.json 均不存在"
        })
        return None

    def validate_registry_consistency(self, scripts: List[Dict[str, Any]], registry: Dict[str, Any]) -> None:
        """验证注册表一致性"""
        registry_scripts = set(registry.get("functions", {}).keys())
        found_scripts = set(s["name"] for s in scripts)

        # 检查未注册的脚本
        unregistered = found_scripts - registry_scripts
        if unregistered:
            self.issues.append({
                "type": "unregistered_scripts",
                "scripts": list(unregistered)
            })

        # 检查已注册但不存在的脚本
        missing = registry_scripts - found_scripts
        if missing:
            self.issues.append({
                "type": "missing_scripts",
                "scripts": list(missing)
            })

    def generate_registry(self, scripts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成注册表"""
        registry = {
            "version": "1.0.0",
            "description": "YLAI脚本注册表",
            "functions": {}
        }

        for script in scripts:
            script_class = script["class"]
            registry["functions"][script_class.name] = {
                "name": script_class.name,
                "description": getattr(script_class, "description", "无描述"),
                "version": getattr(script_class, "version", "1.0.0"),
                "module": script["module"],
                "class": script["class_name"],
                "timeout": getattr(script_class, "timeout", 30),
                "category": self._infer_category(script["file_path"])
            }

        return registry

    def _infer_category(self, file_path: str) -> str:
        """推断脚本类别"""
        path_parts = Path(file_path).parts
        if "ai" in path_parts:
            return "ai"
        elif "spider" in path_parts:
            return "spider"
        elif "process" in path_parts:
            return "process"
        else:
            return "general"

    def save_registry(self, registry: Dict[str, Any]) -> None:
        """保存注册表"""
        try:
            # 确保functions键存在
            if "functions" not in registry:
                registry["functions"] = {}

            # 如果存在独立注册表文件，写入该文件；否则将其写入到 YL-copilot-rules.json 的 functionRegistry 字段
            if self.registry_file.exists() or not self.yl_rules_file.exists():
                with open(self.registry_file, 'w', encoding='utf-8') as f:
                    json.dump(registry, f, ensure_ascii=False, indent=2)
                logger.info(f"注册表已保存到: {self.registry_file}")
            else:
                # 更新 YL-copilot-rules.json 中的 functionRegistry 字段
                with open(self.yl_rules_file, 'r', encoding='utf-8') as f:
                    yl = json.load(f)
                yl["functionRegistry"] = registry
                with open(self.yl_rules_file, 'w', encoding='utf-8') as f:
                    json.dump(yl, f, ensure_ascii=False, indent=2)
                logger.info(f"注册表已保存到: {self.yl_rules_file}#functionRegistry")
        except Exception as e:
            self.issues.append({
                "type": "save_error",
                "error": f"保存注册表失败: {e}"
            })

    def run_validation(self) -> Dict[str, Any]:
        """运行完整验证"""
        logger.info("开始脚本注册验证...")

        # 扫描脚本
        scripts = self.scan_scripts()
        logger.info(f"发现 {len(scripts)} 个脚本")

        # 验证脚本类
        valid_scripts = []
        for script in scripts:
            validation = self.validate_script_class(script)
            if validation["valid"]:
                valid_scripts.append(script)
            else:
                self.issues.extend([{
                    "type": "script_validation_error",
                    "script": script["name"],
                    "issues": validation["issues"]
                } for issue in validation["issues"]])

        # 加载现有注册表
        registry = self.load_registry()

        if registry:
            # 验证一致性
            self.validate_registry_consistency(valid_scripts, registry)
        else:
            # 生成新注册表
            registry = self.generate_registry(valid_scripts)
            self.save_registry(registry)

        # 生成报告
        report = {
            "total_scripts": len(scripts),
            "valid_scripts": len(valid_scripts),
            "issues": self.issues,
            "registry_updated": registry is not None
        }

        return report

    def print_report(self, report: Dict[str, Any]) -> None:
        """打印验证报告"""
        print("=== 脚本注册验证报告 ===")
        print(f"总脚本数: {report['total_scripts']}")
        print(f"有效脚本数: {report['valid_scripts']}")
        print(f"问题数量: {len(report['issues'])}")

        if report['issues']:
            print("\n=== 发现的问题 ===")
            for i, issue in enumerate(report['issues'], 1):
                print(f"{i}. [{issue['type']}] {issue.get('error', '')}")
                if 'scripts' in issue:
                    print(f"   涉及脚本: {', '.join(issue['scripts'])}")
                if 'script' in issue:
                    print(f"   脚本: {issue['script']}")
                if 'issues' in issue:
                    for sub_issue in issue['issues']:
                        print(f"   - {sub_issue}")

        if report['registry_updated']:
            print("\n✅ 注册表已更新")
        else:
            print("\n❌ 注册表更新失败")

def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)

    validator = ScriptRegistryValidator()
    report = validator.run_validation()
    validator.print_report(report)

    # 返回退出码
    return 0 if len(report['issues']) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())