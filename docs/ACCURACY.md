# How accurate is the index?

Every number on the site comes from a rule-based classifier, so the real
question is how often it agrees with a careful human reader. We measure that
on posts from the collected data, labelled by hand and blind: who the post is
about, and severity 0–4 on the ladder in [DEFINITION.md](DEFINITION.md).

| Sample | Posts | How it was drawn | Precision | Recall | "About Indians" correct |
|---|---|---|---|---|---|
| `tests/eval/labels.jsonl` (tuning) | 130 | half from posts the classifier flagged | 0.83 | 0.82 | 0.92 |
| `tests/eval/holdout.jsonl` (2nd round of tuning) | 100 | keyword match, not the classifier | 1.00 | 0.73 | 0.62 |
| **`tests/eval/test.jsonl` (never tuned on)** | **80** | keyword match | **0.83** | **0.25** | 0.70 |

The first version of the classifier scored 0.60 precision and 0.15 recall on
the untouched test set. The current one scores 0.83 and 0.25.

**Precision** is how many flagged posts really are hostile. **Recall** is how
many hostile posts get flagged. Reproduce with
`python -m pipeline.hateindex.evaluate pipeline/tests/eval/test.jsonl`.

## What this means

- **Explicit hostility is measured fairly reliably.** That's slurs, "deport them",
  "they're rats", "Indians are scammers". When the index flags something, it's
  usually right.
- **Most hostility is missed.** The test set's misses are almost all *implicit*:
  mock-accent jokes ("BLOODY BENCHOD POLLS"), tropes ("total izzat
  catastrophe"), insults aimed at an Indian poster that never say "Indian"
  ("your inbred brothers are waiting for you"), and quiet workplace stereotypes.
  Word lists can't see these. The target only comes from the thread.
- **So the index is a floor, and an uneven one.** How much gets missed depends
  on the platform, and every country's data comes from a different mix of
  platforms. Treat country differences as signals worth looking into, not as
  measured gaps.
- **"Hate" needs judgement.** Labelling 310 posts meant many borderline calls
  (is "Indians hire other Indians" a stereotype or an observation?). These
  labels are one careful reader's calls, not ground truth.

## What would do better

A classifier that reads context, meaning a large language model given the
definition as a rubric, plus the thread each reply belongs to. The labelled
sets above are there to test any replacement against these same numbers before
it's trusted.
