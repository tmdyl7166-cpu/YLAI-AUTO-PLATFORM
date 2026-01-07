import requests
from pathlib import Path
from .config import OLLAMA_URL, OLLAMA_MODEL


def _llm_generate(prompt: str) -> str:
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response") or data.get("result") or ""
    except Exception as e:
        return f"[LLM-ERROR] {e}"


def generate_optimization_suggestions(file_path: Path, unfinished_items):
    suggestions = []
    context_lines = "\n".join([f"Line {it['line']}: {it['content']}" for it in unfinished_items])
    prompt = (
        "你是代码优化助手。请基于以下未完成的代码行，给出简洁的修复方案与补全建议，"
        "突出要点（异常处理、路径、类型提示），尽量贴近原风格。\n"
        f"文件: {file_path.name}\n"
        f"未完成行:\n{context_lines}\n"
        "请输出每一项的建议，用简要中文说明。"
    )
    llm_text = _llm_generate(prompt)
    for item in unfinished_items:
        suggestions.append({
            "line": item["line"],
            "suggestion": f"{llm_text[:300]}"
        })
    return suggestions


def apply_suggestions(text, suggestions):
    lines = text.splitlines()
    for sug in suggestions:
        idx = sug["line"] - 1
        if 0 <= idx < len(lines):
            original = lines[idx]
            insertion = None
            lower = original.lower()
            if any(k in lower for k in ["todo", "fixme", "pass", "notimplemented"]):
                insertion = "# [AUTO OPTIMIZED] 占位实现已插入"
            elif lower.strip().startswith("except:"):
                insertion = "# [AUTO OPTIMIZED] 请指定异常类型，如: except Exception as e:"
            elif any(k in original for k in ["./", "../", "C:\\"]):
                insertion = "# [AUTO OPTIMIZED] 建议使用 pathlib.Path 组合路径"
            summary = sug.get("suggestion", "建议优化此行")[:200]
            lines[idx] = f"{original}\n{insertion or '# [AUTO OPTIMIZED] 建议已记录'}\n# [SUGGEST] {summary}"
    return "\n".join(lines)
