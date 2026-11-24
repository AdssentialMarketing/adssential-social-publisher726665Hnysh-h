#!/usr/bin/env python3
"""Publish one scheduled organic post to a Facebook Page and its linked Instagram account.

Usage:
  python3 publish.py --schedule schedule/organic.json --item 3 --image-base https://raw.githubusercontent.com/OWNER/REPO/COMMIT/
  python3 publish.py ... --dry-run          # check everything, publish nothing
  python3 publish.py ... --only facebook    # or --only instagram

Authentication: no token is stored in this repo. Either
  * run it where a network proxy injects the Page token for graph.facebook.com (Claude cloud
    environment with a saved credential), or
  * set FB_PAGE_TOKEN in the environment (a Page access token with pages_manage_posts,
    pages_read_engagement, instagram_basic, instagram_content_publish).

Instagram fetches the image from a public URL, so --image-base must be publicly reachable and
serve the file as image/jpeg. Exit code 0 = everything requested was published.
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request, urllib.error

def call(method, url, params=None):
    params = dict(params or {})
    tok = os.environ.get("FB_PAGE_TOKEN")
    if tok and tok != "proxy-injected":
        params["access_token"] = tok
    data = None
    if method == "GET":
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            err = json.loads(body).get("error", {})
        except Exception:
            err = {"message": body[:300]}
        raise RuntimeError(f"{e.code} {err.get('type','')} {err.get('code','')}: {err.get('message','')}")

def check_image(url):
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "facebookexternalhit/1.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        ctype = r.headers.get("Content-Type", "")
        size = len(r.read())
    if "jpeg" not in ctype:
        raise RuntimeError(f"image is served as '{ctype}', Instagram needs image/jpeg: {url}")
    return size

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule", required=True)
    ap.add_argument("--item", type=int, required=True)
    ap.add_argument("--image-base", required=True, help="public base URL the image path is appended to")
    ap.add_argument("--only", choices=["facebook", "instagram"])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    s = json.load(open(a.schedule, encoding="utf-8"))
    it = next((x for x in s["items"] if x["n"] == a.item), None)
    if not it:
        sys.exit(f"item {a.item} not found")
    G = f"https://graph.facebook.com/{s.get('graph_api_version','v21.0')}"
    page, ig = s["facebook_page_id"], s["instagram_user_id"]
    img = a.image_base.rstrip("/") + "/" + it["image"]
    out = {"item": it["n"], "id": it["id"], "image": img, "dry_run": a.dry_run}

    size = check_image(img)
    me = call("GET", f"{G}/me", {"fields": "id,name"})
    if me.get("id") != page:
        raise RuntimeError(f"token is for {me}, expected Page {page}")
    out["image_bytes"] = size
    if a.dry_run:
        lim = call("GET", f"{G}/{ig}/content_publishing_limit", {"fields": "quota_usage,config"})
        out["instagram_quota"] = lim.get("data")
        out["ok"] = True
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    results, failed = {}, False
    if a.only in (None, "facebook"):
        try:
            r = call("POST", f"{G}/{page}/photos", {"url": img, "message": it["facebook_caption"], "published": "true"})
            pid = r.get("post_id") or r.get("id")
            results["facebook"] = {"ok": True, "post_id": pid, "url": f"https://www.facebook.com/{pid}"}
        except Exception as e:
            results["facebook"] = {"ok": False, "error": str(e)}; failed = True
    if a.only in (None, "instagram"):
        try:
            c = call("POST", f"{G}/{ig}/media", {"image_url": img, "caption": it["instagram_caption"]})
            cid = c["id"]
            for _ in range(30):
                st = call("GET", f"{G}/{cid}", {"fields": "status_code"}).get("status_code")
                if st == "FINISHED":
                    break
                if st in ("ERROR", "EXPIRED"):
                    raise RuntimeError(f"container status {st}")
                time.sleep(4)
            p = call("POST", f"{G}/{ig}/media_publish", {"creation_id": cid})
            link = call("GET", f"{G}/{p['id']}", {"fields": "permalink"}).get("permalink")
            results["instagram"] = {"ok": True, "media_id": p["id"], "url": link}
        except Exception as e:
            results["instagram"] = {"ok": False, "error": str(e)}; failed = True
    out["results"] = results
    out["ok"] = not failed
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(1)
