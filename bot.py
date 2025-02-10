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

@bot.event
async def on_ready():
    await load_cogs()
    print("Tagger is online, running and ready for commands")

@bot.command(name="end")
async def end(ctx):

    """ Ends the game. Can only be run by Mods or Committee"""
    # Ensure the command is run in the correct channel
    if ctx.channel.name != "bot-test":
        await ctx.send("You cannot stop the bot from this channel.")
        return

    guild = ctx.guild
    human_role = discord.utils.get(guild.roles, name="Human")
    zombie_role = discord.utils.get(guild.roles, name="Zombie")

    db_path = "database.db"
    if not os.path.exists(db_path):
        await ctx.send("Database file not found. Nothing to clean.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query both tables for user IDs
    cursor.execute("SELECT player_id FROM humans")
    user_ids_table1 = cursor.fetchall()

    cursor.execute("SELECT player_id FROM zombies") 
    user_ids_table2 = cursor.fetchall()

    conn.close()

    # Combine and deduplicate user IDs from both tables
    user_ids = {int(user_id[0]) for user_id in user_ids_table1 + user_ids_table2}

    if not user_ids:
        await ctx.send("No users found in the database. Nothing to clean. Shutting down Tagger")
        await bot.close()
        return

    # Iterate over the user IDs and remove roles
    for user_id in user_ids:
        member = guild.get_member(user_id)
        if member:
            try:
                await member.remove_roles(human_role, zombie_role)
            except discord.Forbidden:
                await ctx.send(f"Could not remove roles for {member.display_name}.")
            except Exception as e:
                await ctx.send(f"An error occurred while removing roles: `{e}`")

    # Delete the database file
    try:
        os.remove(db_path)
        await ctx.send("Database wiped successfully.")
    except Exception as e:
        await ctx.send(f"Failed to delete database: {e}")

    # Shut down the bot
    await ctx.send("Tagger has been shut down, roles removed, and database wiped.")
    await bot.close()
    
# Run the bot
with open("files/token.txt", "r", encoding="utf-8") as file:
    TOKEN = file.read()
bot.run(TOKEN)
