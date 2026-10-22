#!/usr/bin/env python3
"""Read / update the marketing leads workbook for the instagram-store-builder skill.

  leads.py list   FILE [--sheet NAME] [--all]   pending rows as JSON (row number + every column)
  leads.py update FILE ROW key=value ... [--sheet NAME]   write cells (missing headers are appended)

A row is "pending" when its `status` cell is empty or `pending`/`failed`.
Header matching is case-insensitive and trims spaces. The file must not be open
in Excel while updating (Excel holds a lock and the save will fail or be lost).
"""
import json
import sys

from openpyxl import load_workbook

DONE = {"done", "created", "skipped", "in_progress"}


def sheet_of(wb, name):
    return wb[name] if name else wb.worksheets[0]


def headers(ws):
    return {str(c.value).strip().lower(): c.column for c in ws[1] if c.value is not None}


def pop_flag(args, flag):
    if flag in args:
        i = args.index(flag)
        val = args[i + 1]
        del args[i : i + 2]
        return val
    return None


def cmd_list(path, sheet, include_all):
    wb = load_workbook(path, data_only=True)
    ws = sheet_of(wb, sheet)
    names = [str(c.value).strip() if c.value is not None else f"col{c.column}" for c in ws[1]]
    status_col = headers(ws).get("status")
    rows = []
    for r in ws.iter_rows(min_row=2):
        values = {names[i]: (c.value if c.value is not None else "") for i, c in enumerate(r) if i < len(names)}
        if not any(str(v).strip() for v in values.values()):
            continue
        status = str(r[status_col - 1].value or "").strip().lower() if status_col else ""
        if include_all or status not in DONE:
            rows.append({"row": r[0].row, **{k: str(v) for k, v in values.items()}})
    print(json.dumps({"sheet": ws.title, "count": len(rows), "rows": rows}, ensure_ascii=False, indent=1))


def cmd_update(path, row, pairs, sheet):
    wb = load_workbook(path)
    ws = sheet_of(wb, sheet)
    cols = headers(ws)
    for pair in pairs:
        key, _, value = pair.partition("=")
        col = cols.get(key.strip().lower())
        if col is None:
            col = ws.max_column + 1
            ws.cell(row=1, column=col, value=key.strip())
            cols[key.strip().lower()] = col
        ws.cell(row=int(row), column=col, value=value)
    wb.save(path)
    print(json.dumps({"ok": True, "row": int(row), "written": pairs}, ensure_ascii=False))


def main():
    args = sys.argv[1:]
    sheet = pop_flag(args, "--sheet")
    include_all = "--all" in args
    args = [a for a in args if a != "--all"]
    if len(args) >= 2 and args[0] == "list":
        cmd_list(args[1], sheet, include_all)
    elif len(args) >= 4 and args[0] == "update":
        cmd_update(args[1], args[2], args[3:], sheet)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
