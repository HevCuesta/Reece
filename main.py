import discord
from discord.ext import commands
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
import time
import pytz
import io

# Bot configuration
TOKEN = "MTM1NDUzMjYzMzU0NzExNjc4Nw.GOwVUO.7DP5CAsfNwwJrjHKN8VT05q3Dmzp9kQNlL3r6Y"
PREFIX = "!"

bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all())

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

@bot.command(name="commands")
async def commands_list(ctx):
    """Displays a list of available commands"""
    help_text = (
        "**Available Commands:**\n"
        "!points [@user] - Displays the points and items of a user (or yourself if no user is mentioned)\n"
        "!addpoints @user <amount> - Adds points to a user\n"
        "!removepoints @user <amount> - Removes points from a user\n"
        "!giveitem @user <quantity> <item> - Gives an item to a user\n"
        "!ranking - Displays the top 10 users with the most points and a chart"
    )
    
    # Split help message into chunks if it exceeds Discord's message length limit
    MAX_LENGTH = 2000
    while len(help_text) > MAX_LENGTH:
        await ctx.send(help_text[:MAX_LENGTH])
        help_text = help_text[MAX_LENGTH:]
    
    # Send any remaining part of the help text
    await ctx.send(help_text)

import random

greetings = [
    "hey there, {}!", 
    "hello, {}!", 
    "hi, {} how's it going", 
    "yo, {}", 
    "sup, {}?", 
    "greetings, {}", 
    "hola, {}", 
    "hey hey, {}"
]

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Evita que el bot se responda a sí mismo
        
    cst = pytz.timezone('US/Central')
    current_time = datetime.now(cst)

    if 6 <= current_time.hour < 12:
        if "hi reece" in message.content.lower():
            response = "good morning, {}".format(message.author.mention)
            await message.channel.send(response)

        if "hello reece" in message.content.lower():
            response = "good morning, {}".format(message.author.mention)
            await message.channel.send(response)
        
        if "gm reece" in message.content.lower():
            response = "good morning, {}".format(message.author.mention)
            await message.channel.send(response)
            
        if "good morning reece" in message.content.lower():
            response = "good morning, {}".format(message.author.mention)
            await message.channel.send(response)
    else:
        if "hi reece" in message.content.lower():
            response = random.choice(greetings).format(message.author.mention)
            await message.channel.send(response)
        if "hello reece" in message.content.lower():
            response = random.choice(greetings).format(message.author.mention)
            await message.channel.send(response)

    
    if "do a backflip reece" in message.content.lower():
        response = random.choice(greetings).format(message.author.mention)
        await message.channel.send("🤸")
        time.sleep(0.5)
        await message.channel.send("Ta-da!")

    if "reece do a backflip" in message.content.lower():
        response = random.choice(greetings).format(message.author.mention)
        await message.channel.send("🤸")
        time.sleep(0.5)
        await message.channel.send("Ta-da!")



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