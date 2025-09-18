import discord
from discord.ext import commands
import random
import sqlite3
import os
import asyncio

with open("files/words.txt", "r") as f:
    words = [line.strip() for line in f.readlines()]

class AdminCommands(commands.Cog, name="Admin"):
    """Commands for administrative purposes, Only to be run by Moderators or Committee"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def give_points(self, ctx, braincode: str, amount: int ):
        if ctx.channel.name != "bot-commands":
            await ctx.send("This command cannot be used here")
            return

        db="database.db"

        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT points FROM players WHERE LOWER(braincode) =?", (braincode.lower(),))
        result = cursor.fetchone()
        print(result)
        if result is None:
            await ctx.send ("Player not found")
        else:
            cursor.execute("UPDATE players SET points = points + ? WHERE LOWER(braincode) =?", (amount, braincode.lower()))
            conn.commit()
                                

    @commands.command(name="check_humans")
    async def check_humans(self, ctx):
        """Check the contents of the humans table in the database."""
        if ctx.channel.name != "bot-commands":
            await ctx.send("This command can only be used in `#bot-commands`.")
            return

        db_path = "database.db"

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT player_id, braincode, first_name, last_name, points FROM players WHERE team = 'Human'")
            rows = cursor.fetchall()
            conn.close()

            if rows:
                response = "**Human Players:**\n"
                for player_id, braincode,  first_name, last_name, points  in rows:
                    response += f"- {first_name} {last_name} (ID: {player_id}) (Braincode: {braincode})(Points: {points})\n"
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
        if ctx.channel.name != "bot-commands":
            await ctx.send("This command can only be used in `#bot-commands`.")
            return

        db_path = "database.db"

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT player_id, braincode, first_name, last_name, points FROM players WHERE team = 'Zombie'")
            rows = cursor.fetchall()
            conn.close()

            if rows:
                response = "**Zombie Players:**\n"
                for player_id, braincode, first_name, last_name, points in rows:
                    response += f"- {first_name} {last_name} (ID: {player_id})(Braincode: {braincode})(Points: {points})\n"
            else:
                response = "There are no Zombies."

            await ctx.send(response)
        except sqlite3.OperationalError as e:
            await ctx.send(f"Database error: `{e}`")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: `{e}`")

    @commands.command(name="check_players")
    async def check_players(self, ctx):
        """Check the contents of the zombies table in the database."""
        if ctx.channel.name != "bot-commands":
            await ctx.send("This command can only be used in `#bot-commands`.")
            return
        db_path = "database.db"
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT player_id, braincode, first_name, last_name, points FROM players")
            rows = cursor.fetchall()
            conn.close()

            if rows:
                response = "**All Players:**\n"
                for player_id, braincode, first_name, last_name, points in rows:
                    response += f"- {first_name} {last_name} (ID: {player_id})(Braincode: {braincode})(Points: {points})\n"
            else:
                response = "There are no Players."

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

        if ctx.channel.name != "bot-commands":
            await ctx.send("This command must be used in `#bot-commands`.")
            return

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT player_id, first_name, last_name FROM players WHERE braincode = ?", (braincode,))
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

                cursor.execute("UPDATE players SET braincode = ?, team = ? WHERE braincode = ?",
                               (new_braincode, "Human", braincode))
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
        
        if ctx.channel.name != "bot-commands":
            await ctx.send("This command can only be used in `#bot-commands`.")
            return
        db = "database.db"
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        guild = ctx.guild
        human_role = discord.utils.get(guild.roles, name="Human")
        zombie_role = discord.utils.get(guild.roles, name="Zombie")
        player_role = discord.utils.get(guild.roles, name="Player")

        if not human_role or not zombie_role or not Player:
            await ctx.send("Error: Required roles not found in the server.")
            return
        
        for member in guild.members:
            new_braincode = "".join(random.sample(words, 3))
            try:
                if zombie_role in member.roles:
                    await member.remove_roles(zombie_role)
                    await member.add_roles(human_role)
            except discord.Forbidden:
                await ctx.send(f"Could not reset roles for {member.display_name}.")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE players SET team=humans WHERE team=zombies")
        cursor.execute("DELETE FROM tags")
        conn.commit()

        for member in guild.members:
            if human_role in member.roles:
                braincode = "".join(random.sample(words, 3))
                cursor.execute("INSERT INTO humans (player_id, braincode) VALUES (?, ?)", (str(member.id), braincode))
                try:
                    await member.send(f"Your new braincode is: **`{braincode}`**\n*Keep it secret, keep it safe!*")
                except discord.Forbidden:
                    await ctx.send(f"Could not DM {member.display_name}.")                                    
                    cursor.execute("UPDATE players SET braincode = ?, team = ? WHERE player_id =?",(new_braincode, "Human", member.id))
                    conn.commit()
##                    # Send the new braincode via DM
##                    try:
##                        await member.send(f"Your new braincode is: **`{new_braincode}`**\n*Keep it secret, keep it safe!*")
##                    except discord.Forbidden:
##                        await ctx.send(f"Could not DM {member.display_name}.")
                

        conn.commit()
        conn.close()


        await ctx.send("Game has been reset.")

    
    @commands.command(name="end")
    async def end(self, ctx):
        """ Ends the game. Can only be run by Mods or Committee"""
        # Ensure the command is run in the correct channel
        if ctx.channel.name != "bot-commands":
            await ctx.send("You cannot stop the bot from this channel.")
            return

        guild = ctx.guild
        human_role = discord.utils.get(guild.roles, name="Human")
        zombie_role = discord.utils.get(guild.roles, name="Zombie")
        player_role = discord.utils.get(guild.roles, name="Player")

        db_path = "database.db"
        if not os.path.exists(db_path):
            await ctx.send("Database file not found. Nothing to clean.")
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query both tables for user IDs
        cursor.execute("SELECT player_id FROM players")
        user_ids = cursor.fetchall()
        conn.close()

        # print("ids: "||user_ids)

        if not user_ids:
            await ctx.send("No users found in the database. Nothing to clean. Shutting down Tagger")
            await self.bot.close()
            return

        # Iterate over the user IDs and remove roles
        for (user_id,) in user_ids:  # Unpacking tuple
            member = guild.get_member(int(user_id))
            
            if member is None:
                await ctx.send(f"Could not find user with ID {user_id}.")
                continue

            try:
                await member.remove_roles(zombie_role, human_role, player_role)
            except discord.Forbidden:
                await ctx.send(f"Could not remove roles for {member.display_name}.")
            except Exception as e:
                await ctx.send(f"Error removing roles from {member.display_name}: {e}")


        # Delete the database file
        try:
            os.remove(db_path)
            await ctx.send("Database wiped successfully.")
        except Exception as e:
            await ctx.send(f"Failed to delete database: {e}")

        # Shut down the bot
        await ctx.send("Tagger has been shut down, roles removed, and database wiped.")
        await self.bot.close()

    @commands.command()
    async def shop(self, ctx):
        with open("files/shop.txt", "r", encoding="utf-8") as file_1:
            rules = file_1.read()

        await ctx.send("Equipment Store:")  # Bold title
        formatted_rules = f"```\n{rules}\n```"

        # Chunking for long messages
        for chunk in [formatted_rules[i : i + 1990] for i in range(0, len(formatted_rules), 1990)]:
            await ctx.send(chunk)

    @commands.command(name="starting_tag")
    async def tag(self, ctx, braincode: str):
        """
        Turns a human into a zombie using the given braincode, but does not record the tag in the history 
        Example: `.starting_tag braincode`
        """

        try:
            await ctx.message.delete()  # Deletes the message that triggered the command
        except discord.Forbidden:
            await ctx.send("I do not have permission to delete messages.")

        if ctx.channel.name != "tagger-commands":
            await ctx.send("This command must be used in `#tagger-commands`")
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

                # Announce the tag
                if human_chat_channel:
                    if member.id == 560509176669798440:
                        gif_path = "files/badspeed_deployed.gif"
                        await human_chat_channel.send(f"{member.mention} is a starting zombie!", file=discord.File(gif_path))
                    else:
                        await human_chat_channel.send(f"{member.mention} is a starting zombie!")

                if zombie_chat_channel:
                    await ctx.send(f"{member.mention} is a starting zombie!")

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
    await bot.add_cog(AdminCommands(bot))
