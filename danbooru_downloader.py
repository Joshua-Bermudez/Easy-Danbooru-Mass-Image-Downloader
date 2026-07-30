#!/usr/bin/env python3
"""

Usage:
    python danbooru_downloader.py
    python danbooru_downloader.py --tags tag tag --limit 5
    python danbooru_downloader.py --rating safe --out ./downloads

"""

import argparse
import os
import sys
import time
import requests

BASE_URL = "https://danbooru.donmai.us"
POSTS_ENDPOINT = f"{BASE_URL}/posts.json"


ALLOWED_EXTENSIONS = {"mp4","gif"} # Change file type Here


def build_session(login: str | None, api_key: str | None) -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "danbooru-downloader-script/1.0"})
    if login and api_key:
        session.auth = (login, api_key)
    return session


def fetch_posts(session, tags, limit, rating, page_limit_per_request=200):
    
    posts = []
    last_id = None
    tag_query = " ".join(tags)

    if rating:
        tag_query += f" rating:{rating}"

    max_retries = 5

    while len(posts) < limit:
        remaining = limit - len(posts)
        params = {
            "tags": tag_query,
            "limit": min(page_limit_per_request, remaining),
        }
        if last_id is not None:
            params["page"] = f"b{last_id}"  # "before" this post id

        for attempt in range(max_retries):
            resp = session.get(POSTS_ENDPOINT, params=params, timeout=30)
            if resp.status_code == 429:
                wait = 5 * (attempt + 1)
                print(f"Rate limited, sleeping {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            break
        else:
            print("Too many failed retries, stopping fetch.")
            break

        batch = resp.json()
        if not batch:
            break  # no more results available

        # Cursor must advance based on the full batch (not the filtered
        # one) so pagination doesn't get stuck re-fetching the same page.
        last_id = batch[-1]["id"]

        filtered = [p for p in batch if (p.get("file_ext") or "").lower() in ALLOWED_EXTENSIONS]
        posts.extend(filtered)

        print(f"  Fetched {len(posts)}/{limit} matching post records so far "
              f"({len(batch) - len(filtered)} skipped this page for file type)...")

        # be polite to the API
        time.sleep(0.5)

    return posts[:limit]


def download_image(session, post, out_dir):
    """
    Download the full-size (or largest available) image for a post.
    """
    file_url = post.get("file_url") or post.get("large_file_url")
    if not file_url:
        print(f"  Skipping post {post.get('id')}: no downloadable file URL "
              f"(may be a restricted/deleted post).")
        return False

    post_id = post.get("id")
    ext = (post.get("file_ext") or "").lower()

    if ext not in ALLOWED_EXTENSIONS:
        print(f"  Skipping post {post_id}: file type '.{ext}' not in allowed list {sorted(ALLOWED_EXTENSIONS)}.")
        return False
    filename = f"{post_id}.{ext}"
    filepath = os.path.join(out_dir, filename)

    if os.path.exists(filepath):
        print(f"  Already have {filename}, skipping.")
        return True

    resp = session.get(file_url, stream=True, timeout=60)
    resp.raise_for_status()

    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"  Downloaded {filename}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Download images from Danbooru by tag.")
    parser.add_argument(
        "--tags", nargs="+", default=["genshin_impact", "absurdres"], # Change tags here
       
    )
    parser.add_argument("--limit", type=int, default=25, help="Max number of images to download")
    parser.add_argument(
        "--rating", choices=["general", "sensitive", "questionable", "explicit"],
        default="explicit", # Change ratings here
        help="Restrict by content rating (default: general/safe-for-work only)"
    )
    parser.add_argument("--out", default="./danbooru_downloads", help="Output directory")
    parser.add_argument("--login", default=None, help="Danbooru username (optional, for higher rate limits)")
    parser.add_argument("--api-key", default=None, help="Danbooru API key (optional)")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    session = build_session(args.login, args.api_key)

    print(f"Searching Danbooru for tags: {args.tags} (rating={args.rating})")
    posts = fetch_posts(session, args.tags, args.limit, args.rating)
    print(f"Found {len(posts)} posts. Starting download...\n")

    success = 0
    skipped = 0
    failed = 0
    for i, post in enumerate(posts, start=1):
        print(f"[{i}/{len(posts)}] Post ID {post.get('id')}")
        try:
            result = download_image(session, post, args.out)
            if result:
                success += 1
            else:
                skipped += 1
        except requests.RequestException as e:
            print(f"  Failed to download post {post.get('id')}: {e}")
            failed += 1
        time.sleep(0.3)  # polite delay between downloads

    print(
        f"\nDone. {success} downloaded, {skipped} skipped (wrong file type / "
        f"unavailable), {failed} failed. Out of {len(posts)} matched posts. "
        f"Saved to '{args.out}'."
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nInterrupted by user.")
