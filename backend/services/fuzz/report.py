from typing import List, Dict, Any

def to_markdown(results: List[Dict[str, Any]]) -> str:
    lines = ["# Fuzz 报告", "", "|状态|码|耗时(ms)|长度|关键词|", "|---|---:|---:|---:|---|"]
    for r in results:
        ok = '✅' if r.get('ok') else '❌'
        lines.append(f"|{ok}|{r.get('status')}|{int(r.get('elapsed_ms',0))}|{int(r.get('length',0))}|{','.join(r.get('keywords',[]))}|")
    lines.append("\n## 详情")
    for i, r in enumerate(results, 1):
        lines.append(f"\n### 用例 {i}")
        lines.append("```")
        lines.append(str(r))
        lines.append("```")
    return "\n".join(lines)
