"""Collectors for public, keyless sources.

Each collector yields records:
    {id, source, kind, country, author, text, context, url, created}
- kind: "social" (people posting), "news" (outlets), or "blog"
- country: ISO-3166 alpha-2 code, or None when the source has no location
- author: a salted hash, so raw data never stores usernames

Every collector is best-effort: if a source blocks us, rate-limits us or
changes its API, the error is recorded and the run carries on.
"""
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

UA = "hateindex-research/0.2 (+https://github.com/FilthyL/hateindex; academic sentiment research)"
SALT = os.environ.get("HATEINDEX_SALT", "hateindex")

QUERIES = ["indians", "\"indian immigrants\"", "\"indian students\"", "pajeet", "\"indian workers\"", "h1b indians"]


def author_hash(source, raw):
    return hashlib.sha256(f"{SALT}:{source}:{raw}".encode()).hexdigest()[:16]


class Fetcher:
    def __init__(self, min_interval=1.0, timeout=30, retries=3):
        self.min_interval, self.timeout, self.retries = min_interval, timeout, retries
        self._last = {}

    def get(self, url, headers=None, as_json=True):
        host = urllib.parse.urlparse(url).netloc
        wait = self.min_interval - (time.time() - self._last.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*", **(headers or {})})
        err = None
        for attempt in range(self.retries):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    self._last[host] = time.time()
                    data = resp.read()
                    return json.loads(data) if as_json else data.decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                err = e
                self._last[host] = time.time()
                if e.code in (429, 500, 502, 503, 504):
                    time.sleep(2 ** (attempt + 2))
                    continue
                raise
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
                err = e
                time.sleep(2 ** (attempt + 1))
        raise err


def _iso(ts):
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, timezone.utc).isoformat()
        return ts
    except Exception:
        return None


# ---------------------------------------------------------------- Reddit ----
# Country subreddits; posts there are attributed to that country.
REDDIT_SUBS = {
    "canada": "CA", "onguardforthee": "CA", "toronto": "CA", "vancouver": "CA", "Brampton": "CA",
    "ontario": "CA", "britishcolumbia": "CA", "alberta": "CA", "CanadaPolitics": "CA",
    "unitedkingdom": "GB", "ukpolitics": "GB", "CasualUK": "GB", "london": "GB", "AskUK": "GB",
    "australia": "AU", "sydney": "AU", "melbourne": "AU", "AustralianPolitics": "AU", "perth": "AU",
    "newzealand": "NZ", "auckland": "NZ", "ireland": "IE", "AskAnAmerican": "US", "Conservative": "US",
    "texas": "US", "nyc": "US", "bayarea": "US", "news": None, "cscareerquestions": None,
    "singapore": "SG", "malaysia": "MY", "southafrica": "ZA", "dubai": "AE", "UAE": "AE",
    "qatar": "QA", "saudiarabia": "SA", "pakistan": "PK", "bangladesh": "BD", "srilanka": "LK",
    "Nepal": "NP", "Philippines": "PH", "Kenya": "KE", "Nigeria": "NG", "germany": "DE",
    "Netherlands": "NL", "sweden": "SE", "Denmark": "DK", "Norway": "NO", "poland": "PL",
    "japan": "JP", "China": "CN", "fiji": "FJ", "mauritius": "MU", "TrinidadandTobago": "TT",
    "guyana": "GY", "italy": "IT", "france": "FR", "europe": None, "AskEurope": None, "portugal": "PT",
}


