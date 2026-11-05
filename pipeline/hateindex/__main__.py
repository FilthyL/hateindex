"""CLI.

    python -m hateindex collect [--sources reddit,4chan,...]   # fetch new posts into data/raw
    python -m hateindex build                                  # classify + write site/data/index.json
    python -m hateindex classify "some text"                   # debug one post
"""
import argparse
import gzip
import inspect
import json
import os
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone

from . import collectors as C
from .aggregate import build
from .classify import classify

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "site", "data", "index.json")
STATUS = os.path.join(ROOT, "data", "source_status.json")

# Per-host politeness (seconds between requests).
INTERVALS = {"reddit": 7.0, "4chan": 1.1, "gdelt": 6.0, "google_news": 2.0, "hackernews": 0.5,
             "mastodon": 1.0, "lemmy": 1.0, "bluesky": 1.0, "medium": 2.0, "wordpress": 1.0}
DEFAULT_SOURCES = list(C.COLLECTORS)
# Max seconds per source per run. Runs are hourly, so the total stays well under an hour.
BUDGET = {"4chan": 1000, "reddit": 800, "lemmy": 300, "google_news": 300, "mastodon": 300, "hackernews": 180,
          "bluesky": 180, "gdelt": 180, "medium": 120, "wordpress": 120}
DEFAULT_BUDGET = 120
STATE = os.path.join(ROOT, "data", "state")


def _path(source):
    return os.path.join(RAW, f"{source}.jsonl.gz")


def load(source):
    p = _path(source)
    if not os.path.exists(p):
        return []
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def save(source, records):
    os.makedirs(RAW, exist_ok=True)
    with gzip.open(_path(source), "wt", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def collect(sources, retention_days, cap):
    status = json.load(open(STATUS)) if os.path.exists(STATUS) else {}
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=retention_days)).isoformat()
    for name in sources:
        existing = load(name)
        seen = {r["id"] for r in existing}
        new, err = [], None
        started = time.time()
        f = C.Fetcher(min_interval=INTERVALS.get(name, 1.0), deadline=started + BUDGET.get(name, DEFAULT_BUDGET))
        collector = C.COLLECTORS[name]
        state_path = os.path.join(STATE, f"{name}.json")
        state = None
        if "state" in inspect.signature(collector).parameters:
            state = json.load(open(state_path)) if os.path.exists(state_path) else {}
        try:
            for rec in (collector(f, state=state) if state is not None else collector(f)):
                if rec["id"] in seen or not rec.get("text"):
                    continue
                rec["collected"] = now.isoformat(timespec="seconds")
                seen.add(rec["id"])
                new.append(rec)
                if len(new) >= cap:
                    break
        except C.BudgetExceeded:
            err = None
            print(f"[{name}] time budget reached; keeping partial results", flush=True)
        except Exception as e:  # keep whatever we got before the failure
            err = f"{type(e).__name__}: {e}"[:300]
            if not str(e).startswith("skipped"):
                traceback.print_exc(limit=1)
        if err is None and not new and f._dead:
            err = "no data; unreachable: " + ", ".join(sorted(f._dead))[:250]
        if state is not None:
            os.makedirs(STATE, exist_ok=True)
            json.dump(state, open(state_path, "w"))
        kept = [r for r in existing if r.get("collected", "") >= cutoff] + new
        save(name, kept)
        status[name] = {"last_run": now.isoformat(timespec="seconds"), "new": len(new), "stored": len(kept),
                        "ok": err is None, "error": err,
                        "seconds": round(time.time() - started)}
        print(f"[{name}] +{len(new)} new, {len(kept)} stored" + (f"  ERROR {err}" if err else ""), flush=True)
    os.makedirs(os.path.dirname(STATUS), exist_ok=True)
    json.dump(status, open(STATUS, "w"), indent=2)


def build_cmd(retention_days):
    status = json.load(open(STATUS)) if os.path.exists(STATUS) else {}
    records = [r for s in C.COLLECTORS for r in load(s)]
    out = build(records, window_label=f"last {retention_days} days", source_status=status)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    t = out["totals"]
    print(f"built {OUT}: {t.get('posts', 0)} posts, {t.get('targeted', 0)} about Indians, "
          f"{t.get('hateful', 0)} hateful, {t.get('sarcasm_excluded', 0)} sarcasm excluded, "
          f"{len(out['countries'])} countries")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="hateindex")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--sources", default=",".join(DEFAULT_SOURCES))
    c.add_argument("--retention-days", type=int, default=365)
    c.add_argument("--cap", type=int, default=20000, help="max new records per source per run")
    b = sub.add_parser("build")
    b.add_argument("--retention-days", type=int, default=365)
    k = sub.add_parser("classify")
    k.add_argument("text")
    k.add_argument("--context", default="")
    a = ap.parse_args(argv)
    if a.cmd == "collect":
        collect([s.strip() for s in a.sources.split(",") if s.strip()], a.retention_days, a.cap)
    elif a.cmd == "build":
        build_cmd(a.retention_days)
    else:
        print(json.dumps(classify(a.text, a.context).to_dict(), indent=2))


if __name__ == "__main__":
    sys.exit(main())
