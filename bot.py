import discord
from discord.ext import commands
import random
import sqlite3
import os
import asyncio
import time

# Load the list of words from words.txt
with open("files/words.txt", "r") as f:
    words = [line.strip() for line in f.readlines()]

# Database setup
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    team TEXT,
    braincode TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    points TEXT
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

#Variable set up

human_count = 0
zombie_count = 0
spectator_count = 0
stun_timer = 5

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
COGS = ["cogs.human_commands", "cogs.dayplay_commands", "cogs.zombie_commands", "cogs.admin_commands", "cogs.game_commands", "cogs.automation", "cogs.shop"]
async def load_cogs():
    """Loads all cogs from the list"""
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Successfully loaded {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")

async def announce_ready():
    channel_id = 1350945770215309312
    guild = bot.guilds[0]
    channel = guild.get_channel(channel_id)
    role_id = 501688609104199680
    role = guild.get_role(int(role_id))
        
    if channel:
        await channel.send(f"Aye-yi-yi-yi-yi! Alpha-10 ready for action!{role.mention}")
    else:
        print(f"could not find channel")


# List of cogs to ignore
IGNORED_COGS = {"Dayplay", "Admin", "Shop"}

class CustomHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Help", color=discord.Color.blue())

        for cog, commands in mapping.items():
            if cog and cog.qualified_name in IGNORED_COGS:
                continue  # Skip ignored cogs

            filtered_commands = [cmd for cmd in commands if not cmd.hidden]
            if filtered_commands:
                command_list = "\n".join(f"`{cmd.name}` - {cmd.help or 'No description'}" for cmd in filtered_commands)
                embed.add_field(name=cog.qualified_name if cog else "No Category", value=command_list, inline=False)

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        if cog.qualified_name in IGNORED_COGS:
            return  # Ignore hidden cogs

        embed = discord.Embed(title=f"Help - {cog.qualified_name}", color=discord.Color.green())
        commands = cog.get_commands()
        filtered_commands = [cmd for cmd in commands if not cmd.hidden]

        if not filtered_commands:
            return

        for command in filtered_commands:
            embed.add_field(name=command.name, value=command.help or "No description", inline=False)

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        if command.cog and command.cog.qualified_name in IGNORED_COGS:
            return  # Ignore commands from ignored cogs

        embed = discord.Embed(title=f"Help: {command.name}", description=command.help or "No description", color=discord.Color.green())
        embed.add_field(name="Usage", value=self.get_command_signature(command))
        await self.get_destination().send(embed=embed)
bot = commands.Bot(command_prefix=".", intents=intents, help_command=CustomHelpCommand())

@bot.event
async def on_ready():
    await load_cogs()
    print(f"Cogs loaded")
    #await announce_ready()

    
# Run the bot
with open("files/token.txt", "r", encoding="utf-8") as file:
    TOKEN = file.read()
bot.run(TOKEN)
