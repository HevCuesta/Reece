import discord
from discord.ext import commands
import fortune as fortune_module
from cogs.tower.tower import Tower
from cogs.tower.tower_viz import TowerVisualization
from cogs.spotify.spotify import setup as setup_spotify
from cogs.eight_ball.eight_ball import EightBall
from cogs.points_items.points_items import PointsItemsCog
from cogs.autoresponses.autoresponses import AutoResponses
from cogs.anon.anonymous_control import AnonymousControl
import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
TOKEN = os.getenv('DISCORD_KEY')
PREFIX = "!"

bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all(), help_command=None)


# Loads cogs components
@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    await bot.add_cog(Tower(bot))
    await bot.add_cog(TowerVisualization(bot))
    await bot.add_cog(EightBall(bot))
    await bot.add_cog(PointsItemsCog(bot))
    await bot.add_cog(AutoResponses(bot))
    await bot.add_cog(AnonymousControl(bot))
    await setup_spotify(bot)

@bot.command()
async def fortune(ctx):
    # Get a random fortune from the module
    fortune_text = fortune_module.fortune()
    await ctx.send(fortune_text)

@bot.command()
async def help(ctx):
    """Displays a list of available commands"""
    help_text = (
        "**Available Commands:**\n"
        "!points [@user] - Displays the points and items of a user (or yourself if no user is mentioned)\n"
        "!addpoints @user <amount> - Adds points to a user\n"
        "!removepoints @user <amount> - Removes points from a user\n"
        "!giveitem @user <quantity> <item> - Gives an item to a user\n"
        "!ranking - Displays the top 10 users with the most points and a chart\n"
        "!8ball <question> - Ask a question, and the ball shall answer\n"
        "!tower - See what floors the tower has\n"
        "!toweradd <Floor Name> | <Floor Description> - Add a floor to the tower\n"
        "!towerinfo <Floor number> - Get details about a floor\n"
        "!towerstats - Get tower statistics\n"
        "!seetower - GET A GLIMPSE AT THE TOWER OF HORROR\n"
        "!playlist - Check out the official Magma Sphere Spotify playlist\n"
        "!addsong <query> - Add a song to the Spotify playlist"
       )
    
    # Split help message into chunks if it exceeds Discord's message length limit
    MAX_LENGTH = 2000
    while len(help_text) > MAX_LENGTH:
        await ctx.send(help_text[:MAX_LENGTH])
        help_text = help_text[MAX_LENGTH:]
    
    # Send any remaining part of the help text
    await ctx.send(help_text)

if __name__ == "__main__":
    bot.run(TOKEN)