def reddit(f, max_threads_per_sub=8, subs=None):
    subs = subs or REDDIT_SUBS
    consecutive_fail = 0
    for sub, cc in subs.items():
        q = urllib.parse.quote("indian OR indians OR desi OR pajeet")
        url = f"https://www.reddit.com/r/{sub}/search.json?q={q}&restrict_sr=1&sort=relevance&t=year&limit=50"
        try:
            listing = f.get(url)
            consecutive_fail = 0
        except Exception as e:  # one blocked/private sub shouldn't stop the rest...
            consecutive_fail += 1
            if consecutive_fail >= 5:  # ...but five in a row means we're being blocked
                raise RuntimeError(f"reddit appears to block unauthenticated requests: {e}") from e
            continue
        posts = [c["data"] for c in listing.get("data", {}).get("children", [])]
        for p in posts:
            yield _reddit_rec(p, sub, cc, p.get("title", "") + "\n" + p.get("selftext", ""), "", p.get("permalink"))
        posts.sort(key=lambda p: p.get("num_comments", 0), reverse=True)
        for p in posts[:max_threads_per_sub]:
            try:
                thread = f.get(f"https://www.reddit.com/r/{sub}/comments/{p['id']}.json?limit=300&depth=4")
            except Exception:
                continue
            stack = list(thread[1]["data"]["children"]) if len(thread) > 1 else []
            while stack:
                c = stack.pop()
                if c.get("kind") != "t1":
                    continue
                d = c["data"]
                yield _reddit_rec(d, sub, cc, d.get("body", ""), p.get("title", ""), d.get("permalink"))
                rep = d.get("replies")
                if isinstance(rep, dict):
                    stack.extend(rep["data"]["children"])


def _reddit_rec(d, sub, cc, text, ctx, permalink):
    return {"id": f"reddit:{d.get('name') or d.get('id')}", "source": "reddit", "kind": "social", "country": cc,
            "author": author_hash("reddit", d.get("author", "")), "text": text, "context": ctx,
            "url": f"https://www.reddit.com{permalink}" if permalink else None, "created": _iso(d.get("created_utc"))}


# ---------------------------------------------------------------- 4chan -----
# The official read-only API (https://github.com/4chan/4chan-API). /pol/ and
# /int/ show an IP-based country flag on each post.
CHAN_TERMS = re.compile(r"\b(?:indians?|desis?|pajeets?|jeets?|saa+r|curry|poo in loo|street shitt?ers?|h-?1b)\b", re.I)


def fourchan(f, boards=("pol", "int", "bant")):
    for board in boards:
        catalog = f.get(f"https://a.4cdn.org/{board}/catalog.json")
        threads = [t for page in catalog for t in page.get("threads", [])]
        hits = [t for t in threads if CHAN_TERMS.search(f"{t.get('sub', '')} {t.get('com', '')}")]
        for t in hits:
            try:
                data = f.get(f"https://a.4cdn.org/{board}/thread/{t['no']}.json")
            except Exception:
                continue
            ctx = f"{t.get('sub', '')} {t.get('com', '')}"
            for p in data.get("posts", []):
                cc = p.get("country")  # absent for troll/meme flags, which we ignore
                if not p.get("com"):
                    continue
                yield {"id": f"4chan:{board}:{p['no']}", "source": "4chan", "kind": "social",
                       "country": cc if cc and cc not in ("XX", "A1", "A2", "EU") else None,
                       "author": author_hash("4chan", f"{t['no']}:{p.get('id', p['no'])}"),
                       "text": p["com"], "context": "" if p["no"] == t["no"] else ctx,
                       "url": f"https://boards.4chan.org/{board}/thread/{t['no']}#p{p['no']}", "created": _iso(p.get("time"))}


# ---------------------------------------------------------------- GDELT -----
# GDELT DOC 2.0: global news, tagged with the outlet's country.
GDELT_FIPS = {
    "US": "US", "UK": "GB", "CA": "CA", "AS": "AU", "NZ": "NZ", "EI": "IE", "SN": "SG", "MY": "MY", "SF": "ZA",
    "AE": "AE", "SA": "SA", "QA": "QA", "KU": "KW", "MU": "OM", "BA": "BH", "PK": "PK", "BG": "BD", "CE": "LK",
    "NP": "NP", "CH": "CN", "JA": "JP", "GM": "DE", "FR": "FR", "IT": "IT", "NL": "NL", "IS": "IL", "RS": "RU",
    "RP": "PH", "ID": "ID", "KE": "KE", "NI": "NG", "FJ": "FJ", "MP": "MU", "TD": "TT", "GY": "GY", "SW": "SE",
    "PL": "PL", "TU": "TR", "BM": "MM", "AF": "AF", "MV": "MV", "IN": "IN",
}


