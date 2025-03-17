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
cursor.execute("""
CREATE TABLE IF NOT EXISTS tags (
    zombie_id TEXT NOT NULL,
    human_id TEXT NOT NULL,
    FOREIGN KEY (zombie_id) REFERENCES zombies(zombie_id),
    FOREIGN KEY (human_id) REFERENCES humans(human_id),
    PRIMARY KEY (zombie_id, human_id)
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

@bot.event
async def on_ready():
    await load_cogs()
    print("Tagger is online, running and ready for commands")


    
# Run the bot
with open("files/token.txt", "r", encoding="utf-8") as file:
    TOKEN = file.read()
bot.run(TOKEN)
