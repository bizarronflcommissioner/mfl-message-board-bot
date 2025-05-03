import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import aiohttp
from aiohttp import web
import threading

# Load env vars
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LEAGUE_ID = os.getenv("LEAGUE_ID")
MESSAGE_BOARD_ID = os.getenv("MESSAGE_BOARD_ID")
SEASON_YEAR = os.getenv("SEASON_YEAR", "2025")
DISCORD_CLAIMS_CHANNEL = int(os.getenv("DISCORD_CLAIMS_CHANNEL"))

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.guild_messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is ready: {bot.user} (ID: {bot.user.id})")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# MFL message board post
async def post_to_mfl_board(author: str, body: str):
    if not LEAGUE_ID or not MESSAGE_BOARD_ID:
        print("❌ MFL credentials missing.")
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

    async with aiohttp.ClientSession() as session:
        async with session.post(post_url, data=payload) as response:
            if response.status == 200:
                print("✅ Message posted to MFL board.")
                return True
            else:
                print(f"❌ Failed to post message. Status code: {response.status}")
                return False

# Forum monitor with logging & reactions
@bot.event
async def on_thread_create(thread):
    print(f"[EVENT] on_thread_create fired for thread: {thread.name} ({thread.id})")

    if str(thread.parent_id) != str(DISCORD_CLAIMS_CHANNEL):
        print(f"[SKIP] Thread {thread.name} is in channel {thread.parent_id}, not {DISCORD_CLAIMS_CHANNEL}")
        return

    await asyncio.sleep(2)  # allow time for Discord to populate the starter message

    try:
        # Debug: show thread history
        messages = [m async for m in thread.history(limit=1, oldest_first=True)]
        if not messages:
            print(f"[ERROR] No starter message found for thread {thread.name}")
            return

        msg = messages[0]
        print(f"[MESSAGE] Author: {msg.author.display_name}, Content: {msg.content[:60]}")

        success = await post_to_mfl_board(msg.author.display_name, msg.content)
        if success:
            print("[SUCCESS] Posted to MFL message board")
            await thread.send("✅ Claim posted to MFL.")
            await msg.add_reaction("📬")
        else:
            print("[FAIL] MFL post failed")
            await thread.send("❌ Could not post to MFL.")

    except Exception as e:
        print(f"[EXCEPTION] {e}")

# Web server (keep-alive)
async def handle_status(request):
    return web.Response(text="✅ Bot is alive")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_status)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=3000)
    await site.start()
    print("🌐 Web server running on port 3000")

def start_async_web_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_web_server())
    loop.run_forever()

# Launch web server in background
threading.Thread(target=start_async_web_server, daemon=True).start()

# Run the Discord bot
bot.run(DISCORD_TOKEN)
