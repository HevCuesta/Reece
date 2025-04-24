import discord
from discord.ext import commands
import random
import json
import asyncio

class EightBall(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.standard_responses, self.custom_responses = self.load_8ball_responses()
        print("8Ball cog loaded")
    
    def load_8ball_responses(self):
        try:
            with open("data/8ball.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                return data.get("standard_responses", []), data.get("custom_responses", [])
        except FileNotFoundError:
            print("Warning: data/8ball.json not found. Using default responses.")
            return [], []
        except json.JSONDecodeError:
            print("Error: Could not parse data/8ball.json. Using default responses.")
            return [], []
    
    @commands.command(name="8ball", aliases=["magic8", "8b", "magic8ball"])
    async def magic_8ball(self, ctx, *, question=None):
        """Ask the Magic 8-Ball a question!"""
        if not question:
            await ctx.send(f"{ctx.author.mention}, you need to ask a question")
            return
            
        # Small chance of getting a custom response
        if random.random() < 0.1:  # 10% chance for custom response
            response = random.choice(self.custom_responses)
        else:
            response = random.choice(self.standard_responses)
        
        # Create an embed for the response
        embed = discord.Embed(
            description=f"**Question:** {question}",
            color=response["color"]
        )
        
        # Add a thinking delay for effect
        async with ctx.typing():
            await asyncio.sleep(1.5)  # Simulates "thinking"
        
        embed.add_field(name="The 8-Ball says:", value=response["text"], inline=False)
        
        # Add a small flavor text based on response type
        if response["type"] == "positive":
            embed.set_footer(text="!!!!!!!")
        elif response["type"] == "negative":
            embed.set_footer(text="idk man dont blame me...")
        else:
            embed.set_footer(text="youch...")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EightBall(bot))
