import discord
from discord.ext import commands
import random
import sqlite3
import os
import asyncio

with open("files/words.txt", "r") as f:
    words = [line.strip() for line in f.readlines()]

class AdminCommands(commands.Cog, name="Admin Commands"):
    """Commands for administrative purposes, Only to be run by Moderators or Committee"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="check_humans")
    async def check_humans(self, ctx):
        """Check the contents of the humans table in the database."""
        if ctx.channel.name != "tagger-commands":
            await ctx.send("This command can only be used in `#bot-commands`.")
            return

        db_path = "database.db"

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT player_id, braincode,first_name, last_name FROM humans")
            rows = cursor.fetchall()
            conn.close()

            if rows:
                response = "**Human Players:**\n"
                for player_id, braincode, first_name, last_name  in rows:
                    response += f"- {first_name} {last_name} (ID: {player_id}) (Braincode: {braincode})\n"
            else:
                response = "There are no Humans."

            await ctx.send(response)
        except sqlite3.OperationalError as e:
            await ctx.send(f"Database error: `{e}`")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: `{e}`")

    @commands.command(name="check_zombies")
    async def check_zombies(self, ctx):
        """Check the contents of the zombies table in the database."""
        if ctx.channel.name != "tagger-commands":
            await ctx.send("This command can only be used in `#bot-commands`.")
            return

        db_path = "database.db"

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT player_id, braincode, first_name, last_name FROM zombies")
            rows = cursor.fetchall()
            conn.close()

            if rows:
                response = "**Zombie Players:**\n"
                for player_id, braincode, first_name, last_name in rows:
                    response += f"- {first_name} {last_name} (ID: {player_id})(Braincode: {braincode})\n"
            else:
                response = "There are no Zombies."

            await ctx.send(response)
        except sqlite3.OperationalError as e:
            await ctx.send(f"Database error: `{e}`")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: `{e}`")

    @commands.command(name="revive")
    async def revive(self, ctx, braincode: str):
        """Revives a player based on their braincode and returns them to the Humans."""
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("I do not have permission to delete messages.")

        if ctx.channel.name != "tagger-commands":
            await ctx.send("This command must be used in `#bot-commands`.")
            return

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT player_id, first_name, last_name FROM zombies WHERE LOWER(braincode) = ?", (braincode.lower(),))
        result = cursor.fetchone()

        if not result:
            await ctx.send("No player found with that braincode, or the player is not a Zombie.")
            conn.close()
            return

        player_id, first_name, last_name = result

        guild = ctx.guild
        member = guild.get_member(int(player_id))
        
        if not member:
            await ctx.send(f"Could not find the player with ID {player_id} in this server.")
            conn.close()
            return

        human_role = discord.utils.get(guild.roles, name="Human")
        zombie_role = discord.utils.get(guild.roles, name="Zombie")

        if not human_role or not zombie_role:
            await ctx.send("Please make sure 'Human' and 'Zombie' roles exist on the server.")
            conn.close()
            return

        try:
            if zombie_role in member.roles:
                await member.remove_roles(zombie_role)
                await member.add_roles(human_role)

                new_braincode = "".join(random.sample(words, 3))

                cursor.execute("DELETE FROM zombies WHERE LOWER(braincode) = ?", (braincode.lower(),))
                cursor.execute("INSERT OR REPLACE INTO humans (player_id, braincode, first_name, last_name) VALUES (?, ?, ?, ?)",
                               (member.id, new_braincode, first_name, last_name))
                conn.commit()

                human_chat_channel = discord.utils.get(guild.text_channels, name="human-chat")
                zombie_chat_channel = discord.utils.get(guild.text_channels, name="zombie-chat")
                
                if human_chat_channel:
                    await human_chat_channel.send(f"{member.mention} has been revived and is now a Human again!")
                if zombie_chat_channel:
                    await zombie_chat_channel.send(f"{member.mention} has been revived and is no longer a Zombie!")

                await ctx.send(f"Player has been revived successfully.")

                # ✅ FIX: Update the human and zombie counts using GameCommands Cog
                game_cog = self.bot.get_cog("Game Commands")
                if game_cog:
                    await game_cog.update_counts()
                else:
                    await ctx.send("Error: Game Commands cog not found.")

                try:
                    await member.send(f"**You have been revived!**\nYour new braincode is: **`{new_braincode}`**\n*Keep it secret, keep it safe!*")
                except discord.Forbidden:
                    return
            else:
                await ctx.send(f"{member.mention} is not a Zombie.")
        except Exception as e:
            await ctx.send(f"An error occurred while reviving: `{e}`")
        finally:
            conn.close()

    @commands.command(name="reset")
    async def reset(self, ctx):
        """Resets the game, restoring all players to Human and issuing new braincodes."""
        if ctx.channel.name != "tagger-commands":
            await ctx.send("This command can only be used in `#bot-commands`.")
            return

        guild = ctx.guild
        human_role = discord.utils.get(guild.roles, name="Human")
        zombie_role = discord.utils.get(guild.roles, name="Zombie")

        for member in guild.members:
            try:
                if zombie_role in member.roles:
                    await member.remove_roles(zombie_role)
                    await member.add_roles(human_role)
            except discord.Forbidden:
                await ctx.send(f"Could not reset roles for {member.display_name}.")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM humans")
        cursor.execute("DELETE FROM zombies")
        conn.commit()

        for member in guild.members:
            if human_role in member.roles:
                braincode = "".join(random.sample(words, 3))
                cursor.execute("INSERT INTO humans (player_id, braincode) VALUES (?, ?)", (str(member.id), braincode))
                try:
                    await member.send(f"Your new braincode is: **`{braincode}`**\n*Keep it secret, keep it safe!*")
                except discord.Forbidden:
                    await ctx.send(f"Could not DM {member.display_name}.")
        conn.commit()
        conn.close()

        await ctx.send("Game has been reset.")

        # ✅ FIX: Update the human and zombie counts using GameCommands Cog
        game_cog = self.bot.get_cog("Game Commands")
        if game_cog:
            await game_cog.update_counts()
        else:
            await ctx.send("Error: Game Commands cog not found.")

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
