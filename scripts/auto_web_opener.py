#!/usr/bin/env python3
"""
自动网页打开和热重载监控脚本
确保所有网页都能正常访问，清理缓存，防止重复打开
"""

import os
import sys
import time
import subprocess
import requests
import webbrowser
import hashlib
from pathlib import Path
from typing import List, Set
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

class AutoWebOpener:
    def __init__(self):
        self.project_root = Path(__file__).parent
        # 自动检测服务地址
        self.backend_url = self._detect_backend_url()
        self.frontend_url = self._detect_frontend_url()

        # 需要打开的页面
        self.pages = [
            "index.html",
            "api-doc.html",
            "run.html",
            "monitor.html",
            "visual_pipeline.html"
        ]

        # 已打开的URL哈希集合，防止重复打开
        self.opened_urls: Set[str] = set()

        # 文件监控
        self.last_file_hashes = {}

    def _detect_backend_url(self) -> str:
        """自动检测后端服务URL"""
        # 首先尝试0.0.0.0:8001
        if self._check_service("http://0.0.0.0:8001/health"):
            return "http://0.0.0.0:8001"
        # 然后尝试127.0.0.1:8001
        if self._check_service("http://127.0.0.1:8001/health"):
            return "http://127.0.0.1:8001"
        # 最后尝试localhost:8001
        if self._check_service("http://localhost:8001/health"):
            return "http://localhost:8001"
        return "http://127.0.0.1:8001"  # 默认值

    def _detect_frontend_url(self) -> str:
        """自动检测前端服务URL"""
        # 首先尝试0.0.0.0:3001
        if self._check_service("http://0.0.0.0:3001/pages/index.html"):
            return "http://0.0.0.0:3001"
        # 然后尝试127.0.0.1:3001
        if self._check_service("http://127.0.0.1:3001/pages/index.html"):
            return "http://127.0.0.1:3001"
        # 最后尝试localhost:3001
        if self._check_service("http://localhost:3001/pages/index.html"):
            return "http://localhost:3001"
        return "http://127.0.0.1:3001"  # 默认值

    def _check_service(self, url: str, timeout: int = 2) -> bool:
        """检查服务是否可访问"""
        try:
            response = requests.get(url, timeout=timeout)
            return response.status_code == 200
        except:
            return False

    def check_service_health(self, url: str, timeout: int = 5) -> bool:
        """检查服务是否健康（兼容旧代码）"""
        return self._check_service(f"{url}/health", timeout)

    def wait_for_services(self, max_wait: int = 30) -> bool:
        """等待服务启动"""
        logger.info("等待服务启动...")
        start_time = time.time()

        while time.time() - start_time < max_wait:
            # 重新检测服务地址
            backend_ok = self._check_service(f"{self.backend_url}/health")
            frontend_ok = self._check_service(f"{self.frontend_url}/pages/index.html")

            if backend_ok and frontend_ok:
                logger.info("✅ 所有服务已就绪")
                logger.info(f"后端服务: {self.backend_url}")
                logger.info(f"前端服务: {self.frontend_url}")
                return True

            logger.info(f"服务状态 - 前端: {'✅' if frontend_ok else '⏳'} ({self.frontend_url}), 后端: {'✅' if backend_ok else '⏳'} ({self.backend_url})")
            time.sleep(2)

        logger.error("❌ 服务启动超时")
        return False

    def clear_browser_cache(self):
        """清理浏览器缓存"""
        logger.info("清理浏览器缓存...")

        # 清理前端构建缓存
        frontend_dist = self.project_root / "frontend" / "dist"
        if frontend_dist.exists():
            import shutil
            shutil.rmtree(frontend_dist, ignore_errors=True)
            logger.info("已清理前端构建缓存")

        # 清理node_modules缓存
        try:
            subprocess.run([
                "rm", "-rf",
                str(self.project_root / "frontend" / "node_modules" / ".vite")
            ], check=False, capture_output=True)
        except:
            pass

    def get_file_hash(self, file_path: Path) -> str:
        """获取文件哈希"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""

    def get_files_to_monitor(self) -> List[Path]:
        """获取需要监控的文件"""
        monitor_files = []

        # 前端文件
        frontend_dirs = [
            self.project_root / "frontend" / "src",
            self.project_root / "frontend" / "pages",
            self.project_root / "frontend" / "public"
        ]

        for dir_path in frontend_dirs:
            if dir_path.exists():
                for ext in ['*.js', '*.ts', '*.vue', '*.html', '*.css']:
                    monitor_files.extend(dir_path.rglob(ext))

        # 后端文件
        backend_dirs = [
            self.project_root / "backend" / "api",
            self.project_root / "backend" / "services",
            self.project_root / "backend" / "scripts"
        ]

        for dir_path in backend_dirs:
            if dir_path.exists():
                for ext in ['*.py']:
                    monitor_files.extend(dir_path.rglob(ext))

        return monitor_files

    def check_file_changes(self) -> bool:
        """检查文件是否有变化"""
        changed = False
        current_hashes = {}

        for file_path in self.get_files_to_monitor():
            file_hash = self.get_file_hash(file_path)
            current_hashes[str(file_path)] = file_hash

            if str(file_path) not in self.last_file_hashes or \
               self.last_file_hashes[str(file_path)] != file_hash:
                changed = True
                logger.info(f"文件变化: {file_path}")

        self.last_file_hashes = current_hashes
        return changed

    def open_page_safe(self, base_url: str, page: str):
        """安全打开页面，避免重复"""
        url = f"{base_url}/pages/{page}"
        url_hash = hashlib.md5(url.encode()).hexdigest()

        if url_hash in self.opened_urls:
            logger.info(f"页面已在浏览器中: {page}")
            return

        try:
            # 使用系统默认浏览器打开
            webbrowser.open(url, new=0, autoraise=True)
            self.opened_urls.add(url_hash)
            logger.info(f"✅ 已打开页面: {page} ({url})")
            time.sleep(0.5)  # 避免打开太快
        except Exception as e:
            logger.error(f"❌ 打开页面失败 {page}: {e}")

    def open_all_pages(self):
        """打开所有需要的页面"""
        logger.info("开始打开所有网页...")

        # 清理缓存
        self.clear_browser_cache()

        # 打开前端页面
        logger.info("打开前端页面...")
        for page in self.pages:
            self.open_page_safe(self.frontend_url, page)

        # 打开后端页面（用于对比）
        logger.info("打开后端页面...")
        for page in self.pages:
            self.open_page_safe(self.backend_url, page)

        # 打开API文档
        self.open_page_safe(self.backend_url, "../docs")

        logger.info(f"✅ 共打开 {len(self.opened_urls)} 个页面")

    def monitor_and_refresh(self):
        """监控文件变化并刷新页面"""
        logger.info("开始监控文件变化...")

        while True:
            try:
                if self.check_file_changes():
                    logger.info("检测到文件变化，准备刷新页面...")
                    time.sleep(2)  # 等待文件保存完成

                    # 重新打开所有页面
                    self.opened_urls.clear()  # 清除记录，允许重新打开
                    self.open_all_pages()

                time.sleep(3)  # 检查间隔

            except KeyboardInterrupt:
                logger.info("监控已停止")
                break
            except Exception as e:
                logger.error(f"监控出错: {e}")
                time.sleep(5)

def main():
    opener = AutoWebOpener()

    # 等待服务启动
    if not opener.wait_for_services():
        sys.exit(1)

    # 打开所有页面
    opener.open_all_pages()

    # 开始监控
    try:
        opener.monitor_and_refresh()
    except KeyboardInterrupt:
        logger.info("程序已退出")

if __name__ == "__main__":
    main()