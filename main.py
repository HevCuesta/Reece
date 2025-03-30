import discord
from discord.ext import commands
import sqlite3
import matplotlib.pyplot as plt
import fortune as fortune_module
from datetime import datetime
import time
import pytz
import io
from random import choice, randint
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests
import asyncio


# List of Magic 8-Ball responses
MAGIC_8BALL_RESPONSES = [
    # Positive answers
    {"text": "It is certain.", "type": "positive", "color": 0x2ecc71},
    {"text": "It is decidedly so.", "type": "positive", "color": 0x2ecc71},
    {"text": "Without a doubt.", "type": "positive", "color": 0x2ecc71},
    {"text": "Yes – definitely.", "type": "positive", "color": 0x2ecc71},
    {"text": "You may rely on it.", "type": "positive", "color": 0x2ecc71},
    {"text": "As I see it, yes.", "type": "positive", "color": 0x2ecc71},
    {"text": "Most likely.", "type": "positive", "color": 0x2ecc71},
    {"text": "Outlook good.", "type": "positive", "color": 0x2ecc71},
    {"text": "Yes.", "type": "positive", "color": 0x2ecc71},
    {"text": "Signs point to yes.", "type": "positive", "color": 0x2ecc71},
    
    # Neutral answers
    {"text": "Reply hazy, try again.", "type": "neutral", "color": 0xe67e22},
    {"text": "Ask again later.", "type": "neutral", "color": 0xe67e22},
    {"text": "Better not tell you now.", "type": "neutral", "color": 0xe67e22},
    {"text": "Cannot predict now.", "type": "neutral", "color": 0xe67e22},
    {"text": "Concentrate and ask again.", "type": "neutral", "color": 0xe67e22},
    
    # Negative answers
    {"text": "Don't count on it.", "type": "negative", "color": 0xe74c3c},
    {"text": "My reply is no.", "type": "negative", "color": 0xe74c3c},
    {"text": "My sources say no.", "type": "negative", "color": 0xe74c3c},
    {"text": "Outlook not so good.", "type": "negative", "color": 0xe74c3c},
    {"text": "Very doubtful.", "type": "negative", "color": 0xe74c3c},
]

# Custom responses that can randomly appear (rare)
CUSTOM_RESPONSES = [
    {"text": "The stars align in your favor... but Mercury is in retrograde, so...", "type": "neutral", "color": 0x9b59b6},
    {"text": "Ask me again when I've had my coffee.", "type": "neutral", "color": 0x9b59b6},
    {"text": "Absolutely! ...wait, what was the question again?", "type": "positive", "color": 0x9b59b6},
    {"text": "The answer lies within you. Or maybe Google.", "type": "neutral", "color": 0x9b59b6},
    {"text": "42. That's always the answer.", "type": "positive", "color": 0x9b59b6},
    {"text": "My crystal ball is in the shop. Try tomorrow.", "type": "neutral", "color": 0x9b59b6},
    {"text": "The spirits are whispering... but I don't speak ghost.", "type": "neutral", "color": 0x9b59b6},
    {"text": "All signs point to maybe. Or possibly not. One of those.", "type": "neutral", "color": 0x9b59b6},
    {"text": "I'm legally obligated to say no to that question.", "type": "negative", "color": 0x9b59b6},
    {"text": "Let me think... ERROR: ILLEGAL OPERATION: THINKING", "type": "negative", "color": 0x9b59b6},
]

import random

# Bot configuration
TOKEN = "MTM1NDUzMjYzMzU0NzExNjc4Nw.GOwVUO.7DP5CAsfNwwJrjHKN8VT05q3Dmzp9kQNlL3r6Y"
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

