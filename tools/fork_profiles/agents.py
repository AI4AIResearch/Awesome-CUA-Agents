"""Validate Agents computer-use action records from JSON Lines."""
from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

PROFILE = 'agents'
ACTION_FIELDS: dict[str, tuple[str, ...]] = {
    "act": [
        "action"
    ],
    "observe": [],
    "plan": [
        "goal"
    ],
    "verify": [
        "goal"
    ]
}
COORDINATE_FIELDS = {"x", "y", "x1", "y1", "x2", "y2"}


def validate_record(record: Any) -> list[str]:
    """Return readable validation errors for one {"action": {...}} record."""
    if not isinstance(record, Mapping):
        return ["record must be a JSON object"]
    action = record.get("action")
    if not isinstance(action, Mapping):
        return ["action must be a JSON object"]
    kind = action.get("type")
    if not isinstance(kind, str) or kind not in ACTION_FIELDS:
        return [f"unsupported action type: {kind!r}"]
    errors = [f"action is missing {field!r}" for field in ACTION_FIELDS[kind] if field not in action]
    for field in COORDINATE_FIELDS.intersection(action):
        value = action[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
            errors.append(f"{field} must be a normalized number in [0, 1]")
    if "success" in record and not isinstance(record["success"], bool):
        errors.append("success must be a boolean when present")
    return errors


def validate_jsonl(path: Path) -> list[str]:
    """Validate every nonblank JSONL line and include its line number in errors."""
    errors: list[str] = []
    for line_number, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not text.strip():
            continue
        try:
            record = json.loads(text)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{line_number}: invalid JSON: {exc.msg}")
            continue
        errors.extend(f"{path}:{line_number}: {error}" for error in validate_record(record))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path, help="JSONL file containing action records")
    args = parser.parse_args()
    errors = validate_jsonl(args.jsonl)
    if errors:
        print("\n".join(errors))
        return 1
    print(f"{args.jsonl}: valid {PROFILE} action records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
