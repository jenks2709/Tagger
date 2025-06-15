import discord
from discord.ext import commands
import sqlite3
import math
import os

class GameCommands(commands.Cog, name="Game Commands"):
    """Commands that are game-wide like checking human/zombie numbers"""

    def __init__(self, bot):
        self.bot = bot
        self.human_count = 0  # Store count inside the class
        self.zombie_count = 0

    async def update_counts(self):
        """Updates the human and zombie counts"""
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM humans")
        self.human_count = cursor.fetchone()[0]  # Store inside class
        cursor.execute("SELECT COUNT(*) FROM zombies")
        self.zombie_count = cursor.fetchone()[0]
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
    async def ratio(self, ctx):
        """Returns the ratio of Humans to Zombies"""
        await self.update_counts()  # Update before showing count
        gcd = math.gcd(self.human_count, self.zombie_count)
        zombies = self.zombie_count // gcd
        humans = self.human_count // gcd
        if self.human_count == self.zombie_count:
            await ctx.send(f"There is **1** zombie for every **1** human!")
        elif zombies == 1:
            await ctx.send(f"There is **1** zombie for every **{humans}** humans!")
        elif humans == 1:
            await ctx.send(f"There are **{zombies}** zombies for every **1** human!")
        else:
            await ctx.send(f"There are **{zombies}** zombies for every **{humans}** human!")

    @commands.command()
    async def campus_map(self, ctx):
        """Posts a map of the RHUL campus to chat"""
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        else:
            try:
                await ctx.send(file=discord.File('files/campus_map.png'))
            except FileNotFoundError:
                await ctx.send("Error: Cannot find campus map image")


    @commands.command()
    async def estates_map(self, ctx):
        """Posts a map of the allowed play area to chat"""
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        else:
            try:
                await ctx.send(file=discord.File('files/play_area.png'))
            except FileNotFoundError:
                await ctx.send("Error: Cannot find play area image")

async def setup(bot):
    await bot.add_cog(GameCommands(bot))