@bot.command(name="8ball", aliases=["magic8", "8b", "magic8ball"])
async def magic_8ball(ctx, *, question=None):
    """Ask the Magic 8-Ball a question!"""
    if not question:
        await ctx.send(f"{ctx.author.mention}, you need to ask a question! Try `!8ball Will I have good luck today?`")
        return
        
    # Small chance of getting a custom response
    if random.random() < 0.1:  # 10% chance for custom response
        response = random.choice(CUSTOM_RESPONSES)
    else:
        response = random.choice(MAGIC_8BALL_RESPONSES)
    
    # Create an embed for the response
    embed = discord.Embed(
        title="🔮 Magic 8-Ball",
        description=f"**Question:** {question}",
        color=response["color"]
    )
    
    # Add a thinking delay for effect
    async with ctx.typing():
        await asyncio.sleep(1.5)  # Simulates "thinking"
    
    embed.add_field(name="The 8-Ball says:", value=response["text"], inline=False)
    
    # Add a small flavor text based on response type
    if response["type"] == "positive":
        embed.set_footer(text="Looks like the universe is on your side!")
    elif response["type"] == "negative":
        embed.set_footer(text="Don't shoot the messenger...")
    else:
        embed.set_footer(text="The future is cloudy...")
    
    await ctx.send(embed=embed)




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
        "!8ball <question> - Ask a question, and the ball shall answer"
    )
    
    # Split help message into chunks if it exceeds Discord's message length limit
    MAX_LENGTH = 2000
    while len(help_text) > MAX_LENGTH:
        await ctx.send(help_text[:MAX_LENGTH])
        help_text = help_text[MAX_LENGTH:]
    
    # Send any remaining part of the help text
    await ctx.send(help_text)


greetings = [
    "hey there, {}!", 
    "hello, {}!", 
    "hi, {} how's it going", 
    "yo, {}", 
    "sup, {}?", 
    "greetings, {}", 
    "hola, {}", 
    "hey hey, {}",
    "how now, brown cow?",
    "how do you do, {}?",
    "salutations, {}",
    "how have you been, {}?",
    "to whom it may concern",
    "it's great to see you, {}",
    "nice to see you, {}",
    "Hello Sue, how are you?",
    "Long time no see, {}",
    "Well hello {}",
    "Oh My God….I did NOT expect to see you here, {}!",
    "A nod (with nothing actually spoken)",
    "how's the weather over there, {}?",
    "what's the story, {}?",
    "what's the word on the street, {}?",
    "why are you like this?",
    "please don't talk to me right now.",
    "aloha, {}! (this one means hello AND goodbye)",
    "salam alaykum, {}",
    "こんにちは、{}ーさん！",
    "Ciao",
    "glück auf, {}",
    "Blessings be upon your family, {}.",
    "Have you accepted Jesus Christ as your lord and savior, {}?",
    "Interfaith greetings in Indonesia",
    "Shalom, {}",
    "Happy Holidays, {}",
    "Wazzapppp!!!",
    "want to watch me do a backflip, {}?",
    "hey hey, {}, it's my birthday today!",
    "what's happening, {}?",
    "hey {}, want to join my secret telegram channel?"
]

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
    
    if "how are you reece" in lower_content:
        responses = [
            "I'm just a bot, but I'm feeling electric! ⚡",
            "Doing great! Thanks for asking, {}!".format(message.author.mention),
            "I am 01001000 01100001 01110000 01110000 01111001! (That means happy in binary)"
        ]
        await message.channel.send(random.choice(responses))
    
    if "what's your favorite color reece" in lower_content or "reece what is your favorite color" in lower_content or "what is your favorite color reece" in lower_content:
        await message.channel.send("I like #00FF00, it's a very refreshing shade of green!")
    
    if "who made you reece" in lower_content:
        await message.channel.send("I was created by some wonderful humans with way too much time on their hands!")
    
    if "reece tell me a fun fact" in lower_content or "tell me a fun fact reece" in lower_content:
        facts = [
            "Did you know that honey never spoils? Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3000 years old and still perfectly edible!",
            "Bananas are berries, but strawberries aren't!",
            "Octopuses have three hearts and their blood is blue!",
            "A group of flamingos is called a 'flamboyance'!"
        ]
        await message.channel.send(random.choice(facts))
    
    await bot.process_commands(message)  # Permite que los comandos sigan funcionando



