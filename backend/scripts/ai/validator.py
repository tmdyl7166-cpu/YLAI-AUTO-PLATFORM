import subprocess
from pathlib import Path


def run_static_analysis(file_path: Path):
    result = subprocess.run(["flake8", str(file_path)], capture_output=True, text=True)
    ok = result.returncode == 0
    return ok, result.stdout.strip()


def run_tests(test_dir: Path):
    result = subprocess.run(["pytest", str(test_dir)], capture_output=True, text=True)
    ok = result.returncode == 0
    return ok, result.stdout.strip()


def run_mypy(target: Path):
    result = subprocess.run(["mypy", str(target)], capture_output=True, text=True)
    ok = result.returncode == 0
    return ok, result.stdout.strip()
