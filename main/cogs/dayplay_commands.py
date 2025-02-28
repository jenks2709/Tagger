from discord.ext import commands

class Dayplay(commands.Cog):
    """Commands related to Dayplay rules"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def check_dayplay_rules(self, ctx):
        """Returns the ruleset for Dayplay"""
        with open("files\dayplay_rules.txt", "r", encoding="utf-8") as file_1:
            rules = file_1.read()

        await ctx.send("**📜 Dayplay Rules:**")  # Bold title
        formatted_rules = f"```\n{rules}\n```"

        # Chunking for long messages
        for chunk in [formatted_rules[i : i + 1990] for i in range(0, len(formatted_rules), 1990)]:
            await ctx.send(chunk)

# Setup function required to load the Cog
async def setup(bot):
    await bot.add_cog(Dayplay(bot))
