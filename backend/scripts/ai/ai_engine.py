import json
from pathlib import Path

def load_rules(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "rules" not in data:
        raise ValueError("rules.json 格式错误: 顶层必须包含 'rules' 数组")
    rules = data["rules"]
    for i, r in enumerate(rules):
        if not isinstance(r, dict):
            raise ValueError(f"规则项[{i}]必须为对象")
        for key in ("name", "match", "suggest"):
            if key not in r:
                raise ValueError(f"规则项[{i}]缺少必需字段: {key}")
        if not isinstance(r["match"], list) or not all(isinstance(x, str) for x in r["match"]):
            raise ValueError(f"规则项[{i}].match 必须为字符串数组")
    return rules


def analyze_content(text: str, rules):
    results = []
    for rule in rules:
        hits = []
        for kw in rule["match"]:
            if kw in text:
                hits.append(kw)
        if hits:
            results.append({
                "rule": rule["name"],
                "keywords": hits,
                "suggest": rule["suggest"]
            })
    return results
