import discord
from discord.ext import commands
import sqlite3
import os
# Tag graph imports:
import networkx as nx
import matplotlib.pyplot as plt
import pydot
from networkx.drawing.nx_pydot import graphviz_layout
from networkx.readwrite import json_graph

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
        tags = cursor.fetchall() # Get tags from database 

        self.tag_history = [] # Clear the internal tag history 
        for tag in tags: # Repopulate the internal tag history
            self.tag_history.append((tag[1], tag[0]))
        conn.close()

    async def render_tag_graph(self, ctx):
        """Generates an image containing a graph of the current tag history"""
        
        guild = ctx.guild
        clean_tag_history = []
        for tag in self.tag_history:
            clean_tag_history.append([guild.get_member(int(tag[0])), guild.get_member(int(tag[1]))]) # Convert the userIDs in the tags into human readable usernames

        tag_graph = nx.DiGraph()
        tag_graph.add_edges_from(clean_tag_history)

        fig = plt.figure("Tag History", facecolor="#5393f3")
        fig.set_figwidth(10) #TODO: set the width of the diagram to scale with height divided by total nodes 
        fig.set_figheight(10) #TODO: set the height of the diagram to scale with the height of the tag tree
        fig.suptitle("Tag History", fontsize="xx-large", fontweight="bold")
        
        plt.xlabel("RHUL Humans vs Zombies", fontsize="xx-large", color="white")# add a label to the bottom of the diagram

        layout = graphviz_layout(tag_graph, prog="dot") # defines positions of nodes to use a hierarchical layout

        nx.draw_networkx(tag_graph, pos=layout, arrows=True, with_labels=True, arrowsize=25, node_size=900, font_size=20, font_color="#0000cc", node_color="#FFC442", node_shape="h", arrowstyle="->", width=2, edge_color="#5C5CD3") # renders tag graph

        ax = plt.gca()
        ax.set_facecolor("#FFC442") # sets the graph background color to orange

        plt.savefig("files/tag_graph_image.png", dpi=200) # save the graph to file
        plt.clf() # resets the internal plot to empty

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
        if self.tag_history == []:
            await ctx.send("Sorry, I can't generate an image if no tags have occurred")
        else:
            await self.render_tag_graph(ctx)
            try:
                await ctx.send(file=discord.File('files/tag_graph_image.png'))
            except FileNotFoundError:
                await ctx.send("Error: Cannot find tag tree image")




async def setup(bot):
    await bot.add_cog(GameCommands(bot))
