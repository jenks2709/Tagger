import discord
from discord.ext import commands
import random
import sqlite3
import os
import asyncio

# Load the list of words from words.txt
with open("files/words.txt", "r") as f:
    words = [line.strip() for line in f.readlines()]

# Database setup
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS humans (
    player_id TEXT PRIMARY KEY,
    braincode TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS zombies (
    player_id TEXT PRIMARY KEY,
    braincode TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT
)
""")
conn.commit()
conn.close()

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents)

#Human, Zombie and Spectator count variable set up

human_count = 0
zombie_count = 0
spectator_count = 0

#Function set up
async def update_human_count():
    """Updates the global human_count variable from the database."""
    global human_count
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM humans")
    human_count = cursor.fetchone()[0]  # Update the global variable
    conn.close()
    
async def update_zombie_count():
    """Updates the global human_count variable from the database."""
    global zombie_count
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM zombies")
    zombie_count = cursor.fetchone()[0]  # Update the global variable
    conn.close()

#Cog set up
COGS = ["cogs.human_commands", "cogs.dayplay_commands", "cogs.zombie_commands", "cogs.admin_commands", "cogs.game_commands"]
async def load_cogs():
    """Loads all cogs from the list"""
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Successfully loaded {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")
async def dayplay_announcements(ctx):
    """Automates dayplay announcements"""
    channel_id = 670630369179074570
    role_id = 501688609104199680
    role = ctx.guild.get_role(role_id)
    channel = bot.get_channel(channel_id)

    timestamps = []
       
    if channel:
        for target_time in sorted(timestamps):
            current_time = time.time()
            wait_time = target_time - current_time
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            else:
                await channel.send(f"{role.mention} MESSAGE")
    else:
        print(f"Channel not found")
        

async def announce_ready(ctx):
    channel_id = 670630369179074570
    channel = bot.get_channel(channel_id)
    role_id = 501688609104199680
    role = ctx.guild.get_role(role_id)  
        
    if channel:
        await channel.send("Ay-Ay-Ay-Ay-Ay! It's time to get ready for duty cadets! Join the game now!{role.mention}")
    else:
        print(f"could not find channel")


@bot.event
async def on_ready():
    await load_cogs()
    await announce_ready()
    await dayplay_announcements()
    
    
    


    
# Run the bot
with open("files/token.txt", "r", encoding="utf-8") as file:
    TOKEN = file.read()
bot.run(TOKEN)
