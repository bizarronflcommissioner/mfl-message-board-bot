import discord
from discord.ext import commands
import aiohttp
import os
import re
import asyncio
from dotenv import load_dotenv

# Load env variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LEAGUE_ID = os.getenv("LEAGUE_ID")
MESSAGE_BOARD_ID = os.getenv("MESSAGE_BOARD_ID")
SEASON_YEAR = os.getenv("SEASON_YEAR", "2025")
DISCORD_CLAIMS_CHANNEL = int(os.getenv("DISCORD_CLAIMS_CHANNEL"))

# MFL login credentials
MFL_USERNAME = os.getenv("MFL_USERNAME")
MFL_PASSWORD = os.getenv("MFL_PASSWORD")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# MFL login to get session cookie
async def get_mfl_session_cookie():
    login_url = f"https://api.myfantasyleague.com/{SEASON_YEAR}/login"
    payload = {
        "USERNAME": MFL_USERNAME,
        "PASSWORD": MFL_PASSWORD,
        "XML": 1
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(login_url, data=payload) as response:
            text = await response.text()
            match = re.search(r'cookie_name="(.*?)" cookie_value="(.*?)"', text)
            if match:
                cookie_name, cookie_value = match.groups()
                print(f"[AUTH] Logged in to MFL. Cookie: {cookie_name}={cookie_value}")
                return {cookie_name: cookie_value}
            else:
                print("[AUTH ERROR] Could not extract cookie from login response.")
                print(f"[AUTH DEBUG] Response text:\n{text}")
                return None

# Post message to MFL board
async def post_to_mfl_board(author: str, body: str):
    session_cookie = await get_mfl_session_cookie()
    if not session_cookie:
        print("❌ Login to MFL failed. Cannot post.")
        return False

    subject = f"Taxi Squad Claim - {author}"
    formatted_message = f"**Posted by {author}**\n\n{body}\n\n{'-' * 40}"

    post_url = f"https://www43.myfantasyleague.com/{SEASON_YEAR}/message_board_post"
    payload = {
        "L": LEAGUE_ID,
        "MB": MESSAGE_BOARD_ID,
        "SUBJECT": subject,
        "BODY": formatted_message
    }

    print(f"[MFL POST] POST to {post_url} with payload: {payload}")

    try:
        async with aiohttp.ClientSession(cookies=session_cookie) as session:
            async with session.post(post_url, data=payload) as response:
                text = await response.text()
                print(f"[MFL RESPONSE] Status: {response.status}")
                print(f"[MFL RESPONSE] Body: {text}")

                if response.status == 200 and "error" not in text.lower():
                    print("✅ Message posted to MFL board.")
                    return True
                else:
                    print("❌ MFL post rejected.")
                    return False
    except Exception as e:
        print(f"[EXCEPTION] {e}")
        return False

# Bot ready
@bot.event
async def on_ready():
    print(f"✅ Bot is ready: {bot.user} (ID: {bot.user.id})")

# Ping command for test
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# Diagnose forum channel detection
@bot.command()
async def diagnose(ctx):
    guild = ctx.guild
    forum_channels = [ch for ch in guild.channels if isinstance(ch, discord.ForumChannel)]
    await ctx.send(f"✅ Found {len(forum_channels)} forum channels. Check Railway logs.")
    print(f"[DIAGNOSE] DISCORD_CLAIMS_CHANNEL: {DISCORD_CLAIMS_CHANNEL}")
    for ch in forum_channels:
        print(f"- {ch.name} (ID: {ch.id})")

# Thread event listener
@bot.event
async def on_thread_create(thread):
    print(f"[EVENT] on_thread_create fired for thread: {thread.name} ({thread.id})")

    if str(thread.parent_id) != str(DISCORD_CLAIMS_CHANNEL):
        print(f"[SKIP] Thread is not in claims forum: {thread.parent_id}")
        return

    await asyncio.sleep(2)  # Give Discord time to populate starter message

    try:
        messages = [m async for m in thread.history(limit=1, oldest_first=True)]
        if not messages:
            print("[ERROR] No messages in thread.")
            return

        msg = messages[0]
        print(f"[MESSAGE] Author: {msg.author.display_name}, Content: {msg.content[:100]}")

        success = await post_to_mfl_board(msg.author.display_name, msg.content)
        if success:
            print("[SUCCESS] Claim posted to MFL.")
            await thread.send("✅ Claim posted to MFL.")
            await msg.add_reaction("📬")
        else:
            print("[FAIL] MFL post failed.")
            await thread.send("❌ Could not post to MFL.")

    except Exception as e:
        print(f"[EXCEPTION] Error in thread handler: {e}")

# Start bot
bot.run(DISCORD_TOKEN)
