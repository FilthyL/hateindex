# Indian Hate Index

An open, transparent index of **online hostility toward Indians**, by country.
It tracks where the hostility comes from, **why** (economic, immigration,
disgust, fraud…) and **which stereotypes** people repeat. Hover over any
country on the map to see its breakdown.

- **Definition of hate**, the severity ladder, sarcasm handling and scoring: [`docs/DEFINITION.md`](docs/DEFINITION.md)
- **Background research**: why people hate racial groups, the common sentiment toward Indians, and stereotypes vs reality: [`docs/RESEARCH.md`](docs/RESEARCH.md)

## How it works

```
public sources ──► collectors ──► data/raw/*.jsonl.gz (data branch) ──► classifier ──► per-author averages ──► site/data/index.json ──► map
```

1. **Collect** (`pipeline/hateindex/collectors.py`): keyless public sources only.

   | Source | Type | Country from |
   |---|---|---|
   | 4chan /pol/, /int/, /bant/, /sp/ (official API; every changed live thread, hourly) | social | IP-based post flag |
   | Reddit (~60 country subreddits; public JSON, or [PullPush](https://pullpush.io) when reddit.com blocks) | social | subreddit |
   | Mastodon (public tag timelines) | social | instance (local accounts only) |
   | Hacker News (Algolia API) | social | — (global only) |
   | Bluesky (public AppView search) | social | — (global only) |
   | GDELT DOC 2.0 | news | outlet country |
   | Google News RSS (24 English editions) | news | edition |
   | Medium tag feeds, WordPress.com tags | blogs | — (global only) |
   | YouTube, X | — | stubs; enabled when API keys are added as secrets |

   Usernames are replaced with salted hashes before anything is stored.
2. **Classify** (`classify.py`, `taxonomy.py`): a transparent rule-based classifier.
   It checks the target (Indians as people, not the Indian state), then
   severity 0–4, then reasons and stereotypes. Sarcasm is excluded; counter-speech
   and negations count as non-hateful.
3. **Aggregate** (`aggregate.py`): each author's posts are averaged, then authors
   are averaged per country, with small-sample shrinkage. There are three
   layers: **people** (social media), **media** (news) and **combined**.
4. **Publish**: a static site (`site/`) with a D3 world map, deployed to GitHub Pages.

## Run locally

```bash
python -m pipeline.hateindex collect                      # all sources
```

```bash
python -m pipeline.hateindex collect --sources 4chan,gdelt
```

```bash
python -m pipeline.hateindex build
```

```bash
python -m http.server -d site 8000                        # open http://localhost:8000
```

```bash
python -m pipeline.hateindex classify "Indians are all scammers"
```

```bash
cd pipeline && python -m unittest discover -s tests
```

Only the Python 3.10+ standard library is needed.

## Deploy (GitHub Pages)

The workflow `.github/workflows/collect-and-deploy.yml` runs **hourly**. It collects,
rebuilds the index and deploys `site/` to Pages. Raw posts and collector progress
are saved to the `data` branch as a single commit that's overwritten each run, so
`main`'s history doesn't fill up with data.

1. Repo **Settings → Pages → Source: GitHub Actions**.
2. Optional: add a `HATEINDEX_SALT` secret (any random string) for the author hashes.
3. **Actions → Collect data and deploy site → Run workflow** for the first run.

Later, add `YOUTUBE_API_KEY` / `X_BEARER_TOKEN` secrets and implement those collectors.

## Limitations

This measures people who post publicly online, in English, about Indians. It
is not a poll of any country's population. Geolocation is imperfect, and some
sources (Reddit in particular) may block or rate-limit unauthenticated requests
from cloud IPs. Each source's status is shown on the site.
