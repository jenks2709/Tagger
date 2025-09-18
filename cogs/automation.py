import discord
from discord.ext import commands
import asyncio
import time
from datetime import datetime
import sqlite3

class Automation(commands.Cog):
    
    def __init__(self, bot):
        pass

    @commands.command()
    async def announcements(self, ctx):
        
        if ctx.channel.name != "bot-commands":
            await ctx.send("This command can only be used in `#bot-commands`.")
            return
        guild = ctx.guild
        human_channel = discord.utils.get(guild.text_channels, name="human-announcements")
        zombie_channel = discord.utils.get(guild.text_channels, name="zombie-announcements")
        dayplay_channel = discord.utils.get(guild.text_channels, name="dayplay-announcements")

        human = discord.utils.get(guild.roles, name="Human")
        zombie = discord.utils.get(guild.roles, name="Zombie")
        player = discord.utils.get(guild.roles, name="Player")

        async def dayplay_announcements(message, wait_seconds):
            await asyncio.sleep(wait_seconds)
            if isinstance(message, discord.File):
                await dayplay_channel.send(file=message)
            else:
                await dayplay_channel.send(message)


        async def human_announcements(message, wait_seconds):
            
            await asyncio.sleep(wait_seconds)
            await human_channel.send(message)


        async def zombie_announcements(message, wait_seconds):
            await asyncio.sleep(wait_seconds)
            await zombie_channel.send(message)
        
        # Define messages and their corresponding Unix timestamps in a 2-tuple
        friday_schedule = [] 

        current_time = int(time.time())

        for message, target_timestamp in friday_schedule:
            wait_seconds = target_timestamp - current_time
            if wait_seconds > 0:
                asyncio.create_task(dayplay_announcements(message, wait_seconds))
            else:
                pass
        
        saturday_schedule = []

        for message, target_timestamp in saturday_schedule:
            wait_seconds = target_timestamp - current_time
            if wait_seconds > 0:
                if isinstance(message, str) and message.endswith((".jpg", ".png", ".gif")):
                    asyncio.create_task(dayplay_announcements(discord.File(message), wait_seconds))
                else:
                    asyncio.create_task(dayplay_announcements(message, wait_seconds))
                
        sunday_schedule = []

        for message, target_timestamp in sunday_schedule:
            wait_seconds = target_timestamp - current_time
            if wait_seconds > 0:
                if isinstance(message, str) and message.endswith((".jpg", ".png", ".gif")):
                    asyncio.create_task(dayplay_announcements(discord.File(message), wait_seconds))
                else:
                    asyncio.create_task(dayplay_announcements(message, wait_seconds))
        
        monday_schedule = []

        for message, target_timestamp in monday_schedule:
            wait_seconds = target_timestamp - current_time
            if wait_seconds > 0:
                asyncio.create_task(dayplay_announcements(message, wait_seconds))
            else:
                pass
        
        tuesday_schedule = []

        for message, target_timestamp in tuesday_schedule:
            wait_seconds = target_timestamp - current_time
            if wait_seconds > 0:
                asyncio.create_task(dayplay_announcements(message, wait_seconds))
            else:
                pass
        
        wednesday_schedule = []

        for message, target_timestamp in wednesday_schedule:
            wait_seconds = target_timestamp - current_time
            if wait_seconds > 0:
                asyncio.create_task(dayplay_announcements(message, wait_seconds))
            else:
                pass

        await ctx.send("Dayplay Announcements have been scheduled!")
        
                   
        human_schedule = []

        zombie_schedule = []


        for message, target_timestamp in human_schedule:
            wait_seconds = target_timestamp - current_time
            if wait_seconds > 0:
                asyncio.create_task(human_announcements(message, wait_seconds))
            else:
                pass
        await ctx.send("Human Briefing Announcements have been scheduled!")

        for message, target_timestamp in zombie_schedule:
            wait_seconds = target_timestamp - current_time
            if wait_seconds > 0:
                asyncio.create_task(zombie_announcements(message, wait_seconds))
            else:
                pass
        await ctx.send("Zombie Briefing Announcements have been scheduled!")
        

async def setup(bot):
    await bot.add_cog(Automation(bot))
