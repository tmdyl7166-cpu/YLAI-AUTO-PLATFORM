from pathlib import Path
import shutil
from .config import BACKUP_DIR

BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def backup_file(file_path: Path):
    backup_path = BACKUP_DIR / f"{file_path.name}.bak"
    shutil.copy(file_path, backup_path)
    return backup_path


def deploy_optimization(file_path: Path, optimized_text: str):
    backup_file(file_path)
    file_path.write_text(optimized_text, encoding="utf-8")


def rollback(file_path: Path):
    bak = BACKUP_DIR / f"{file_path.name}.bak"
    if bak.exists():
        shutil.copy(bak, file_path)
        return True
    return False