@bot.command()
async def points(ctx, member: discord.Member = None):
    """Displays a user's points and items"""
    user_id = member.id if member else ctx.author.id
    c.execute("SELECT points FROM points WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    points = result[0] if result else 0.0

    c.execute("SELECT item, quantity FROM inventory WHERE user_id = ?", (user_id,))
    items = c.fetchall()
    items_text = ", ".join([f"{item} x{quantity}" for item, quantity in items]) if items else "No items"
    
    await ctx.send(f"{member.mention if member else ctx.author.mention} has {points} points and items: {items_text}.")

@points.error
async def points_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found. Please mention a valid user.")



@bot.command()
async def addpoints(ctx, member: discord.Member, amount: float):
    """Adds (or removes) points from a user"""
    if amount >= 50:
        await ctx.send("Do not give more than 50 points at a time")
        return
    # Allow negative amounts to be added or subtracted from the user's points
    c.execute("INSERT INTO points (user_id, points) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET points = points + ?", (member.id, amount, amount))
    conn.commit()
    await ctx.send(f"{ctx.author.mention} gave {amount} points to {member.mention}.")

@addpoints.error
async def addpoints_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found. Please mention a valid user.")

@bot.command()
async def removepoints(ctx, member: discord.Member, amount: float):
    """Removes (or adds) points from a user"""
    if amount >= 50:
        await ctx.send("Do not give more than 50 points at a time")
        return
    # Allow negative amounts to be removed (add negative points)
    c.execute("INSERT INTO points (user_id, points) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET points = points - ?", (member.id, 0.0, amount))
    conn.commit()
    await ctx.send(f"{ctx.author.mention} removed {amount} points from {member.mention}.")


@removepoints.error
async def removepoints_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found. Please mention a valid user.")


@bot.command()
async def giveitem(ctx, member: discord.Member, quantity: int, *, item: str):
    """Gives an item to a user - !giveitem @user <quantity> <item name>"""
    c.execute("INSERT INTO inventory (user_id, item, quantity) VALUES (?, ?, ?) ON CONFLICT(user_id, item) DO UPDATE SET quantity = quantity + ?", (member.id, item, quantity, quantity))
    conn.commit()
    await ctx.send(f"{ctx.author.mention} gave {member.mention} {quantity} {item}.")

@bot.command()
async def removeitem(ctx, member: discord.Member, quantity: int, *, item: str):
    """Removes an item from a user - !removeitem @user <quantity> <item name>"""
    c.execute("UPDATE inventory SET quantity = MAX(0, quantity - ?) WHERE user_id = ? AND item = ?", (quantity, member.id, item))
    c.execute("DELETE FROM inventory WHERE user_id = ? AND item = ? AND quantity = 0", (member.id, item))
    conn.commit()
    await ctx.send(f"{ctx.author.mention} removed {quantity} {item} from {member.mention}.")

@giveitem.error
async def giveitem_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found. Please mention a valid user.")

@bot.command()
async def ranking(ctx):
    """Displays the top 10 users with the most points and sends a styled table"""
    c.execute("SELECT user_id, points FROM points ORDER BY points DESC LIMIT 10")
    ranking = c.fetchall()
    if not ranking:
        await ctx.send("No points data available.")
        return
    
    # Prepare data for the table
    table_data = []
    for user_id, points in ranking:
        try:
            member = await ctx.guild.fetch_member(user_id)
            if not member:  # If the member is not in the guild
                raise Exception("Member not found")
        except Exception:
            member = None  # If member not found, set it to None
            member_name = "Unknown Member"
        else:
            member_name = member.display_name
        
        # Get the user's items
        c.execute("SELECT item, quantity FROM inventory WHERE user_id = ?", (user_id,))
        items = c.fetchall()
        items_text = ", ".join([f"{item} x{quantity}" for item, quantity in items]) if items else "No items"
        table_data.append([member_name, points, items_text])

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Hide axes
    ax.axis("off")

    # Create the table with headers
    table = ax.table(cellText=table_data, colLabels=["User", "Points", "Items"], loc="center", cellLoc='center')

    # Styling the table
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 1.2)  # Scale the table for better readability

    # Set the header style
    for (i, j), cell in table.get_celld().items():
        if i == 0:
            cell.set_fontsize(14)
            cell.set_text_props(weight='bold')
            cell.set_facecolor('#4CAF50')  # Header background color
            cell.set_edgecolor('black')
        else:
            cell.set_edgecolor('gray')  # Set the border color of each cell
            cell.set_facecolor('#f2f2f2')  # Cell background color

    # Set alternating row colors
    for i, row in enumerate(table.get_celld().values()):
        if i % 2 == 1:  # Change background color for alternating rows
            row.set_facecolor('#e6e6e6')

    # Add a title to the table
    plt.title("Top 10 Users by Points", fontsize=16, fontweight='bold')

    # Save the table to a buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    plt.close()

    # Send the styled table as an image
    file = discord.File(buffer, filename="ranking.png")
    await ctx.send("Here is the leaderboard table:", file=file)






bot.run(TOKEN)