def gdelt(f, timespan="3months"):
    f_slow = Fetcher(min_interval=6.0, timeout=60)  # GDELT asks for ≤1 request / 5 s
    q = '(indians OR "indian immigrants" OR "indian students" OR "indian workers" OR "anti-indian")'
    for fips, cc in GDELT_FIPS.items():
        params = urllib.parse.urlencode({"query": f"{q} sourcecountry:{fips} sourcelang:english", "mode": "artlist",
                                         "format": "json", "maxrecords": 250, "timespan": timespan, "sort": "hybridrel"})
        try:
            data = f_slow.get(f"https://api.gdeltproject.org/api/v2/doc/doc?{params}")
        except Exception:
            continue
        for a in data.get("articles", []) if isinstance(data, dict) else []:
            yield {"id": f"gdelt:{hashlib.sha1(a['url'].encode()).hexdigest()[:16]}", "source": "gdelt", "kind": "news",
                   "country": cc, "author": author_hash("gdelt", a.get("domain", "")), "text": a.get("title", ""),
                   "context": "", "url": a["url"], "created": a.get("seendate")}


# ---------------------------------------------------------- Google News -----
GNEWS_EDITIONS = ["US", "GB", "CA", "AU", "NZ", "IE", "SG", "MY", "ZA", "NG", "KE", "PK", "PH", "BD", "IL", "AE",
                  "GH", "UG", "TZ", "ZW", "BW", "NA", "ET", "LB"]


def google_news(f):
    for cc in GNEWS_EDITIONS:
        for q in ("indians", "\"indian immigrants\"", "\"anti-indian\""):
            params = urllib.parse.urlencode({"q": q, "hl": f"en-{cc}", "gl": cc, "ceid": f"{cc}:en"})
            try:
                xml = f.get(f"https://news.google.com/rss/search?{params}", as_json=False)
            except Exception:
                continue
            for item in ET.fromstring(xml).iter("item"):
                link = item.findtext("link") or ""
                src = item.find("source")
                yield {"id": f"gnews:{hashlib.sha1(link.encode()).hexdigest()[:16]}", "source": "google_news",
                       "kind": "news", "country": cc,
                       "author": author_hash("gnews", src.text if src is not None else link),
                       "text": item.findtext("title") or "", "context": "", "url": link, "created": item.findtext("pubDate")}


# ---------------------------------------------------------- Hacker News -----
def hackernews(f, pages=5):
    for q in ("indians", "indian workers", "h1b indians", "indian managers"):
        for page in range(pages):
            params = urllib.parse.urlencode({"query": q, "tags": "comment", "hitsPerPage": 200, "page": page})
            data = f.get(f"https://hn.algolia.com/api/v1/search?{params}")
            for h in data.get("hits", []):
                yield {"id": f"hn:{h['objectID']}", "source": "hackernews", "kind": "social", "country": None,
                       "author": author_hash("hn", h.get("author", "")), "text": h.get("comment_text") or "",
                       "context": h.get("story_title") or "", "url": f"https://news.ycombinator.com/item?id={h['objectID']}",
                       "created": h.get("created_at")}
            if page + 1 >= data.get("nbPages", 0):
                break


# ------------------------------------------------------------- Mastodon -----
MASTODON_INSTANCES = {
    "mastodon.social": None, "mastodon.online": None, "mstdn.social": None, "mas.to": None,
    "mstdn.ca": "CA", "mastodon.scot": "GB", "mastodon.org.uk": "GB", "aus.social": "AU", "mastodon.nz": "NZ",
    "mastodon.ie": "IE", "sfba.social": "US", "mastodon.sg": "SG", "mastodon.africa": None,
}


