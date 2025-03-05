import discord
from discord.ext import commands
import sqlite3
import random

# Load the list of words from words.txt
with open("files/words.txt", "r") as f:
    words = [line.strip() for line in f.readlines()]

async def update_human_count():
    """Updates the global human_count variable from the database."""
    global human_count
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM humans")
    human_count = cursor.fetchone()[0]  # Update the global variable
    conn.close()    

class HumanCommands(commands.Cog, name="Human Commands"):
    """Commands related to core rules such as joining and checking your braincode"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, first_name: str = None, last_name: str = None):
        """Assigns the 'Human' role, generates a braincode, and optionally changes the player's nickname. This command is run by typing '.join' into the '#-join' channel."""
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("I do not have permission to delete messages.")
        if ctx.channel.name == "join":
            guild = ctx.guild
            member = ctx.author
            human_role = discord.utils.get(guild.roles, name="Human")
            zombie_role = discord.utils.get(guild.roles, name="Zombie")
            player_role = discord.utils.get(guild.roles, name="Player")

            if not human_role:
                await ctx.send("'Human' role does not exist. Please create it and try again.")
                return

            if player_role in member.roles:
                await ctx.send("You have already joined the game.")
                return

            await member.add_roles(human_role)
            await member.add_roles(player_role)
            

            braincode = "".join(random.sample(words, 3))
            # Insert player info into the database
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()   
            cursor.execute("""
                INSERT OR REPLACE INTO humans (player_id, braincode, first_name, last_name) 
                VALUES (?, ?, ?, ?)
            """, (str(member.id), braincode, first_name, last_name))
            conn.commit()
            conn.close()
            if first_name and last_name:
                try:
                    await member.edit(nick=f"{first_name} {last_name}")
                except discord.Forbidden:
                    pass

            try:
                await member.send(f"Your braincode is: **`{braincode}`**\n*Keep it secret, Keep it safe!*")
            except discord.Forbidden:
                await ctx.send("Failed to send DM. Please check your privacy settings.")
            await update_human_count()
        else:
            await ctx.send("You must use this command in the `#join` channel")

    @commands.command()
    async def check_braincode(self, ctx):
        """ This command will resend a DM containing your braincode. This command is run by typing '.check_braincode' into any channel"""
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("I do not have permission to delete messages.")
        
        # Database setup (ensure the connection is open)
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Get the user_id of the author who ran the command
        player_id = str(ctx.author.id)  # Convert user ID to string since it's stored as TEXT

        # Query the database to retrieve the braincode for the player_id
        cursor.execute("SELECT braincode FROM humans WHERE player_id = ?", (player_id,))
        result = cursor.fetchone()
        conn.close()

        # Check if a braincode exists for the user
        if not result:
            await ctx.send(f"{ctx.author.mention}, you do not have an associated braincode.")
        else:
            braincode = result[0]  # Extract the braincode from the result
            await ctx.author.send(f"{ctx.author.mention}, your braincode is: **`{braincode}`**")




# Setup function required to load the Cog
async def setup(bot):
    await bot.add_cog(HumanCommands(bot))
