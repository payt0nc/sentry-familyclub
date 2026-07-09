"""
FamilyClub.jp diary fetcher (text + images)
--------------------------------------------
Workflow:
1. GET the diary detail page with a valid session cookie attached.
2. Detect whether the response contains the real <article> content
   or a membership/registration wall (no valid session).
3. Parse out the post date, body text, and any image URLs embedded
   in the article body.

You must supply your own session cookie string, copied from DevTools
while logged into web.familyclub.jp in your own browser. Never share
this cookie value — it grants access to your account.
"""

import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_URL = "https://web.familyclub.jp"


def fetch_diary(artist_code: str, diary_id: str, session_cookie: str) -> dict:
    """
    artist_code: e.g. 'F2097'
    diary_id: e.g. '281166'
    session_cookie: raw 'Cookie' header value from your authenticated session.
    """
    url = f"{BASE_URL}/s/jwb/diary/{artist_code}/detail/{diary_id}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": session_cookie,  # supply your own; never hard-code/share it
    }

    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    article = soup.select_one("article.article.row") or soup.select_one("article")

    if article is None:
        return {
            "authenticated": False,
            "message": "No article content returned — session cookie may be "
                       "missing/expired, or this diary requires membership access.",
        }

    posted = article.select_one("div.article__posted")
    content = article.select_one("div.article-content.wysiwyg-area")

    image_urls = []
    if content:
        for img in content.select("img"):
            src = img.get("src")
            if src:
                image_urls.append(urljoin(BASE_URL, src))

    return {
        "authenticated": True,
        "title": soup.title.string.strip() if soup.title else None,
        "posted_at": posted.get_text(strip=True) if posted else None,
        "body_text": content.get_text(separator="\n", strip=True) if content else None,
        "image_urls": image_urls,
    }


def download_images(image_urls, session_cookie: str, out_dir: str = "."):
    """Optional helper: download each image URL to out_dir.
    Uses the same session cookie in case images are also access-gated."""
    import os
    headers = {"User-Agent": "Mozilla/5.0", "Cookie": session_cookie}
    saved = []
    for i, img_url in enumerate(image_urls):
        filename = os.path.join(out_dir, img_url.split("/")[-1] or f"image_{i}.jpg")
        r = requests.get(img_url, headers=headers, timeout=10)
        r.raise_for_status()
        with open(filename, "wb") as f:
            f.write(r.content)
        saved.append(filename)
    return saved


if __name__ == "__main__":
    SESSION_COOKIE = "PASTE_HEADER_COOKIES_HERE"

    result = fetch_diary("F2064", "275870", SESSION_COOKIE)

    if result["authenticated"]:
        print("Posted at:", result["posted_at"])
        print("Body:\n", result["body_text"])
        print("Images found:", result["image_urls"])
        # Uncomment to actually save the images locally:
        # saved_files = download_images(result["image_urls"], SESSION_COOKIE)
        # print("Saved:", saved_files)
    else:
        print(result["message"])
