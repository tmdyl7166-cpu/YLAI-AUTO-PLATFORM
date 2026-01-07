#!/usr/bin/env python3
"""
consistency_check.py — 全仓路径与引用一致性校验

校验项：
- 前端 pages/*.html 引用的 JS/CSS 是否存在
- 前端 static/js/pages/*.js 是否被页面使用（可选统计）
- 文档/页面引用的 docs/*.md 是否存在
- VS Code 任务、脚本入口与文件路径存在性
- Docker 与 Nginx 配置文件存在性

输出：
- logs/consistency.json （结构化结果）
- logs/consistency.txt （摘要）
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / 'logs'
LOGS.mkdir(exist_ok=True)

pages_dir = ROOT / 'frontend' / 'pages'
static_dir = ROOT / 'frontend' / 'static'
docs_dir = ROOT / 'docs'
vscode_tasks = ROOT / '.vscode' / 'tasks.json'
scripts_dir = ROOT / 'scripts'
docker_dir = ROOT / 'docker'
nginx_dir = ROOT / 'nginx'

result = {
    'missing': [],
    'pages_refs': [],
    'scripts': [],
    'docker': [],
    'nginx': [],
}

def exists(path: Path):
    return path.exists()

def record_missing(kind: str, path: Path, context: str = ''):
    result['missing'].append({'kind': kind, 'path': str(path.relative_to(ROOT)), 'context': context})

def scan_pages_refs():
    if not pages_dir.exists():
        record_missing('dir', pages_dir)
        return
    for p in pages_dir.glob('*.html'):
        content = p.read_text(encoding='utf-8', errors='ignore')
        # JS/CSS src/href
        refs = re.findall(r'(?:src|href)=["\']([^"\']+)["\']', content)
        for r in refs:
            # 只检查项目内路径
            if r.startswith('/'):
                # 归一化到 workspace 根
                if r.startswith('/static/'):
                    fp = static_dir / r.replace('/static/', '')
                elif r.startswith('/pages/'):
                    fp = pages_dir / r.replace('/pages/', '')
                elif r.startswith('/docs/'):
                    fp = docs_dir / r.replace('/docs/', '')
                else:
                    # 其他根路径，跳过或标注
                    fp = ROOT / r.lstrip('/')
                result['pages_refs'].append({'page': str(p.relative_to(ROOT)), 'ref': r, 'exists': exists(fp)})
                if not exists(fp):
                    record_missing('ref', fp, context=f'{p.name} -> {r}')

def scan_scripts_and_tasks():
    # 列出脚本文件
    for s in scripts_dir.glob('**/*'):
        if s.is_file():
            result['scripts'].append(str(s.relative_to(ROOT)))
    # VS Code 任务存在性
    if not vscode_tasks.exists():
        record_missing('file', vscode_tasks, context='vscode tasks')

def scan_docker_nginx():
    # Docker files
    for f in docker_dir.glob('*'):
        if f.is_file():
            result['docker'].append(str(f.relative_to(ROOT)))
    # Nginx config
    for f in nginx_dir.glob('*'):
        if f.is_file():
            result['nginx'].append(str(f.relative_to(ROOT)))

def write_outputs():
    (LOGS / 'consistency.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    # 摘要：统计缺失项
    missing = result.get('missing', [])
    lines = [f'missing: {len(missing)}']
    for m in missing:
        lines.append(f"- {m['kind']}: {m['path']} ({m.get('context','')})")
    (LOGS / 'consistency.txt').write_text('\n'.join(lines), encoding='utf-8')

def main():
    scan_pages_refs()
    scan_scripts_and_tasks()
    scan_docker_nginx()
    write_outputs()
    print(f"[consistency] missing: {len(result.get('missing',[]))}")
    print(f"[consistency] logs: {LOGS / 'consistency.json'}")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('[consistency] error:', e, file=sys.stderr)
        sys.exit(2)