def mastodon(f, tags=("india", "indians", "indian", "h1b", "immigration")):
    for inst, cc in MASTODON_INSTANCES.items():
        for tag in tags:
            try:
                statuses = f.get(f"https://{inst}/api/v1/timelines/tag/{tag}?limit=40")
            except Exception:
                continue
            for s in statuses:
                if s.get("language") not in (None, "en"):
                    continue
                acct = s.get("account", {})
                # Only count local accounts toward the instance's country.
                local = "@" not in acct.get("acct", "@")
                yield {"id": f"mastodon:{s.get('uri')}", "source": "mastodon", "kind": "social",
                       "country": cc if local else None, "author": author_hash("mastodon", acct.get("url", "")),
                       "text": s.get("content", ""), "context": "", "url": s.get("url"), "created": s.get("created_at")}


# -------------------------------------------------------------- Bluesky -----
def bluesky(f, pages=5):
    # Public AppView search. May require auth in future; failures are recorded.
    for q in ("indians", "pajeet", "indian immigrants", "h1b indians"):
        cursor = None
        for _ in range(pages):
            params = {"q": q, "limit": 100, "lang": "en"}
            if cursor:
                params["cursor"] = cursor
            data = f.get("https://api.bsky.app/xrpc/app.bsky.feed.searchPosts?" + urllib.parse.urlencode(params))
            for p in data.get("posts", []):
                rec = p.get("record", {})
                yield {"id": f"bsky:{p['uri']}", "source": "bluesky", "kind": "social", "country": None,
                       "author": author_hash("bsky", p.get("author", {}).get("did", "")), "text": rec.get("text", ""),
                       "context": "", "url": None, "created": rec.get("createdAt")}
            cursor = data.get("cursor")
            if not cursor:
                break


# ---------------------------------------------------------------- Blogs -----
def medium(f, tags=("india", "indians", "indian-diaspora", "racism", "h1b", "immigration")):
    for tag in tags:
        xml = f.get(f"https://medium.com/feed/tag/{tag}", as_json=False)
        ns = {"content": "http://purl.org/rss/1.0/modules/content/", "dc": "http://purl.org/dc/elements/1.1/"}
        for item in ET.fromstring(xml).iter("item"):
            link = item.findtext("link") or ""
            body = item.findtext("content:encoded", default="", namespaces=ns)
            yield {"id": f"medium:{hashlib.sha1(link.encode()).hexdigest()[:16]}", "source": "medium", "kind": "blog",
                   "country": None, "author": author_hash("medium", item.findtext("dc:creator", "", ns)),
                   "text": (item.findtext("title") or "") + "\n" + body[:20000], "context": "", "url": link,
                   "created": item.findtext("pubDate")}


def wordpress(f, tags=("indians", "india", "indian-immigrants", "racism")):
    for tag in tags:
        data = f.get(f"https://public-api.wordpress.com/rest/v1.1/read/tags/{tag}/posts?number=40")
        for p in data.get("posts", []):
            yield {"id": f"wp:{p.get('site_ID')}:{p.get('ID')}", "source": "wordpress", "kind": "blog", "country": None,
                   "author": author_hash("wp", p.get("site_ID")), "text": p.get("title", "") + "\n" + p.get("content", "")[:20000],
                   "context": "", "url": p.get("URL"), "created": p.get("date")}


# ------------------------------------------------- Keyed (future) sources ---
def youtube(f):
    if not os.environ.get("YOUTUBE_API_KEY"):
        raise RuntimeError("skipped: set YOUTUBE_API_KEY to enable")
    raise NotImplementedError("YouTube collector is planned once a key is provided")


def x_twitter(f):
    if not os.environ.get("X_BEARER_TOKEN"):
        raise RuntimeError("skipped: set X_BEARER_TOKEN to enable")
    raise NotImplementedError("X collector is planned once a key is provided")


COLLECTORS = {
    "reddit": reddit, "4chan": fourchan, "gdelt": gdelt, "google_news": google_news, "hackernews": hackernews,
    "mastodon": mastodon, "bluesky": bluesky, "medium": medium, "wordpress": wordpress,
    "youtube": youtube, "x": x_twitter,
}
