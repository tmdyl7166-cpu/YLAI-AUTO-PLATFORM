#!/usr/bin/env python3
import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / 'docs'
FRONTEND_DIR = ROOT / 'frontend'
BACKEND_DIR = ROOT / 'backend'
AI_DOCKER_DIR = ROOT / 'ai-docker'
PAGES_DATA_DIR = FRONTEND_DIR / 'pages' / 'data'
REPORT = DOCS_DIR / 'AUDIT_REPORT.md'

# Files we expect docs to mention
EXPECT_LIST = [
    '.env.dev',
    'ai-docker/.env',
    '.gitignore',
    'frontend/.devcontainer/devcontainer.json',
    '.devcontainer/devcontainer.json',
    'frontend/pages/data/module-status.json',
    'frontend/pages/data/module-routes-status.json',
    'frontend/pages/data/crawler_status.json',
    'frontend/pages/data/stats.json',
    'frontend/static/js/core/theme.js',
    'logs/',
    'function_registry.json',
    'modules_policy.json',
    'backend/scripts/ai/rules.json',
    'ai-docker/rules/output_format.json',
    '核心指向.json',
]

def file_exists(rel):
    p = ROOT / rel
    return p.exists()

def collect_scripts():
    scripts = []
    for d in [ROOT/'scripts', BACKEND_DIR, AI_DOCKER_DIR, FRONTEND_DIR/'static'/'js'/'pages']:
        if d.exists():
            for path in d.rglob('*.py'):
                scripts.append(path.relative_to(ROOT).as_posix())
            # include JS pages
            for path in d.rglob('*.js'):
                scripts.append(path.relative_to(ROOT).as_posix())
    return sorted(set(scripts))

def collect_pages():
    pages = []
    pdir = FRONTEND_DIR/'pages'
    if pdir.exists():
        for path in pdir.rglob('*.html'):
            pages.append(path.relative_to(ROOT).as_posix())
        for path in pdir.rglob('*.md'):
            pages.append(path.relative_to(ROOT).as_posix())
    return sorted(pages)

def collect_env_json_tmp():
    items = []
    for path in ROOT.rglob('*'):
        name = path.name
        if name.endswith('.env') or name.endswith('.json') or name.endswith('.tmp'):
            items.append(path.relative_to(ROOT).as_posix())
    return sorted(items)

def collect_mismatch(expect_list):
    missing = [e for e in expect_list if not file_exists(e)]
    return missing

def main():
    scripts = collect_scripts()
    pages = collect_pages()
    env_json_tmp = collect_env_json_tmp()
    missing = collect_mismatch(EXPECT_LIST)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open('w', encoding='utf-8') as f:
        f.write('# 文档与代码一致性审计报告\n\n')
        f.write('项目根: %s\n\n' % ROOT)
        f.write('## 期望存在的关键文件（来自说明文档）\n')
        for e in EXPECT_LIST:
            status = '✓' if file_exists(e) else '✗'
            f.write(f'- {e} {status}\n')
        f.write('\n## 缺失项\n')
        if missing:
            for m in missing:
                f.write(f'- {m}\n')
        else:
            f.write('- 无\n')
        f.write('\n## 发现的脚本（.py/.js）\n')
        for s in scripts:
            f.write(f'- {s}\n')
        f.write('\n## 前端页面与文档\n')
        for p in pages:
            f.write(f'- {p}\n')
        f.write('\n## 所有 .env/.json/.tmp 文件\n')
        for i in env_json_tmp:
            f.write(f'- {i}\n')
        f.write('\n---\n')
        f.write('提示：如需将“统一接口映射表.md”自动生成 JSON（module-status.json、module-routes-status.json），建议新增 scripts/gen_api_map_json.py 并在CI执行。\n')
    print(f'Wrote report to {REPORT}')

if __name__ == '__main__':
    main()
