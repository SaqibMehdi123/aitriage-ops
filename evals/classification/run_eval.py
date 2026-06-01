#!/usr/bin/env python
"""Classification eval — run the live classifier over the labelled set and report
accuracy. Per the Technical Foundation, run this on every prompt/model change.

Usage (inside the api container, which has deps + GROQ_API_KEY from .env):
    docker compose exec api python /evals/classification/run_eval.py

Exits non-zero if category accuracy falls below the target (PRD: >= 90% on top
categories), so it can gate CI.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

# Make the backend `triage` package importable whether run from host or container.
HERE = Path(__file__).resolve().parent
for candidate in (Path("/app"), HERE.parent.parent / "backend"):
    if (candidate / "triage").exists():
        sys.path.insert(0, str(candidate))
        break

TARGET_ACCURACY = float(os.environ.get("EVAL_TARGET_ACCURACY", "0.90"))


def main() -> int:
    from triage.classification.service import classify_text, model_version
    from triage.config import get_settings

    if not get_settings().groq_api_key:
        print("SKIP: GROQ_API_KEY not set — cannot run live classification eval.")
        return 0

    dataset = [json.loads(l) for l in (HERE / "dataset.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"Model: {model_version()}   Examples: {len(dataset)}\n")

    correct = 0
    urg_correct = 0
    per_cat: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # cat -> [correct, total]
    failures: list[str] = []

    for ex in dataset:
        try:
            res = classify_text(ex["subject"], ex["body"], ex.get("from"))
        except Exception as exc:
            failures.append(f"  ! error on {ex['subject']!r}: {exc}")
            per_cat[ex["expected_category"]][1] += 1
            continue

        exp = ex["expected_category"]
        per_cat[exp][1] += 1
        if res.category == exp:
            correct += 1
            per_cat[exp][0] += 1
        else:
            failures.append(f"  ✗ {ex['subject'][:40]!r}: expected {exp}, got {res.category} (conf {res.confidence:.2f})")
        if res.urgency == ex.get("expected_urgency"):
            urg_correct += 1

    n = len(dataset)
    accuracy = correct / n if n else 0.0
    print("Per-category accuracy:")
    for cat, (c, t) in sorted(per_cat.items()):
        print(f"  {cat:<8} {c}/{t}  ({(c / t * 100) if t else 0:.0f}%)")
    print(f"\nCategory accuracy: {correct}/{n} = {accuracy:.1%}")
    print(f"Urgency accuracy:  {urg_correct}/{n} = {urg_correct / n:.1%}")

    if failures:
        print("\nMisses:")
        print("\n".join(failures))

    print(f"\nTarget: {TARGET_ACCURACY:.0%}  →  {'PASS' if accuracy >= TARGET_ACCURACY else 'FAIL'}")
    return 0 if accuracy >= TARGET_ACCURACY else 1


if __name__ == "__main__":
    raise SystemExit(main())
