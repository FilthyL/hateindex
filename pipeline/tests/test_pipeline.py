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


if __name__ == "__main__":
    unittest.main()
