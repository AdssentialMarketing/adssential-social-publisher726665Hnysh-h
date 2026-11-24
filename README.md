# Adssential Social Publisher

Assets, schedule and a small publishing script that post Adssential Marketing's **organic** content to the Facebook Page and the linked Instagram account at the same time.

Paid lead-generation creatives (Lead Leak Check, service offers, retargeting) are **not** here. They are run from Meta Ads Manager.

## What is in the repo

| Path | What it is |
|---|---|
| `assets/organic/<yyyy-mm>/` | Post images, 1080×1350 JPEG (Instagram only accepts JPEG from a public URL) |
| `schedule/organic.json` | One entry per post: publish time (Singapore time), image path, Facebook caption, Instagram caption |
| `scripts/publish.py` | Publishes one schedule item to Facebook and Instagram via the Meta Graph API. `--dry-run` checks without posting |
| `docs/SETUP.md` | How to set the whole thing up again from scratch (Meta app, tokens, hosting, scheduling) |

No tokens, passwords or keys are ever stored in this repository.

## How posting works

1. Images are committed here; Instagram fetches them from `raw.githubusercontent.com` using a URL pinned to a commit, so later edits never change a scheduled post's image.
2. A scheduled task runs at each `publish_at` time and calls:
   ```bash
   python3 scripts/publish.py --schedule schedule/organic.json --item N \
     --image-base https://raw.githubusercontent.com/AdssentialMarketing/adssential-social-publisher726665hnysh-h/<commit>/
   ```
3. The script posts the photo to the Page, then creates and publishes the Instagram post, and prints the links of both. If one fails it reports which, so it can be retried with `--only facebook` or `--only instagram`.

## Current organic schedule

Every ~1.5 weeks, alternating Thursday 12:30 PM and Monday 8:30 PM (SGT). See `schedule/organic.json`.

| # | When | Post |
|---|---|---|
| 1 | Thu 26 Nov 2026, 12:30 PM | Portfolio: GWS Living Art |
| 2 | Mon 7 Dec 2026, 8:30 PM | Guide: GEO audit checklist |
| 3 | Thu 17 Dec 2026, 12:30 PM | Guide: How long to build a website |
| 4 | Mon 28 Dec 2026, 8:30 PM | Portfolio: Mindwaves Hypnotherapy |
| 5 | Thu 7 Jan 2027, 12:30 PM | Guide: Custom website or template |
| 6 | Mon 18 Jan 2027, 8:30 PM | Guide: Does your website need llms.txt? |
| 7 | Thu 28 Jan 2027, 12:30 PM | Portfolio: AscendCare Medical Clinic |
| 8 | Tue 9 Feb 2027, 8:30 PM | Guide: Redesign or refresh |
| 9 | Thu 18 Feb 2027, 12:30 PM | Guide: WordPress vs Shopify vs Wix vs Webflow |
