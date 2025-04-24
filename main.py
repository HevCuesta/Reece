import discord
from discord.ext import commands
import sqlite3
import matplotlib.pyplot as plt
import fortune as fortune_module
from datetime import datetime
import time
import pytz
import io
import asyncio
from cogs.tower.tower import Tower
from cogs.tower.tower_viz import TowerVisualization
from cogs.spotify.spotify import setup as setup_spotify
from cogs.eight_ball.eight_ball import EightBall
from cogs.points_items.points import PointsItemsCog
import os
from dotenv import load_dotenv
import random
import json


load_dotenv()

# Bot configuration
TOKEN = os.getenv('DISCORD_KEY')
PREFIX = "!"

bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all(), help_command=None)


# Connect to SQLite database
conn = sqlite3.connect("points.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS points (
    user_id INTEGER PRIMARY KEY,
    points REAL DEFAULT 0.0
)
""")
c.execute("""
CREATE TABLE IF NOT EXISTS inventory (
    user_id INTEGER,
    item TEXT,
    quantity INTEGER DEFAULT 1,
    PRIMARY KEY (user_id, item)
)
""")
conn.commit()

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    await bot.add_cog(Tower(bot))
    await bot.add_cog(TowerVisualization(bot))
    await bot.add_cog(EightBall(bot))
    await bot.add_cog(PointsItemsCog(bot, conn, c))
    await setup_spotify(bot)

    print('Tower cogs loaded')

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

# Load responses from data/8ball.json
def load_8ball_responses():
    try:
        with open("data/8ball.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("standard_responses", []), data.get("custom_responses", [])
    except FileNotFoundError:
        print("Warning: data/8ball.json not found. Using default responses.")
        # Default responses if file not found
        return [], []
    except json.JSONDecodeError:
        print("Error: Could not parse data/8ball.json. Using default responses.")
        return [], []

# Load greetings from file
def load_greetings():
    try:
        with open("data/greetings.txt", "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("Warning: data/greetings.txt not found. Using default greetings.")
        # Default greetings as fallback
        return [
            "hey there, {}!",
            "hello, {}!",
            "hi, {} how's it going",
            "yo, {}"
        ]
        
def load_facts():
    try:
        with open("data/funfacts.txt", "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("Warning: data/funfacts.txt not found. Using default facts.")
        # Default facts as fallback
        return [
            "Did you know? Honey never spoils.",
            "Bananas are berries, but strawberries aren't.",
            "A group of flamingos is called a 'flamboyance'.",
            "Octopuses have three hearts."
        ]
        

# Load greetings when bot starts
greetings = load_greetings()
facts = load_facts()
MAGIC_8BALL_RESPONSES, CUSTOM_RESPONSES = load_8ball_responses()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Evita que el bot se responda a sí mismo
        
    cst = pytz.timezone('US/Central')
    current_time = datetime.now(cst)
    lower_content = message.content.lower()
    
    morning_responses = [
        "good morning, {}! Hope you have a great day!",
        "Rise and shine, {}!",
        "Morning, {}! Have you had your coffee yet?",
        "Top of the morning to you, {}!"
    ]
    
    if 6 <= current_time.hour < 12:
        if any(phrase in lower_content for phrase in ["hi reece", "hello reece", "gm reece", "good morning reece"]):
            response = random.choice(morning_responses).format(message.author.mention)
            await message.channel.send(response)
        
    else:
        if any(phrase in lower_content for phrase in ["hi reece", "hello reece"]):
            response = random.choice(greetings).format(message.author.mention)
            await message.channel.send(response)
    
    if "do a backflip reece" in lower_content or "reece do a backflip" in lower_content:
        await message.channel.send("🤸")
        time.sleep(0.5)
        await message.channel.send("Ta-da!")
    
    if "fuck you reece" in lower_content:
        await message.channel.send("One should always aim high. Set your aspirations beyond your reach and you will always have something to strive for.")
    
    # Nuevas interacciones divertidas
    if "tell me a joke reece" in lower_content:
        jokes = [
            "Why don't programmers like nature? It has too many bugs!",
            "What do you call 8 hobbits? A hob-byte!",
            "Why did the computer catch a cold? It left its Windows open!",
            "I told my wife she should embrace her mistakes. She gave me a hug."
        ]
        await message.channel.send(random.choice(jokes))

    if "gn reece" in lower_content or "good night reece" in lower_content or "goodnight reece" in lower_content:
        await message.channel.send("Good night, {}".format(message.author.mention))
    
    if "what's your favorite color reece" in lower_content or "reece what is your favorite color" in lower_content or "what is your favorite color reece" in lower_content:
        await message.channel.send("I like #00FF00, it's a very refreshing shade of green!")
    
    if "who made you reece" in lower_content:
        await message.channel.send("I was created by some wonderful humans with way too much time on their hands!")
    
    if "reece tell me a fun fact" in lower_content or "tell me a fun fact reece" in lower_content:
        await message.channel.send(random.choice(facts))
    
    await bot.process_commands(message)  # Permite que los comandos sigan funcionando



if __name__ == "__main__":
    
    bot.run(TOKEN)
    
