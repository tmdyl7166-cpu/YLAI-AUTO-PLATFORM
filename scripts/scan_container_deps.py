#!/usr/bin/env python3
import os
import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKER_DIR = ROOT / "docker"
TARGETS = [
    DOCKER_DIR / "api.Dockerfile",
    DOCKER_DIR / "nginx.Dockerfile",
    DOCKER_DIR / "Dockerfile.ai-app",
    ROOT / "docker-compose.yml",
    DOCKER_DIR / "docker-compose.yml",
    ROOT / "frontend" / "docker-compose.yml",
]
EXTRA_DEPS = {
    "backend_requirements": ROOT / "backend" / "requirements.txt",
    "root_requirements": ROOT / "requirements.txt",
    "ai_requirements": ROOT / "ai-docker" / "requirements.txt",
    "frontend_package": ROOT / "frontend" / "package.json",
}

def read_text(p: Path):
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def extract_pkg_installs(dockerfile_text: str):
    installs = {
        "apt": [],
        "pip": [],
        "npm": [],
        "apk": [],
        "other": [],
    }
    for line in dockerfile_text.splitlines():
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        # apt-get install
        m = re.search(r"apt-get\s+install\s+-y\s+(.*)", s)
        if m:
            pkgs = re.split(r"\s+", m.group(1))
            installs["apt"].extend([p for p in pkgs if p and p != '&&'])
        # apk add
        m = re.search(r"apk\s+add\s+--no-cache\s+(.*)", s)
        if m:
            pkgs = re.split(r"\s+", m.group(1))
            installs["apk"].extend([p for p in pkgs if p and p != '&&'])
        # pip install -r
        m = re.search(r"pip\s+install\s+-r\s+([^\s]+)", s)
        if m:
            installs["pip"].append({"requirements": m.group(1)})
        # pip install package(s)
        m = re.search(r"pip\s+install\s+(-U\s+)?(.+)$", s)
        if m and "-r" not in s:
            pkgs = [p for p in re.split(r"\s+", m.group(2)) if p and p != '&&']
            installs["pip"].extend(pkgs)
        # npm install
        if s.startswith("npm install"):
            installs["npm"].append(s)
        # fallback other RUN lines
        if s.startswith("RUN") and not any(k in s for k in ["apt-get install", "apk add", "pip install", "npm install"]):
            installs["other"].append(s)
    return installs

def extract_compose_builds(compose_text: str):
    # naive parse: scan service blocks for build: dockerfile/context
    services = {}
    current_service = None
    for line in compose_text.splitlines():
        s = line.rstrip()
        if re.match(r"^[\w-]+:\s*$", s.strip()) and not s.strip().startswith("version") and not s.strip().startswith("services"):
            current_service = s.strip().split(':')[0]
            services.setdefault(current_service, {})
        if current_service:
            m = re.search(r"dockerfile:\s*(.+)$", s)
            if m:
                services[current_service]["dockerfile"] = m.group(1).strip()
            m = re.search(r"context:\s*(.+)$", s)
            if m:
                services[current_service]["context"] = m.group(1).strip()
    return services

def main():
    matrix = {"dockerfiles": {}, "compose": {}, "files": {}, "conflicts": {}}
    for p in TARGETS:
        if not p.exists():
            continue
        txt = read_text(p)
        if p.suffix.lower() in (".yml", ".yaml"):
            matrix["compose"][str(p.relative_to(ROOT))] = extract_compose_builds(txt)
        else:
            matrix["dockerfiles"][str(p.relative_to(ROOT))] = extract_pkg_installs(txt)
    # extras: parse requirements.txt and package.json
    files_summary = {}
    # requirements.txt files
    for key in ("backend_requirements", "root_requirements", "ai_requirements"):
        p = EXTRA_DEPS[key]
        pkgs = []
        if p.exists():
            for line in read_text(p).splitlines():
                s = line.strip()
                if not s or s.startswith('#'):
                    continue
                pkgs.append(s)
        files_summary[key] = {"path": str(p.relative_to(ROOT)) if p.exists() else None, "packages": pkgs}
    # frontend package.json
    p_pkg = EXTRA_DEPS["frontend_package"]
    pkg_info = {"path": str(p_pkg.relative_to(ROOT)) if p_pkg.exists() else None, "dependencies": {}, "devDependencies": {}}
    if p_pkg.exists():
        try:
            import json as _json
            data = _json.loads(read_text(p_pkg) or "{}")
            pkg_info["dependencies"] = data.get("dependencies", {}) or {}
            pkg_info["devDependencies"] = data.get("devDependencies", {}) or {}
        except Exception:
            pass
    files_summary["frontend_package"] = pkg_info
    matrix["files"] = files_summary
    # version conflict detection across requirements & package.json
    # collect versions per name
    versions = {}
    # requirements
    for key in ("backend_requirements", "root_requirements", "ai_requirements"):
        info = files_summary.get(key, {})
        for pkg in info.get("packages", []):
            name = pkg.split("==")[0]
            ver = None
            if "==" in pkg:
                ver = pkg.split("==", 1)[1]
            versions.setdefault(name, set()).add(ver or "(unspecified)")
    # package.json dependencies
    for depmap_key in ("dependencies", "devDependencies"):
        for name, ver in files_summary.get("frontend_package", {}).get(depmap_key, {}).items():
            versions.setdefault(name, set()).add(ver or "(unspecified)")
    conflicts = {name: sorted(list(vs)) for name, vs in versions.items() if len(vs) > 1}
    matrix["conflicts"] = conflicts
    print(json.dumps(matrix, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
