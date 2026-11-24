# Setting up Facebook + Instagram auto-publishing (reusable guide)

Use this to set up the same structure for another brand or client. Total cost: free (the Meta Graph API has no fees; only ad spend costs money). Time: about 30–45 minutes the first time.

## 1. Accounts you need

- A Facebook **Page**, with your personal Facebook account as a full admin (or the Page in a Meta Business portfolio you manage).
- An Instagram **professional** account (Business or Creator) **linked to that Page** (Instagram app → Settings → Account type and tools / Business tools → connect to Facebook Page).
- A GitHub account with a **public** repository for the images (Instagram must fetch images without logging in). Never commit tokens.

## 2. Create the Meta app (once)

1. developers.facebook.com → **Get started** (register as a developer) → **My Apps → Create App**.
2. Use case **Other** → app type **Business**. Name it e.g. "<Brand> Publisher".
3. **Use cases → Add use case → "Manage everything on your Page"** → Customize → add `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`.
4. **Add use case → "Manage messaging & content on Instagram"** → choose **API setup with Facebook login** (not "Instagram login": those `instagram_business_*` permissions use tokens that expire every 60 days) → add `instagram_basic`, `instagram_content_publish`.
5. `business_management` is also needed when the Page is owned by a Business portfolio.

Gotcha we hit: permissions only appear in Graph API Explorer after the matching use case is added. Refresh the Explorer after adding them.

## 3. Get a Page token that does not expire

1. **Tools → Graph API Explorer** → select your app → add all six permissions above → **Generate Access Token** → click **Edit access** → tick the business portfolio, the Page and the Instagram account → Done.
2. **Tools → Access Token Debugger** → paste → **Extend Access Token** → copy the long-lived user token.
3. Paste it back in the Explorer, run `me/accounts`, and copy the **`access_token` inside the Page's entry** (not the one in the top box). That is the Page token.
4. Check it in the Debugger: **Type: Page**, **Expires: Never**.

Gotchas we hit:
- Saving the top-box token instead of the Page token: posting then fails. `GET /me` must return the **Page** id and name.
- `me/accounts` returns `[]` when `business_management` was not granted or the Page was not ticked under **Edit access**.

## 4. Store the token safely

- Claude cloud: save it as an environment network secret for host `graph.facebook.com` (Claude asks with a secure form). The proxy adds it to requests; scripts never see it.
- Elsewhere: export `FB_PAGE_TOKEN` only in the shell or CI secret store. Never commit it.

Verify (read-only):
```bash
curl -sS -g "https://graph.facebook.com/v21.0/me?fields=id,name,instagram_business_account{id,username}"
curl -sS "https://graph.facebook.com/v21.0/<IG_USER_ID>/content_publishing_limit?fields=quota_usage,config"
```
The second call fails with "Requires instagram_content_publish" until step 2.4 is done.

## 5. Images

- Export posts as **JPEG**, 1080×1350 (4:5) for feed. Instagram rejects PNG and WebP from the API.
- Commit them under `assets/organic/<yyyy-mm>/`, push, and use a raw URL **pinned to the commit**:
  `https://raw.githubusercontent.com/<owner>/<repo>/<commit-sha>/<path>`
- Avoid hosts that return a viewer page or expire (Google Drive, Dropbox share links, signed CDN links), and WordPress sites that silently convert uploads to WebP.

## 6. Schedule

- Fill `schedule/organic.json` (times in Singapore time with `+08:00`).
- The Instagram API cannot schedule ahead, and the Facebook API schedules only about 30 days ahead, so publishing is triggered at post time by a scheduled task (e.g. a Claude scheduled task per post) that runs:
  ```bash
  python3 scripts/publish.py --schedule schedule/organic.json --item N --image-base <pinned raw base>
  ```
- Always run with `--dry-run` once after setup: it checks the image URL, the token's Page and the Instagram quota (100 API posts per 24 h) without posting.

## 7. Captions

- Facebook: links are clickable, so guide posts end with the article URL.
- Instagram: links are not clickable, so use "Full guide: <site>/blog (link in bio)" and keep the bio link pointing at the blog or a link page.
