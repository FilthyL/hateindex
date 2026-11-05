# What counts as "hate" in this index

The index measures **hostility toward Indians as people**: people of Indian
origin, including the diaspora. It does **not** measure criticism of the Indian
state, its government, its policies, its cricket team or its films. Counting
those as racism would make the index meaningless.

## Severity ladder

Every post that is about Indians gets a severity level from 0 to 4.

| Level | Name | What it looks like | Weight |
|---|---|---|---|
| 0 | Neutral / critique | News, questions, praise, criticism of a policy or government | 0.00 |
| 1 | Negative stereotyping | Stating a stereotype as true of the group ("Indians are all scammers") | 0.25 |
| 2 | Contempt / slurs | Mockery, disgust, insults or slurs aimed at the group | 0.50 |
| 3 | Dehumanisation | Comparing Indians to animals, vermin, disease or filth | 0.75 |
| 4 | Exclusion / violence | Calls to deport, ban, expel, attack or kill Indians | 1.00 |

A post's severity is the **highest** level it reaches.

## A post counts as hate only if all of these hold

1. **Target:** it is about Indians as a *group*, or attacks someone *for being
   Indian*. A post about the Indian government or a policy doesn't qualify.
2. **Sincere:** it is not sarcastic or ironic (see below).
3. **Endorsed:** it is not counter-speech. Quoting a stereotype to condemn it
   ("it's racist to say Indians smell") is not hate.
4. **Not negated:** "Indians are *not* scammers" and "not all Indians…" are not
   endorsements.

## Sarcasm: excluded entirely

Sarcastic posts are **removed from both the numerator and the denominator**.
We can't reliably tell whether a sarcastic post mocks Indians or mocks racists,
so we don't guess. Signals the pipeline looks for:

- Explicit markers: `/s`, `#sarcasm`, `(sarcasm)`
- Ironic set phrases: "yeah right", "oh sure", "sure, because…", "as if",
  "said no one ever", "totally not racist"
- Irony emoji (🙄 🙃 😏 🤡) on a post that also has strong positive wording
- Scare-quoted stereotype words (`Indians are "scammers"`)

The share of posts removed as sarcasm is published for every country, so you
can see how much was dropped.

## From posts to a country score ("average of the people")

1. Each post gets a weight from the table above.
2. **Average per author first.** One account posting 500 slurs counts as one
   person, not 500. An author's score is the mean weight of their posts.
3. **Raw country score** = mean author score × 100 (0–100).
4. **Small-sample shrinkage.** Countries with few authors are pulled toward the
   global average: `adjusted = (n·raw + k·global) / (n + k)`, with `k = 30`.
   Without this, a country with three angry posters would top the chart.
5. **Confidence** is reported: `low` (< 50 authors), `medium` (< 300),
   `high` (≥ 300). Countries with fewer than 10 authors show as
   "insufficient data".

## Where the country comes from

| Source | How a country is assigned |
|---|---|
| 4chan /pol/, /int/, /bant/, /sp/ | The country flag the board shows on each post (IP-based) |
| Reddit (direct, PullPush or Arctic Shift) | The country subreddit it was posted in (r/canada → Canada, …) |
| GDELT news | The country of the news outlet |
| Google News RSS | The country edition the article was listed in |
| Mastodon, Lemmy | The country of the instance, where it has one (local accounts only) |
| Hacker News, Bluesky, Medium, WordPress blogs | No country. These count toward the **global** reasons and stereotypes only |

## What the index is not

- It is **not** a measure of how a country's population feels. It measures
  people who *post online* about Indians, in English, which is a skewed sample.
- Geolocation is imperfect: VPNs, the diaspora, bots.
- The classifier is rule-based. It misses coded language and misreads some
  context. Treat the breakdowns of reasons and stereotypes as *signals*, not
  verdicts.
