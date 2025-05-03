import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio  # ← Needed for the idle loop

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LEAGUE_ID = os.getenv("LEAGUE_ID")
MESSAGE_BOARD_ID = os.getenv("MESSAGE_BOARD_ID")
SEASON_YEAR = os.getenv("SEASON_YEAR", "2025")
DISCORD_CLAIMS_CHANNEL = int(os.getenv("DISCORD_CLAIMS_CHANNEL"))

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is ready: {bot.user} (ID: {bot.user.id})")
    # Keep-alive dummy task to prevent Railway from stopping container
    bot.loop.create_task(idle_loop())

async def idle_loop():
    while True:
        await asyncio.sleep(3600)  # Sleep for 1 hour at a time

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

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

    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.post(post_url, data=payload) as response:
            if response.status == 200:
                print("✅ Message posted to MFL board.")
                return True
            else:
                print(f"❌ Failed to post message. Status code: {response.status}")
                return False

# Run the bot
bot.run(DISCORD_TOKEN)
