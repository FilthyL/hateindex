"""Regression guard: rule changes must not make the classifier worse on the labelled sets."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hateindex.evaluate import evaluate

EVAL = os.path.join(os.path.dirname(__file__), "eval")


class Accuracy(unittest.TestCase):
    def check(self, name, min_precision, min_recall):
        stats, _, _ = evaluate(os.path.join(EVAL, name))
        self.assertGreaterEqual(stats["precision"], min_precision, stats)
        self.assertGreaterEqual(stats["recall"], min_recall, stats)

    def test_tuning_set(self):
        self.check("labels.jsonl", 0.80, 0.80)

    def test_holdout_set(self):
        self.check("holdout.jsonl", 0.95, 0.70)

    def test_untouched_test_set(self):
        # deliberately low recall: see docs/ACCURACY.md. Raise these as the classifier improves.
        self.check("test.jsonl", 0.80, 0.25)


if __name__ == "__main__":
    unittest.main()
