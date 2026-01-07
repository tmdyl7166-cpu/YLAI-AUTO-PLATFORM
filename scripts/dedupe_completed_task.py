#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deduplicate repeated AI connection errors in Task/CompletedTask.md.
- Collapses repeated HTTPConnectionPool/Connection refused entries into a single summary block.
- Preserves first occurrence and appends a summarized time range.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "Task" / "CompletedTask.md"

# Match the error JSON blocks across multiple lines
ERR_PAT = re.compile(
    r"\{\s*\"error\"\s*:\s*\"HTTPConnectionPool.*?Connection refused.*?\"\s*\}\s*",
    re.DOTALL,
)
HEADER_PAT = re.compile(r"^## +(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?$", re.MULTILINE)

SUMMARY_HEADER = (
    "### 错误摘要（AI 连接拒绝去重）\n"
    "- 类型：HTTPConnectionPool/Connection refused\n"
)


def main():
    text = FILE.read_text(encoding="utf-8")
    # Find all error blocks
    errors = list(ERR_PAT.finditer(text))
    if len(errors) <= 1:
        print("No duplicates found or only single occurrence. No changes.")
        return

    # Collect timestamps around error blocks
    # Strategy: scan lines preceding error match for nearest markdown header with timestamp
    lines = text.splitlines()
    idx_map = [text[:m.start()].count("\n") for m in errors]
    ts_list = []
    for idx in idx_map:
        # Search backwards up to 20 lines for a timestamp header
        start = max(0, idx - 20)
        block = "\n".join(lines[start:idx])
        m = list(HEADER_PAT.finditer(block))
        if m:
            ts_list.append(m[-1].group("ts"))
        else:
            ts_list.append(None)

    # Keep the first error occurrence; remove subsequent duplicates
    first_err = errors[0]
    start_pos = first_err.start()
    end_pos = first_err.end()

    # Build new content: preserve first block, remove others
    new_text_parts = []
    last_pos = 0
    for i, m in enumerate(errors):
        if i == 0:
            # keep
            new_text_parts.append(text[last_pos:m.end()])
            last_pos = m.end()
        else:
            # skip duplicate block
            new_text_parts.append(text[last_pos:m.start()])
            last_pos = m.end()
    new_text_parts.append(text[last_pos:])
    new_text = "".join(new_text_parts)

    # Append summary block after first kept error
    # Determine time range
    first_ts = ts_list[0]
    last_ts = None
    for ts in ts_list[::-1]:
        if ts:
            last_ts = ts
            break
    range_line = (
        f"- 时间范围：{first_ts or '未知'} 至 {last_ts or '未知'}\n"
        if len(errors) > 1 else ""
    )

    summary_block = "\n" + SUMMARY_HEADER + range_line + "- 去重：后续同类错误不再重复记录\n"
    # Insert summary_block right after first error JSON line
    insert_pos = new_text.find("}\",", start_pos)
    if insert_pos == -1:
        insert_pos = end_pos
    new_text = new_text[:insert_pos] + "\n" + summary_block + new_text[insert_pos:]

    FILE.write_text(new_text, encoding="utf-8")
    print("Deduplication applied. Duplicates collapsed with summary.")


if __name__ == "__main__":
    main()
