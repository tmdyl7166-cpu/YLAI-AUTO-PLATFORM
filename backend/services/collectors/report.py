from typing import Dict, Any, List

def to_markdown(items: List[Dict[str, Any]]) -> str:
    lines = ["# Collectors 报告", "", "|源|状态|码|摘要|", "|---|---|---:|---|"]
    for it in items:
        src = it.get('source')
        res = it.get('result', {})
        ok = '✅' if res.get('ok') else '❌'
        status = res.get('status', '-')
        summary = str(res.get('data', ''))[:120]
        lines.append(f"|{src}|{ok}|{status}|{summary}|")
    lines.append("\n## 详情")
    for i, it in enumerate(items, 1):
        lines.append(f"\n### 项 {i}")
        lines.append("```")
        lines.append(str(it))
        lines.append("```")
    return "\n".join(lines)
