import discord
from discord.ext import commands
import random

class Magic8Ball(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("data/8ball_responses.txt") as f:
            self.responses = [line.strip() for line in f if line.strip()]

    @commands.command(name='8ball')
    async def eight_ball(self, ctx, *, question: str):
        response = random.choice(self.responses)
        await ctx.send(f'🎱 {response}')

def setup(bot):
    bot.add_cog(Magic8Ball(bot))
