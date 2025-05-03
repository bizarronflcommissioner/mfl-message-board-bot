import discord
from discord.ext import commands
import aiohttp
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LEAGUE_ID = os.getenv("LEAGUE_ID")
MESSAGE_BOARD_ID = os.getenv("MESSAGE_BOARD_ID")
SEASON_YEAR = os.getenv("SEASON_YEAR", "2025")
DISCORD_CLAIMS_CHANNEL = os.getenv("DISCORD_CLAIMS_CHANNEL")

# Debug logging for environment variables
print("🔧 ENV VARS LOADED:")
print("DISCORD_TOKEN:", "✅" if DISCORD_TOKEN else "❌ MISSING")
print("LEAGUE_ID:", LEAGUE_ID or "❌ MISSING")
print("MESSAGE_BOARD_ID:", MESSAGE_BOARD_ID or "❌ MISSING")
print("SEASON_YEAR:", SEASON_YEAR)
print("DISCORD_CLAIMS_CHANNEL:", DISCORD_CLAIMS_CHANNEL or "❌ MISSING")

# Parse claims channel ID if provided
try:
    DISCORD_CLAIMS_CHANNEL = int(DISCORD_CLAIMS_CHANNEL)
except (TypeError, ValueError):
    print("❌ ERROR: DISCORD_CLAIMS_CHANNEL is not a valid integer.")
    DISCORD_CLAIMS_CHANNEL = None

# Setup bot with message content intent
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# MFL post function
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
        "M": formatted_message,
        "SUBJECT": subject
    }

    print(f"🌐 Posting to MFL: {post_url}")
    print(f"📝 Payload: {payload}")

    async with aiohttp.ClientSession() as session:
        async with session.post(post_url, data=payload) as resp:
            resp_text = await resp.text()
            if resp.status == 200:
                print(f"✅ Successfully posted claim from {author}")
                return True
            else:
                print(f"❌ Failed to post to MFL: {resp.status}")
                print("📄 Response text:", resp_text)
                return False

# Bot ready
@bot.event
async def on_ready():
    print(f"🤖 Bot logged in as {bot.user}")

# Message handler
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    print(f"💬 Message from {message.author} in #{message.channel.name} (ID: {message.channel.id})")

    if message.channel.id == DISCORD_CLAIMS_CHANNEL:
        content = message.content.strip()
        if content:
            success = await post_to_mfl_board(message.author.display_name, content)
            if success:
                await message.channel.send("📬 Claim posted to MFL.")
            else:
                await message.channel.send("⚠️ Failed to post to MFL.")
    await bot.process_commands(message)

# Run the bot
try:
    bot.run(DISCORD_TOKEN)
except Exception as e:
    print(f"❌ Bot failed to run: {e}")
