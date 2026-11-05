"""Offline tests: collectors parse canned API responses; aggregation scores them."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hateindex import collectors as C
from hateindex.aggregate import build


class FakeFetcher:
    def __init__(self, routes):
        self.routes = routes

    def get(self, url, headers=None, as_json=True):
        for prefix, body in self.routes.items():
            if url.startswith(prefix):
                return body
        raise RuntimeError(f"unexpected url {url}")


CATALOG = [{"threads": [{"no": 1, "sub": "Why are there so many Indians in Canada", "com": "thoughts?"},
                        {"no": 2, "sub": "cats", "com": "post cats"}]}]
THREAD = {"posts": [
    {"no": 1, "id": "a", "country": "CA", "com": "Why are there so many Indians in Canada", "time": 1700000000},
    {"no": 3, "id": "b", "country": "CA", "com": "they are vermin, deport them all", "time": 1700000100},
    {"no": 4, "id": "c", "country": "GB", "com": "Yeah right, indians are the problem /s", "time": 1700000200},
    {"no": 5, "id": "d", "troll_country": "EU", "com": "pajeets lol", "time": 1700000300},
]}


class Collectors(unittest.TestCase):
    def test_fourchan(self):
        f = FakeFetcher({"https://a.4cdn.org/pol/catalog.json": CATALOG, "https://a.4cdn.org/pol/thread/1.json": THREAD})
        recs = list(C.fourchan(f, boards=("pol",)))
        self.assertEqual(len(recs), 4)
        self.assertEqual(recs[1]["country"], "CA")
        self.assertIsNone(recs[3]["country"])        # troll flag ignored
        self.assertNotIn("b", recs[1]["author"])      # hashed
        self.assertIn("Indians", recs[1]["context"])

    def test_reddit(self):
        listing = {"data": {"children": [{"data": {"id": "x1", "name": "t3_x1", "title": "Indians are all scammers",
                                                    "selftext": "", "author": "u1", "num_comments": 1,
                                                    "permalink": "/r/canada/x1", "created_utc": 1700000000}}]}}
        thread = [{}, {"data": {"children": [{"kind": "t1", "data": {"name": "t1_c1", "body": "send them back",
                                                                      "author": "u2", "permalink": "/c1", "replies": ""}}]}}]
        f = FakeFetcher({"https://www.reddit.com/r/canada/search.json": listing,
                         "https://www.reddit.com/r/canada/comments/x1.json": thread})
        recs = list(C.reddit(f, subs={"canada": "CA"}))
        self.assertEqual([r["country"] for r in recs], ["CA", "CA"])
        self.assertEqual(recs[1]["context"], "Indians are all scammers")


class FourchanIncremental(unittest.TestCase):
    CAT = [{"threads": [{"no": 7, "sub": "cats", "com": "post cats", "last_modified": 100}]}]
    OFFTOPIC = {"posts": [
        {"no": 7, "id": "a", "country": "US", "com": "post cats"},
        {"no": 8, "id": "b", "country": "GB", "com": "jeets ruin every thread"},
        {"no": 9, "id": "c", "country": "DE", "com": "nice cat"},
    ]}

    def fetcher(self):
        return FakeFetcher({"https://a.4cdn.org/pol/catalog.json": self.CAT,
                            "https://a.4cdn.org/pol/thread/7.json": self.OFFTOPIC})

    def test_offtopic_thread_keeps_only_matching_posts(self):
        recs = list(C.fourchan(self.fetcher(), boards=("pol",), state={}))
        self.assertEqual([r["country"] for r in recs], ["GB"])
        self.assertEqual(recs[0]["context"], "")

    def test_unchanged_thread_not_refetched(self):
        state = {}
        list(C.fourchan(self.fetcher(), boards=("pol",), state=state))
        self.assertEqual(state["pol"]["7"], 100)
        f = FakeFetcher({"https://a.4cdn.org/pol/catalog.json": self.CAT})  # thread URL would raise
        self.assertEqual(list(C.fourchan(f, boards=("pol",), state=state)), [])

    def test_dead_threads_forgotten(self):
        state = {"pol": {"1": 5}}
        list(C.fourchan(self.fetcher(), boards=("pol",), state=state))
        self.assertNotIn("1", state["pol"])


class RedditFallback(unittest.TestCase):
    def test_pullpush_when_blocked(self):
        import urllib.error

        class F(FakeFetcher):
            def get(self, url, headers=None, as_json=True):
                if url.startswith("https://www.reddit.com/"):
                    raise urllib.error.HTTPError(url, 403, "Blocked", {}, None)
                return super().get(url, headers, as_json)

        body = {"data": [{"id": "c1", "body": "Indians are all scammers", "author": "u", "created_utc": 1700000500,
                          "permalink": "/r/canada/c1"}]}
        f = F({"https://api.pullpush.io/": body})
        f.min_interval = 0
        state = {}
        recs = list(C.reddit(f, subs={f"s{i}": "CA" for i in range(5)}, state=state))
        self.assertTrue(recs)
        self.assertEqual(recs[0]["country"], "CA")
        self.assertEqual(state["s0:comment"], 1700000500)


class Lemmy(unittest.TestCase):
    def test_local_users_get_instance_country(self):
        body = {"comments": [
            {"comment": {"ap_id": "https://lemmy.ca/comment/1", "content": "Indians are all scammers"},
             "creator": {"actor_id": "https://lemmy.ca/u/a", "local": True}, "post": {"name": "thread"}},
            {"comment": {"ap_id": "https://lemmy.world/comment/2", "content": "send them back"},
             "creator": {"actor_id": "https://lemmy.world/u/b", "local": False}, "post": {"name": "Indians in Canada"}},
        ]}
        f = FakeFetcher({"https://lemmy.ca/api/v3/search": body, "https://": {"comments": [], "posts": []}})
        recs = [r for r in C.lemmy(f, terms=("indians",)) if r["id"].startswith("lemmy:https://lemmy.")]
        self.assertEqual([r["country"] for r in recs], ["CA", None])
        self.assertEqual(recs[1]["context"], "Indians in Canada")


class ArcticFallback(unittest.TestCase):
    def test_arctic_when_pullpush_down(self):
        import urllib.error

        class F(FakeFetcher):
            def get(self, url, headers=None, as_json=True):
                if url.startswith("https://www.reddit.com/"):
                    raise urllib.error.HTTPError(url, 403, "Blocked", {}, None)
                if url.startswith("https://api.pullpush.io/"):
                    raise C.HostDown("api.pullpush.io")
                return super().get(url, headers, as_json)

        body = {"data": [{"id": "c9", "body": "deport all indians", "author": "u", "created_utc": 1700000900}]}
        f = F({"https://arctic-shift.photon-reddit.com/": body})
        f.min_interval = 0
        state = {}
        recs = list(C.reddit(f, subs={f"s{i}": "GB" for i in range(5)}, state=state))
        self.assertTrue(recs)
        self.assertEqual(recs[0]["country"], "GB")
        self.assertEqual(state["arctic:s0:comment"], 1700000900)


class Aggregate(unittest.TestCase):
    def test_build(self):
        f = FakeFetcher({"https://a.4cdn.org/pol/catalog.json": CATALOG, "https://a.4cdn.org/pol/thread/1.json": THREAD})
        out = build(list(C.fourchan(f, boards=("pol",))))
        self.assertEqual(out["totals"]["sarcasm_excluded"], 1)
        ca = out["countries"]["CA"]
        self.assertEqual(ca["num"], "124")
        self.assertEqual(ca["layers"]["people"]["authors"], 2)
        self.assertEqual(ca["layers"]["people"]["raw"], 50.0)   # one neutral author, one severity-4 author
        self.assertEqual(ca["layers"]["people"]["confidence"], "insufficient")
        self.assertNotIn("GB", out["countries"])               # only post was sarcasm



class Gdelt(unittest.TestCase):
    def test_plain_text_error_is_reported(self):
        f = FakeFetcher({"https://api.gdeltproject.org/": "Please limit requests to one every 5 seconds"})
        f.min_interval = 0
        with self.assertRaisesRegex(RuntimeError, "limit requests"):
            list(C.gdelt(f))

    def test_articles_parsed(self):
        import json
        body = json.dumps({"articles": [{"url": "https://x.example/a", "title": "Indians are all scammers", "domain": "x.example"}]})
        f = FakeFetcher({"https://api.gdeltproject.org/": body})
        f.min_interval = 0
        recs = list(C.gdelt(f))
        self.assertEqual(recs[0]["country"], "US")
        self.assertEqual(recs[0]["kind"], "news")


class FetcherLimits(unittest.TestCase):
    def test_budget_exceeded(self):
        import time
        f = C.Fetcher(deadline=time.time() - 1)
        with self.assertRaises(C.BudgetExceeded):
            f.get("https://example.invalid/x")

    def test_budget_not_swallowed_by_collectors(self):
        # collectors catch Exception per request; the budget must still stop them
        self.assertFalse(issubclass(C.BudgetExceeded, Exception))

    def test_dead_host_skipped(self):
        f = C.Fetcher(timeout=1, retries=1)
        f._dead.add("down.example")
        with self.assertRaises(C.HostDown):
            f.get("https://down.example/api")


if __name__ == "__main__":
    unittest.main()
