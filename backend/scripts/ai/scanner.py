from pathlib import Path


def scan_all_files(root: Path):
    files = []
    for p in root.rglob("*"):
        if p.is_file():
            files.append(p)
    return files
