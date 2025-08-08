import os
import discord
import asyncio
import praw
from datetime import datetime, timezone
from server import keep_alive

intents = discord.Intents.default()
client = discord.Client(intents=intents)

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

CHANNEL_ID = 1400741869587140618
SUBREDDIT_NAME = "Guildwars2"
posted_posts = set()

@client.event
async def on_ready():
    print(f"✅ Bot ist online als {client.user}")
    client.loop.create_task(check_subreddit())

async def send_post(channel, post):
    if post.spoiler:
        description = "||**Spoiler**||"
    else:
        description = post.selftext
        if description and len(description) > 400:
            description = description[:397] + "..."

    created_time = datetime.fromtimestamp(post.created_utc, timezone.utc)

    embed = discord.Embed(
        title=post.title,
        url=f"https://reddit.com{post.permalink}",
        description=description or " ",
        color=discord.Color.orange()
    )
    embed.set_author(name=f"u/{post.author}")
    embed.set_footer(text=f"r/{SUBREDDIT_NAME}")
    embed.timestamp = created_time

    if not post.spoiler and hasattr(post, "url") and post.url.endswith((".jpg", ".png", ".jpeg", ".gif", ".mp4", ".webm")):
        embed.set_image(url=post.url)

    await channel.send(embed=embed)

async def check_subreddit():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("❌ Channel nicht gefunden! Prüfe die CHANNEL_ID.")
        return

    subreddit = reddit.subreddit(SUBREDDIT_NAME)

    while not client.is_closed():
        print("🔍 Suche nach neuen Top-Beiträgen...")
        try:
            found_new_post = False

            for post in subreddit.top(time_filter="hour", limit=20):
                if post.id in posted_posts:
                    continue
                if post.score < 10:
                    continue

                posted_posts.add(post.id)
                await send_post(channel, post)
                found_new_post = True

            if not found_new_post:
                print("⚠️ Keine neuen Posts in der letzten Stunde – suche in den letzten 24 Stunden...")
                for post in subreddit.top(time_filter="day", limit=20):
                    if post.id in posted_posts:
                        continue
                    if post.score < 10:
                        continue

                    posted_posts.add(post.id)
                    await send_post(channel, post)

        except Exception as e:
            print(f"❌ Fehler beim Abrufen: {e}")

        await asyncio.sleep(3600)

if __name__ == "__main__":
    keep_alive()
    client.run(os.getenv("DISCORD_TOKEN"))