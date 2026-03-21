import os
import json
import asyncio
from twscrape import API, gather
from atproto import Client

STATE_FILE = 'seen_ids.json'

def load_seen():
    try:
        return set(json.load(open(STATE_FILE)))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_seen(seen):
    with open(STATE_FILE, 'w') as f:
        json.dump(list(seen), f)

async def fetch_tweets():
    api = API()
    await api.pool.add_account(
        username=os.environ['TWITTER_USERNAME'],
        password=os.environ['TWITTER_PASSWORD'],
        email=os.environ.get('TWITTER_EMAIL', ''),
        email_password=os.environ.get('TWITTER_EMAIL_PASSWORD', '')
    )
    await api.pool.login_all()

    handle = os.environ['TWITTER_HANDLE']
    user = await api.user_by_login(handle)
    if not user:
        print(f"Could not find user @{handle}")
        return []

    tweets = await gather(api.user_tweets(user.id, limit=5))
    print(f"Fetched {len(tweets)} tweets from @{handle}")
    return [{'id': str(t.id), 'text': t.rawContent} for t in tweets]

def post_to_bluesky(text: str):
    bsky = Client()
    bsky.login(os.environ['BLUESKY_HANDLE'], os.environ['BLUESKY_PASSWORD'])
    bsky.post(text=text[:300])  # Bluesky has a 300 char limit
    print("Posted to Bluesky:", text[:50])

def main():
    seen = load_seen()
    tweets = asyncio.run(fetch_tweets())
    for tw in tweets:
        if tw['id'] in seen:
            continue
        print("Reposting tweet:", tw['text'])
        post_to_bluesky(tw['text'])
        seen.add(tw['id'])
    save_seen(seen)

if __name__ == '__main__':
    main()
