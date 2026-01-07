from pathlib import Path
from typing import List, Dict, Any

from scanner import scan_all_files
from ai_engine import load_rules, analyze_content
from analyzer import detect_unfinished_content, analyze_dependencies
from optimizer import auto_optimize
from validator import run_static_analysis, run_tests, run_mypy
from deployer import deploy_optimization, rollback, backup_file

from config import RULE_PATH


def run_pipeline_on_file(file_path: Path, auto_fix: bool = True, auto_approve: bool = True) -> Dict[str, Any]:
    original_text = file_path.read_text(encoding="utf-8", errors="ignore")

    rule_set = load_rules(RULE_PATH)

    audit: Dict[str, Any] = {
        "file": str(file_path),
        "stages": [],
    }

    # Stage 1: Scan unfinished markers
    unfinished = detect_unfinished_content(original_text)
    audit["stages"].append({"stage": "scan", "unfinished": unfinished})

    # Stage 2: Rule-based analysis
    rule_hits = analyze_content(original_text, rule_set)
    audit["stages"].append({"stage": "analyze", "rule_hits": rule_hits})

    # Stage 3: Dependencies overview (best-effort)
    deps = analyze_dependencies(str(file_path))
    audit["stages"].append({"stage": "deps", "summary": deps})

    # Stage 4: Plan + Optimize (naive replace based on suggestions)
    # Flatten suggestions into keyword list to feed optimizer
    suggestions = []
    for hit in rule_hits:
        for kw in hit.get("keywords", []):
            suggestions.append({"keyword": kw})
    optimized_text = auto_optimize(original_text, suggestions)
    audit["stages"].append({"stage": "optimize", "changed": optimized_text != original_text})


    # Stage 5: Validate (flake8/pytest/mypy)
    health_passed = False
    if auto_fix and optimized_text != original_text:
        backup_file(file_path)
        deploy_optimization(file_path, optimized_text)
        # 自动审批或等待人工审批
        if not auto_approve:
            audit["stages"].append({"stage": "pending_approval"})
            audit["status"] = "pending_approval"
            return audit

    ok_flake8, out_flake8 = run_static_analysis(file_path)
    ok_pytest, out_pytest = run_tests(file_path.parent)
    ok_mypy, out_mypy = run_mypy(file_path.parent)
    all_ok = ok_flake8 and ok_pytest and ok_mypy
    audit["stages"].append({
        "stage": "validate",
        "flake8": {"ok": ok_flake8, "out": out_flake8},
        "pytest": {"ok": ok_pytest, "out": out_pytest},
        "mypy": {"ok": ok_mypy, "out": out_mypy},
        "all_ok": all_ok,
    })

    # Stage 6: Rollback if failed
    if auto_fix and not all_ok and optimized_text != original_text:
        rollback(file_path)
        audit["stages"].append({"stage": "rollback", "status": "done"})

    audit["status"] = (
        "optimized" if all_ok and optimized_text != original_text
        else ("skipped" if optimized_text == original_text else "rollback")
    )
    return audit


def run_pipeline_on_dirs(dirs: List[Path], max_workers: int = 4, auto_fix: bool = True) -> Dict[str, Any]:
    files: List[Path] = []
    for d in dirs:
        files.extend(scan_all_files(d))

    results: List[Dict[str, Any]] = []
    # simple sequential to keep logs deterministic; can parallelize later
    for f in files:
        try:
            results.append(run_pipeline_on_file(f, auto_fix=auto_fix))
        except Exception as e:
            results.append({"file": str(f), "status": "error", "error": str(e)})

    return {"items": results}
