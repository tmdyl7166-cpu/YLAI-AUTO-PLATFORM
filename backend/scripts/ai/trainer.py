import json
from pathlib import Path

TRAIN_FILE = Path("logs/train.jsonl")


def save_training_sample(file, before, after, rules):
    record = {
        "file": str(file),
        "before": before[:500],
        "after": after[:500],
        "rules": rules
    }
    TRAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRAIN_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
