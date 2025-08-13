import os
import discord
import asyncio
import asyncpraw
from datetime import datetime, timezone
from server import keep_alive

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

reddit = None

CHANNEL_ID = 1400741869587140618
SUBREDDIT_NAME = "Guildwars2"
posted_posts = set()

@client.event
async def on_ready():
    print(f"✅ Bot ist online als {client.user}")
    asyncio.create_task(check_subreddit())

async def send_post(channel, post):
    description = "||**Spoiler**||" if post.spoiler else post.selftext
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

async def get_top_posts(subreddit_name, time_filter, limit):
    global reddit
    if reddit is None:
        reddit = asyncpraw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT")
        )
    subreddit = await reddit.subreddit(subreddit_name)
    posts = []
    async for post in subreddit.top(time_filter=time_filter, limit=limit):
        posts.append(post)
    return posts

async def check_subreddit():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("❌ Channel nicht gefunden! Prüfe die CHANNEL_ID.")
        return

    while not client.is_closed():
        print("🔍 Suche nach neuen Top-Beiträgen...")
        try:
            found_new_post = False

            posts = await get_top_posts(SUBREDDIT_NAME, "hour", 20)
            for post in posts:
                if post.id in posted_posts or post.score < 10:
                    continue

                posted_posts.add(post.id)
                await send_post(channel, post)
                found_new_post = True

            if not found_new_post:
                print("⚠️ Keine neuen Posts in der letzten Stunde – suche in den letzten 24 Stunden...")
                posts = await get_top_posts(SUBREDDIT_NAME, "day", 20)
                for post in posts:
                    if post.id in posted_posts or post.score < 10:
                        continue

                    posted_posts.add(post.id)
                    await send_post(channel, post)

        except Exception as e:
            print(f"❌ Fehler beim Abrufen: {e}")

        await asyncio.sleep(3600)

if __name__ == "__main__":
    keep_alive()
    client.run(os.getenv("DISCORD_TOKEN"))

