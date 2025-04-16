import discord
from discord.ext import commands
import sqlite3
import os

class GameCommands(commands.Cog, name="Game Commands"):
    """Commands that are game-wide like checking human/zombie numbers"""

    def __init__(self, bot):
        self.bot = bot
        self.human_count = 0  # Store count inside the class
        self.zombie_count = 0
        self.tag_history = []

    async def update_counts(self):
        """Updates the human and zombie counts"""
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM humans")
        self.human_count = cursor.fetchone()[0]  # Store inside class
        cursor.execute("SELECT COUNT(*) FROM zombies")
        self.zombie_count = cursor.fetchone()[0]
        conn.close()

    async def update_tags(self):
        """Updates the tag history"""
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tags")
        tags = cursor.fetchall()  # Update the global variable
        for tag in tags:
            self.tag_history.append((tag[0], tag[1]))
        conn.close()

    @commands.command()
    async def how_many_humans(self, ctx):
        """Returns the number of Humans in the game"""
        await self.update_counts()  # Update before showing count
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        if self.human_count == 1:
            await ctx.send(f"There is **1** Human!")
        else:
            await ctx.send(f"There are **{self.human_count}** Humans!")

    @commands.command()
    async def how_many_zombies(self, ctx):
        """Returns the number of Zombies in the game"""
        await self.update_counts()  # Update before showing count
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        if self.zombie_count == 1:
            await ctx.send(f"There is **1** Zombie!")
        else:
            await ctx.send(f"There are **{self.zombie_count}** Zombies!")

    @commands.command()
    async def how_many_players(self, ctx):
        """Returns the number of players who have joined the game"""
        await self.update_counts()  # Update before showing count
        player_count = self.zombie_count + self.human_count
        if player_count == 1:
            await ctx.send(f"There is **1** player!")
        else:
            await ctx.send(f"There are **{player_count}** players!")

    @commands.command()
    async def tag_history(self, ctx):
        """Sends a message containing the tag history for this game"""
        await self.update_tags() #Update the tag history
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        guild = ctx.guild
        if self.tag_history == []:
            await ctx.send("No tags have occurred so far")
        else:
            for tag in self.tag_history:
                await ctx.send(f"**`{guild.get_member(int(tag[0]))}`** tagged **`{guild.get_member(int(tag[1]))}`**")
    @commands.command()
    async def tag_tree(self, ctx):
        """Sends an image containing a diagram of the tag history"""
        await self.update_tags() #Update the tag history
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        try:
            await ctx.send(file=discord.File('files/tag_graph_image.png'))
        except FileNotFoundError:
            await ctx.send("Error: Cannot find tag tree image")




async def setup(bot):
    await bot.add_cog(GameCommands(bot))
