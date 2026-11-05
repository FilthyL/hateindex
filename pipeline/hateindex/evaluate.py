"""Measure the classifier against hand-labelled posts (pipeline/tests/eval/labels.jsonl).

    python -m pipeline.hateindex.evaluate [labels.jsonl]

The sample is stratified (it over-represents posts the classifier flagged
and sources where hostility is common), so precision and recall here are
for this sample, not population rates. It shows *where* the rules go wrong.
"""
import json
import os
import sys
from collections import Counter

from .classify import classify

DEFAULT = os.path.join(os.path.dirname(__file__), "..", "tests", "eval", "labels.jsonl")


def evaluate(path=DEFAULT):
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    tp = fp = fn = tn = 0
    target_wrong, sev_exact, sev_close, n_sev = 0, 0, 0, 0
    by_source = Counter()
    misses, false_alarms = [], []
    for row in rows:
        r = classify(row["text"], row.get("context", ""))
        truth = row["severity"] > 0
        pred = r.targeted and not r.sarcastic and r.severity > 0
        if r.targeted != row["about_indians"]:
            target_wrong += 1
        if truth and pred:
            tp += 1
            n_sev += 1
            sev_exact += r.severity == row["severity"]
            sev_close += abs(r.severity - row["severity"]) <= 1
        elif pred:
            fp += 1
            false_alarms.append((row, r.severity))
        elif truth:
            fn += 1
            misses.append((row, r.severity))
            by_source[row["source"]] += 1
        else:
            tn += 1
    p = tp / (tp + fp) if tp + fp else 0
    rc = tp / (tp + fn) if tp + fn else 0
    return {
        "n": len(rows), "precision": round(p, 3), "recall": round(rc, 3),
        "f1": round(2 * p * rc / (p + rc), 3) if p + rc else 0,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "target_accuracy": round(1 - target_wrong / len(rows), 3),
        "severity_exact": round(sev_exact / n_sev, 3) if n_sev else None,
        "severity_within_1": round(sev_close / n_sev, 3) if n_sev else None,
        "misses_by_source": dict(by_source),
    }, misses, false_alarms


def main(argv=None):
    path = (argv or sys.argv[1:] or [DEFAULT])[0]
    stats, misses, false_alarms = evaluate(path)
    print(json.dumps(stats, indent=2))
    for title, rows in (("MISSED (labelled hostile, predicted not)", misses), ("FALSE ALARMS", false_alarms)):
        print(f"\n{title}: {len(rows)}")
        for row, pred in rows:
            print(f"  [{row['source']} true={row['severity']} pred={pred}] {row['text'][:150]!r}")


if __name__ == "__main__":
    main()
