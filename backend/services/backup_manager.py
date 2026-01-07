import os
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import aiofiles
import json

class BackupManager:
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)

    async def create_backup(self, name: str, data: Dict[str, Any]) -> str:
        """创建数据备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.json"
        filepath = os.path.join(self.backup_dir, filename)

        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))

        return filepath

    async def restore_backup(self, filepath: str) -> Dict[str, Any]:
        """从备份恢复数据"""
        async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content)

    async def list_backups(self, name: str = None) -> List[str]:
        """列出备份文件"""
        files = []
        for file in os.listdir(self.backup_dir):
            if file.endswith('.json'):
                if name is None or file.startswith(name):
                    files.append(file)
        return sorted(files, reverse=True)

    async def cleanup_old_backups(self, days: int = 30):
        """清理旧备份"""
        cutoff = datetime.now() - timedelta(days=days)
        for file in os.listdir(self.backup_dir):
            if file.endswith('.json'):
                filepath = os.path.join(self.backup_dir, file)
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime < cutoff:
                    os.remove(filepath)

# 全局备份管理器
backup_manager = BackupManager()