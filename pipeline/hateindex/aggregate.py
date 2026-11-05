"""Turn classified posts into the per-country index (docs/DEFINITION.md)."""
import json
import os
import re
from email.utils import parsedate_to_datetime
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from .classify import classify, SEVERITY_NAMES
from . import taxonomy as T

SHRINK_K = 30
MIN_AUTHORS = 10
LAYERS = {"people": ("social",), "media": ("news",)}
DOMESTIC = {"IN"}  # Indians posting about Indians: shown, not ranked

_REGIONS = json.load(open(os.path.join(os.path.dirname(__file__), "regions.json")))
_COUNTRIES = json.load(open(os.path.join(os.path.dirname(__file__), "countries.json")))
SHORT_NAMES = {"US": "United States", "GB": "United Kingdom", "RU": "Russia", "KR": "South Korea", "IR": "Iran",
               "VN": "Vietnam", "TW": "Taiwan", "BO": "Bolivia", "VE": "Venezuela", "TZ": "Tanzania", "SY": "Syria",
               "LA": "Laos", "MD": "Moldova", "KP": "North Korea", "CZ": "Czechia", "AE": "United Arab Emirates"}


def country_meta(cc):
    c = _COUNTRIES.get(cc, {})
    r = _REGIONS.get(cc, {})
    return {"iso2": cc, "iso3": c.get("a3"), "num": c.get("num"), "name": SHORT_NAMES.get(cc) or c.get("name") or cc,
            "region": r.get("region") or "Other", "subregion": r.get("sub") or ""}


