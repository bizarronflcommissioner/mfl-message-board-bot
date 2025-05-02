import discord
from discord.ext import commands
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LEAGUE_ID = os.getenv("LEAGUE_ID")
MESSAGE_BOARD_ID = os.getenv("MESSAGE_BOARD_ID")
SEASON_YEAR = os.getenv("SEASON_YEAR", "2025")
DISCORD_CLAIMS_CHANNEL = int(os.getenv("DISCORD_CLAIMS_CHANNEL"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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

    async with aiohttp.ClientSession() as session:
        async with session.post(post_url, data=payload) as resp:
            if resp.status == 200:
                print(f"✅ Posted claim from {author}")
                return True
            else:
                print(f"❌ Failed to post to MFL: {resp.status}")
                return False

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id == DISCORD_CLAIMS_CHANNEL:
        content = message.content.strip()
        if content:
            success = await post_to_mfl_board(message.author.display_name, content)
            if success:
                await message.channel.send("📬 Claim posted to MFL.")
            else:
                await message.channel.send("⚠️ Failed to post to MFL.")

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
