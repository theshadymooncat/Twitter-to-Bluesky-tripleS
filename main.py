import os
import json
import feedparser
from atproto import Client

NITTER_RSS = "https://nitter.net/official_artms/rss"
BLUESKY_HANDLE = os.environ["BLUESKY_HANDLE"]
BLUESKY_PASSWORD = os.environ["BLUESKY_PASSWORD"]
STATE_FILE = "seen_ids.json"

def load_seen():
    try:
        return set(json.load(open(STATE_FILE)))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_seen(seen):
    with open(STATE_FILE, "w") as f:
        json.dump(list(seen), f)

def fetch_tweets():
    feed = feedparser.parse(NITTER_RSS)
    tweets = []
    for entry in feed.entries[:10]:
        if entry.title.startswith("RT by") or entry.title.startswith("R to"):
            continue
        tweet_id = entry.link.split("/status/")[1].split("#")[0]
        tweets.append({"id": tweet_id, "text": entry.title})
    print(f"Fetched {len(tweets)} tweets")
    return tweets

def post_to_bluesky(text):
    try:
        bsky = Client()
        bsky.login(BLUESKY_HANDLE, BLUESKY_PASSWORD)
        bsky.send_post(text=text[:300])
        print("Posted to Bluesky:", text[:60])
    except Exception as e:
        print(f"Error posting to Bluesky: {e}")

def main():
    seen = load_seen()
    tweets = fetch_tweets()
    for tw in reversed(tweets):
        if tw["id"] in seen:
            continue
        print("Reposting:", tw["text"][:80])
        post_to_bluesky(tw["text"])
        seen.add(tw["id"])
    save_seen(seen)

if __name__ == "__main__":
    main()