def parse_date(value):
    """Best-effort date from the formats sources use (ISO, RFC 822, GDELT, epoch)."""
    if value is None or value == "":
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, timezone.utc)
        v = str(value).strip()
        if re.fullmatch(r"\d{8}T\d{6}Z", v):  # GDELT
            return datetime.strptime(v, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        if v[:4].isdigit() and "-" in v[:8]:
            d = datetime.fromisoformat(v.replace("Z", "+00:00"))
        else:
            d = parsedate_to_datetime(v)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def _week(d):
    monday = (d - timedelta(days=d.weekday())).date()
    return monday.isoformat()


def timeline(items, weeks=26, now=None):
    """Weekly sincere posts about Indians and the share that were hostile."""
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(weeks=weeks)
    buckets = defaultdict(lambda: [0, 0])
    for d, r in items:
        if d and start <= d <= now + timedelta(days=1):
            b = buckets[_week(d)]
            b[0] += 1
            b[1] += r.hateful
    out = []
    for i in range(weeks + 1):
        w = _week(start + timedelta(weeks=i))
        posts, hostile = buckets.get(w, [0, 0])
        out.append({"week": w, "posts": posts, "hostile": hostile,
                    "share": round(hostile / posts, 4) if posts else None})
    return out


def confidence(n):
    return "insufficient" if n < MIN_AUTHORS else "low" if n < 50 else "medium" if n < 300 else "high"


def _layer_stats(items, global_raw):
    """items: list of (author, Result) — sincere, targeted posts only."""
    by_author = defaultdict(list)
    for author, r in items:
        by_author[author].append(r.weight)
    n = len(by_author)
    raw = 100 * sum(sum(w) / len(w) for w in by_author.values()) / n if n else 0.0
    adjusted = (n * raw + SHRINK_K * global_raw) / (n + SHRINK_K) if n else None
    hateful = [r for _, r in items if r.hateful]
    reasons, stereos = Counter(), Counter()
    for r in hateful:
        reasons.update(r.reasons)
        stereos.update(r.stereotypes)
    sev = Counter(r.severity for _, r in items)
    hateful_authors = sum(1 for w in by_author.values() if max(w) > 0)
    nh = len(hateful) or 1
    return {
        "index": round(adjusted, 2) if adjusted is not None else None,
        "raw": round(raw, 2), "authors": n, "posts": len(items), "hateful_posts": len(hateful),
        "hateful_author_share": round(hateful_authors / n, 4) if n else 0,
        "confidence": confidence(n),
        "severity": {SEVERITY_NAMES[k]: sev.get(k, 0) for k in range(5)},
        "slur_posts": sum(1 for r in hateful if r.slur),
        "reasons": [{"id": k, "label": T.REASONS[k], "share": round(v / nh, 3)} for k, v in reasons.most_common(6)],
        "stereotypes": [{"id": k, "label": T.STEREOTYPES[k][0], "share": round(v / nh, 3)} for k, v in stereos.most_common(6)],
    }


def summary_text(name, s):
    if not s or s["confidence"] == "insufficient":
        return f"Not enough posts about Indians from {name} yet to say anything reliable."
    if not s["hateful_posts"]:
        return f"None of the {s['posts']} sincere posts about Indians from {name} met the hate definition."
    pct = round(100 * s["hateful_author_share"])
    parts = [f"{pct}% of people posting about Indians from {name} posted something hostile."]
    if s["reasons"]:
        top = [r["label"].lower() for r in s["reasons"][:2]]
        parts.append("Hostility is driven mainly by " + " and ".join(top) + ".")
    if s["stereotypes"]:
        parts.append(f"The most repeated stereotype: “{s['stereotypes'][0]['label']}”.")
    return " ".join(parts)


def build(records, window_label="", source_status=None):
    totals = Counter()
    per = defaultdict(lambda: defaultdict(list))  # cc -> layer -> [(author, r)]
    excluded = defaultdict(Counter)                # cc -> {sarcasm, counter, state}
    glob = defaultdict(list)
    src_counts = Counter()
    src_targeted, src_hostile = Counter(), Counter()
    by_region = defaultdict(list)                   # region -> [(author, r)] (all layers)
    dated = defaultdict(list)                       # layer -> [(date, r)]

    first_collected = min((r["collected"] for r in records if r.get("collected")), default=None)
    for rec in records:
        totals["posts"] += 1
        src_counts[rec["source"]] += 1
        r = classify(rec.get("text", ""), rec.get("context", ""))
        cc = rec.get("country")
        if r.state_only:
            totals["state_critique"] += 1
            excluded[cc]["state_critique"] += 1
        if not r.targeted:
            continue
        totals["targeted"] += 1
        if r.sarcastic:
            totals["sarcasm_excluded"] += 1
            excluded[cc]["sarcasm"] += 1
            continue
        if r.counter:
            totals["counter_speech"] += 1
            excluded[cc]["counter_speech"] += 1
        if r.hateful:
            totals["hateful"] += 1
        src_targeted[rec["source"]] += 1
        src_hostile[rec["source"]] += r.hateful
        key = (rec["source"], rec["author"])
        when = parse_date(rec.get("created")) or parse_date(rec.get("collected"))
        glob["all"].append((key, r))
        dated["all"].append((when, r))
        if cc and cc not in DOMESTIC:
            by_region[country_meta(cc)["region"]].append((key, r))
        for layer, kinds in LAYERS.items():
            if rec["kind"] in kinds:
                glob[layer].append((key, r))
                dated[layer].append((when, r))
                if cc:
                    per[cc][layer].append((key, r))

    g = {}
    for layer in ["all", *LAYERS]:
        g[layer] = _layer_stats(glob[layer], 0)
        g[layer]["index"] = g[layer]["raw"]

    countries = {}
    for cc, layers in per.items():
        meta = country_meta(cc)
        if not meta["num"]:
            continue
        entry = {**meta, "domestic": cc in DOMESTIC, "layers": {}, "excluded": dict(excluded[cc])}
        all_items = [x for items in layers.values() for x in items]
        entry["layers"]["all"] = _layer_stats(all_items, g["all"]["raw"])
        for layer in LAYERS:
            entry["layers"][layer] = _layer_stats(layers.get(layer, []), g[layer]["raw"])
        sincere = entry["layers"]["all"]["posts"] + excluded[cc]["sarcasm"]
        entry["sarcasm_share"] = round(excluded[cc]["sarcasm"] / sincere, 4) if sincere else 0
        entry["summary"] = {k: summary_text(meta["name"], v) for k, v in entry["layers"].items()}
        countries[cc] = entry

    for layer in ["all", *LAYERS]:
        ranked = sorted((c for c in countries.values()
                         if not c["domestic"] and c["layers"][layer]["confidence"] != "insufficient"),
                        key=lambda c: c["layers"][layer]["index"], reverse=True)
        for i, c in enumerate(ranked, 1):
            c["layers"][layer]["rank"] = i

    regions = []
    for name, items in by_region.items():
        st = _layer_stats(items, g["all"]["raw"])
        members = [c["iso2"] for c in countries.values() if c["region"] == name and not c["domestic"]]
        regions.append({"region": name, "countries": len(members), "authors": st["authors"], "posts": st["posts"],
                        "index": st["index"], "raw": st["raw"], "hateful_author_share": st["hateful_author_share"],
                        "confidence": st["confidence"], "reasons": st["reasons"][:3], "stereotypes": st["stereotypes"][:3]})
    regions.sort(key=lambda x: -x["authors"])

    overview = {
        "collection_started": first_collected,
        "countries_with_data": sum(1 for c in countries.values() if c["layers"]["all"]["authors"]),
        "countries_scored": {layer: sum(1 for c in countries.values() if c["layers"][layer].get("rank"))
                             for layer in ["all", *LAYERS]},
        "regions": regions,
        "timeline": {layer: timeline(dated[layer]) for layer in ["all", *LAYERS]},
        "by_source": sorted(({"source": k, "about_indians": v, "hostile": src_hostile[k]}
                             for k, v in src_targeted.items()), key=lambda x: -x["about_indians"]),
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window": window_label, "demo": False,
        "totals": dict(totals), "sources": {k: {"posts": src_counts.get(k, 0), **(source_status or {}).get(k, {})}
                                            for k in sorted(set(src_counts) | set(source_status or {}))},
        "global": g,
        "reasons": T.REASONS,
        "stereotypes": {k: v[0] for k, v in T.STEREOTYPES.items()},
        "countries": countries,
        "overview": overview,
    }
