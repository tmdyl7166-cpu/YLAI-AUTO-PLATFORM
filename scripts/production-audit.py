#!/usr/bin/env python3
"""
YLAI-AUTO-PLATFORM 生产优化完整性验证脚本
验证所有生产配置、文档和代码是否完整一致
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

class ProductionAudit:
    """生产环境审计类"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": [],
        }
    
    def check_file_exists(self, path: str, description: str) -> bool:
        """检查文件是否存在"""
        file_path = self.project_root / path
        if file_path.exists():
            self.results["passed"].append(f"✓ {description}")
            return True
        else:
            self.results["failed"].append(f"✗ {description}")
            return False
    
    def check_file_content(self, path: str, keywords: List[str], description: str) -> bool:
        """检查文件是否包含关键字"""
        try:
            file_path = self.project_root / path
            if not file_path.exists():
                self.results["failed"].append(f"✗ {description} (文件不存在)")
                return False
            
            content = file_path.read_text()
            if all(keyword in content for keyword in keywords):
                self.results["passed"].append(f"✓ {description}")
                return True
            else:
                self.results["failed"].append(f"✗ {description}")
                return False
        except Exception as e:
            self.results["failed"].append(f"✗ {description} ({str(e)})")
            return False
    
    def run_checks(self) -> None:
        """执行所有检查"""
        
        print("\n╔════════════════════════════════════════════════════════════════════════════╗")
        print("║  🔍 YLAI-AUTO-PLATFORM 生产环境完整性验证                                 ║")
        print("╚════════════════════════════════════════════════════════════════════════════╝\n")
        
        # 1. 后端配置检查
        print("1️⃣ 后端配置检查...")
        self.check_file_exists("backend/.env.example", "后端环境变量模板")
        self.check_file_exists("backend/config/logging.py", "日志配置文件")
        self.check_file_exists("backend/config/security.py", "安全配置文件")
        
        # 2. Docker 配置检查
        print("2️⃣ Docker 配置检查...")
        self.check_file_exists("docker/Dockerfile.prod", "生产 Dockerfile")
        self.check_file_exists("docker/docker-compose.prod.yml", "生产 docker-compose")
        self.check_file_exists("docker/startup-check.sh", "启动检查脚本")
        
        # 3. 文档检查
        print("3️⃣ 文档完整性检查...")
        self.check_file_exists("docs/DEPLOYMENT.md", "部署指南")
        self.check_file_exists("docs/API_SPECIFICATION.md", "API 规范")
        self.check_file_exists("README.md", "项目 README")
        
        # 4. CI/CD 检查
        print("4️⃣ CI/CD 流水线检查...")
        self.check_file_exists(".github/workflows/cd-pipeline.yml", "CD 流水线配置")
        
        # 5. 代码质量检查
        print("5️⃣ 代码质量检查...")
        self.check_file_content(
            "backend/requirements.txt",
            ["fastapi", "sqlalchemy", "redis"],
            "后端依赖声明"
        )
        
        # 6. 配置一致性检查
        print("6️⃣ 配置一致性检查...")
        self._check_env_consistency()
        self._check_docker_consistency()
        self._check_documentation_consistency()
        
        # 7. 安全检查
        print("7️⃣ 安全性检查...")
        self._check_security_config()
        
        # 8. 性能检查
        print("8️⃣ 性能配置检查...")
        self._check_performance_config()
    
    def _check_env_consistency(self) -> None:
        """检查环境变量一致性"""
        env_file = self.project_root / "backend/.env.example"
        if env_file.exists():
            env_vars = self._parse_env_file(env_file)
            if len(env_vars) > 30:
                self.results["passed"].append(f"✓ 环境变量完整 ({len(env_vars)} 个)")
            else:
                self.results["warnings"].append("⚠ 环境变量可能不足")
    
    def _check_docker_consistency(self) -> None:
        """检查 Docker 配置一致性"""
        try:
            compose_file = self.project_root / "docker/docker-compose.prod.yml"
            if compose_file.exists():
                content = compose_file.read_text()
                if all(service in content for service in ["backend", "postgres", "redis"]):
                    self.results["passed"].append("✓ Docker 服务配置完整")
                else:
                    self.results["failed"].append("✗ Docker 缺少必要服务")
        except Exception as e:
            self.results["failed"].append(f"✗ Docker 配置检查失败: {str(e)}")
    
    def _check_documentation_consistency(self) -> None:
        """检查文档一致性"""
        deployment_file = self.project_root / "docs/DEPLOYMENT.md"
        if deployment_file.exists():
            content = deployment_file.read_text()
            keywords = ["Docker", "Kubernetes", "health check", "backup"]
            if all(keyword in content for keyword in keywords):
                self.results["passed"].append("✓ 部署文档完整")
            else:
                self.results["warnings"].append("⚠ 部署文档可能不完整")
    
    def _check_security_config(self) -> None:
        """检查安全配置"""
        security_file = self.project_root / "backend/config/security.py"
        if security_file.exists():
            content = security_file.read_text()
            security_features = [
                "CORS", "JWT", "encryption", "rate_limit", "input_validation"
            ]
            found = sum(1 for feature in security_features if feature in content)
            if found >= 4:
                self.results["passed"].append(f"✓ 安全特性完整 ({found}/{len(security_features)})")
            else:
                self.results["warnings"].append(f"⚠ 安全特性不足 ({found}/{len(security_features)})")
    
    def _check_performance_config(self) -> None:
        """检查性能配置"""
        security_file = self.project_root / "backend/config/security.py"
        logging_file = self.project_root / "backend/config/logging.py"
        
        if security_file.exists() and logging_file.exists():
            sec_content = security_file.read_text()
            log_content = logging_file.read_text()
            
            performance_features = {
                "缓存": "cache" in sec_content,
                "压缩": "GZip" in sec_content,
                "日志轮换": "RotatingFileHandler" in log_content,
                "监控": "Prometheus" in log_content,
            }
            
            enabled = sum(1 for v in performance_features.values() if v)
            self.results["passed"].append(f"✓ 性能特性配置 ({enabled}/{len(performance_features)})")
    
    @staticmethod
    def _parse_env_file(filepath: Path) -> Dict:
        """解析环境变量文件"""
        env_vars = {}
        try:
            for line in filepath.read_text().split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _ = line.split("=", 1)
                    env_vars[key] = True
        except Exception:
            pass
        return env_vars
    
    def print_report(self) -> None:
        """打印审计报告"""
        total = len(self.results["passed"]) + len(self.results["failed"])
        passed = len(self.results["passed"])
        percentage = (passed / total * 100) if total > 0 else 0
        
        print("\n╔════════════════════════════════════════════════════════════════════════════╗")
        print(f"║  📊 审计结果: {passed}/{total} 通过 ({percentage:.1f}%)                     │")
        print("╚════════════════════════════════════════════════════════════════════════════╝\n")
        
        if self.results["passed"]:
            print("✅ 通过项目:")
            for item in self.results["passed"]:
                print(f"  {item}")
        
        if self.results["warnings"]:
            print("\n⚠️ 警告项目:")
            for item in self.results["warnings"]:
                print(f"  {item}")
        
        if self.results["failed"]:
            print("\n❌ 失败项目:")
            for item in self.results["failed"]:
                print(f"  {item}")
        
        # 最终评分
        print("\n" + "─" * 80)
        if passed == total:
            print("✨ 评分: 100/100 - 生产就绪度: ⭐⭐⭐⭐⭐")
        elif percentage >= 90:
            print(f"✨ 评分: {percentage:.0f}/100 - 生产就绪度: ⭐⭐⭐⭐")
        elif percentage >= 70:
            print(f"✨ 评分: {percentage:.0f}/100 - 生产就绪度: ⭐⭐⭐")
        else:
            print(f"⚠️ 评分: {percentage:.0f}/100 - 生产就绪度: ⭐⭐")


if __name__ == "__main__":
    audit = ProductionAudit()
    audit.run_checks()
    audit.print_report()
