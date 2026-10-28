#!/usr/bin/env python3
"""Weekly GitHub Release of the free 100-row sample (judge 2026-10-28, loop 3). Stdlib only.

    python3 release.py             create this week's release (skips if the tag already exists), then ping IndexNow + Bing
    python3 release.py --dry-run   print the tag, title, body and asset; create nothing, ping nothing

Runs from the Monday 08:30 UTC cron right after update_sample.py and its git push (so the tag points at the pushed commit):
  tag    week-<week_ending>          (counts.json of the newest weekly file)
  title  New USDOT carriers, week ending <date>: <N> carriers
  body   short changelog: the file's count, the top 10 states with links to their pages on rasengan.win, links to every
         state page, and "Watch -> Releases" to get notified
  asset  sample/new-usdot-carriers-sample.csv (the 100 rows just pushed)
Then pings IndexNow (pipelines/push_d1.py ping_indexnow) and Bing Webmaster SubmitUrlBatch with the 51 state pages and
/new-dot-leads/. The release URL itself is on github.com, which neither API accepts for our site; it is logged instead.
Idempotent: when the tag exists nothing is created and nothing is pinged. Refuses to run when the sample does not come
from the same file as counts.json. Token: data/secrets/github_token (never printed)."""
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRODUCT = ROOT / "ventures/15/products/new-usdot-registrations-weekly"
SAMPLE = HERE / "sample" / "new-usdot-carriers-sample.csv"
README = HERE / "README.md"
STATES_JSON = ROOT / "company/site/new-dot-leads/states.json"
REPO = "rasenganwin-tech/new-dot-numbers-weekly"
API = "https://api.github.com"
SITE = "https://rasengan.win"
UA = "rasengan-release/1 (+https://rasengan.win/new-dot-leads/)"


def gh(method, url, body=None, ctype="application/json", ok404=False):
    token = (ROOT / "data/secrets/github_token").read_text().strip()
    data = body if isinstance(body, (bytes, type(None))) else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA, **({"Content-Type": ctype} if data is not None else {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if ok404 and e.code == 404:
            return None
        raise SystemExit(f"GitHub {method} {url.split('?')[0]}: HTTP {e.code} {e.read()[:300].decode('utf-8', 'replace')}")


def nice(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d:%b} {d.day}, {d.year}"


def facts():
    """counts.json of the newest weekly file, checked against the newest zip and the sample's README line."""
    c = json.loads((PRODUCT / "counts.json").read_text())
    zips = sorted(PRODUCT.glob("New USDOT carriers * to *.zip"))
    if not zips or f"{c['window_start']} to {c['window_end']}" not in zips[-1].name:
        sys.exit("counts.json does not describe the newest weekly zip; not releasing")
    if f"{c['window_start']} to {c['window_end']}" not in README.read_text() or not SAMPLE.exists():
        sys.exit("the sample is not from this week's file (README SAMPLE line); run update_sample.py first; not releasing")
    pages = {e["abbr"]: e for e in json.loads(STATES_JSON.read_text())}
    return c, pages


def body_for(c, pages):
    url = lambda e: f"{SITE}/new-dot-leads/{e['slug']}/?ref=github"
    by = c.get("by_state", {})
    top = sorted((st for st in pages if by.get(st)), key=lambda st: (-by[st], st))[:10]
    lines = [f"This week's file has **{c['rows']:,}** new motor carriers: every carrier that registered for a USDOT number "
             f"from {nice(c['query_start'])} to {nice(c['week_ending'])} and was not in an earlier weekly file "
             f"(public FMCSA Motor Carrier Census).", "",
             "The attached CSV is this week's free 100-row sample, every column (a few personal fields partly hidden).", "",
             "### Top 10 states this week", ""]
    lines += [f"{i}. [{pages[st]['state']}]({url(pages[st])}): {by[st]:,}" for i, st in enumerate(top, 1)]
    lines += ["", "### Every state page", "",
              " · ".join(f"[{e['state']}]({url(e)}) ({by.get(st, 0):,})" for st, e in sorted(pages.items(), key=lambda kv: kv[1]["state"])), "",
              f"Full weekly file (every row, unmasked): {SITE}/new-dot-leads/?ref=github", "",
              "To get a note every Monday: **Watch → Custom → Releases** on this repository.", "",
              "Rasengan Data is not affiliated with FMCSA or the US Department of Transportation."]
    return "\n".join(lines)


def ping(urls):
    """IndexNow (pipelines/push_d1.py) and Bing SubmitUrlBatch. Returns a short status string; never raises."""
    out = []
    try:
        sys.path.insert(0, str(ROOT / "pipelines"))
        from push_d1 import ping_indexnow
        sent, pending = ping_indexnow(urls)
        out.append(f"indexnow sent {sent}, pending {len(pending)}")
    except Exception as e:
        out.append(f"indexnow failed: {type(e).__name__}")
    try:
        key = (ROOT / "data/secrets/bing_api_key").read_text().strip()
        req = urllib.request.Request(f"https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlBatch?{urllib.parse.urlencode({'apikey': key})}",
                                     data=json.dumps({"siteUrl": f"{SITE}/", "urlList": urls}).encode(), method="POST",
                                     headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            out.append(f"bing SubmitUrlBatch HTTP {r.status} ({len(urls)} urls)")
    except urllib.error.HTTPError as e:
        out.append(f"bing SubmitUrlBatch HTTP {e.code} {e.read()[:200].decode('utf-8', 'replace')}")
    except Exception as e:
        out.append(f"bing SubmitUrlBatch failed: {type(e).__name__}")
    return "; ".join(out)


def main():
    dry = "--dry-run" in sys.argv[1:]
    stamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    c, pages = facts()
    tag = f"week-{c['week_ending']}"
    title = f"New USDOT carriers, week ending {nice(c['week_ending'])}: {c['rows']:,} carriers"
    body = body_for(c, pages)
    asset = f"new-usdot-carriers-sample-week-ending-{c['week_ending']}.csv"
    urls = [f"{SITE}/new-dot-leads/"] + [f"{SITE}/new-dot-leads/{e['slug']}/" for e in sorted(pages.values(), key=lambda e: e["state"])]
    try:
        existing = gh("GET", f"{API}/repos/{REPO}/releases/tags/{tag}", ok404=True)
    except SystemExit as e:
        if not dry:
            raise
        existing = None
        print(f"(dry run) tag check failed: {e}")
    if existing:
        print(f"{stamp} release: {tag} already exists ({existing.get('html_url')}); nothing to do")
        return 0
    if dry:
        print(f"{stamp} release DRY RUN: would create {tag} on {REPO} (target main)\ntitle: {title}\n"
              f"asset: {asset} ({SAMPLE.stat().st_size:,} bytes)\nwould ping {len(urls)} urls (IndexNow + Bing)\n--- body ---\n{body}")
        return 0
    rel = gh("POST", f"{API}/repos/{REPO}/releases", {"tag_name": tag, "target_commitish": "main", "name": title, "body": body,
                                                      "draft": False, "prerelease": False})
    up = rel["upload_url"].split("{")[0] + "?" + urllib.parse.urlencode({"name": asset, "label": "Free 100-row sample (CSV)"})
    a = gh("POST", up, SAMPLE.read_bytes(), ctype="text/csv")
    print(f"{stamp} release: created {rel['html_url']} with {a.get('name')} ({a.get('size')} bytes)")
    print(f"{stamp} release: {ping(urls)}; release URL (github.com, not submittable for our site): {rel['html_url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
