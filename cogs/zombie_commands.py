import discord
from discord.ext import commands
import random
import sqlite3
import os
import asyncio

class ZombieCommands(commands.Cog, name="Zombie Commands"):
    """Commands related to zombies such as tagging"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tag")
    async def tag(self, ctx, braincode: str):
        """
        Handles the tagging process, converting a Human into a Zombie, using the braincode given in the command.
        Example: `.tag braincode`
        """

        try:
            await ctx.message.delete()  # Deletes the message that triggered the command
        except discord.Forbidden:
            await ctx.send("I do not have permission to delete messages.")

        if ctx.channel.name != "zombie-chat":
            await ctx.send("This command must be used in `#zombie-chat`")
            return

        # Connect to the database
        try:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()

            # Query the human database for the player_id associated with the braincode
            cursor.execute("SELECT player_id, braincode, first_name, last_name FROM humans WHERE LOWER(braincode) = ?", (braincode.lower(),))
            result = cursor.fetchone()
        except sqlite3.Error as e:
            await ctx.send(f"Database error: `{e}`")
            return

        if not result:
            await ctx.send(f"No player found with that braincode.")
            return

        # Extract player info
        player_id, _, first_name, last_name = result

        # Retrieve the member object
        guild = ctx.guild
        member = guild.get_member(int(player_id))
        tagger = ctx.author
        human_chat_channel = discord.utils.get(guild.text_channels, name="human-chat")
        zombie_chat_channel = discord.utils.get(guild.text_channels, name="zombie-chat")

        if not member:
            await ctx.send(f"Could not find a player with ID {player_id} in this server.")
            return

        # Get roles
        human_role = discord.utils.get(guild.roles, name="Human")
        zombie_role = discord.utils.get(guild.roles, name="Zombie")

        if not human_role or not zombie_role:
            await ctx.send("No 'Human' or 'Zombie' roles found. Please create these roles first.")
            return

        # Convert Human to Zombie in the database
        cursor.execute("INSERT OR REPLACE INTO zombies (player_id, braincode, first_name, last_name) VALUES (?, ?, ?, ?)", (member.id, braincode, first_name, last_name))
        cursor.execute("DELETE FROM humans WHERE LOWER(braincode) = ?", (braincode.lower(),))
        conn.commit()
        conn.close()

        # Remove "Human" role and add "Zombie" role
        try:
            if human_role in member.roles:
                await member.remove_roles(human_role)
                await member.add_roles(zombie_role)

                # Load a random message from the .txt file
                try:
                    with open("files/death_messages.txt", "r") as f:
                        messages = [line.strip() for line in f if line.strip()]
                    tag_message = random.choice(messages) if messages else "The infection spreads further..."
                except FileNotFoundError:
                    tag_message = "The infection spreads further..."

                # Announce the tag
                if human_chat_channel:
                    if member.id == 560509176669798440:
                        gif_path = "files/badspeed_deployed.gif"
                        await human_chat_channel.send(f"{member.mention} was tagged!", file=discord.File(gif_path))
                    else:
                        await human_chat_channel.send(f"{member.mention} was tagged by {tagger.mention}! {tag_message}")

                if zombie_chat_channel:
                    await ctx.send(f"{member.mention} was tagged by {tagger.mention}! {tag_message}")

                # ✅ FIX: Update the human and zombie counts using GameCommands Cog
                game_cog = self.bot.get_cog("Game Commands")  # Get the cog
                if game_cog:
                    await game_cog.update_counts()  # Update counts if the cog exists
                else:
                    await ctx.send("Error: Game Commands cog not found.")
            else:
                await ctx.send(f"{member.mention} is already a Zombie.")
        except Exception as e:
            await ctx.send(f"An error occurred while tagging: `{e}`")

async def setup(bot):
    await bot.add_cog(ZombieCommands(bot))
