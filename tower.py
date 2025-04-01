import discord
from discord.ext import commands
import sqlite3
import asyncio
from datetime import datetime

# Connect to a dedicated database for the tower
conn = sqlite3.connect("tower.db")
c = conn.cursor()

# Create tower floors table if it doesn't exist
c.execute("""
CREATE TABLE IF NOT EXISTS tower_floors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    floor_number INTEGER UNIQUE,
    floor_name TEXT,
    floor_description TEXT,
    added_by_id INTEGER,
    added_by_name TEXT,
    added_at TIMESTAMP
)
""")
conn.commit()

class Tower(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="toweradd", aliases=["tnf", "addfloor"])
    async def tower_new_floor(self, ctx, *, floor_data=None):
        """Add a new floor to the tower - !toweradd Floor Name | Floor Description"""
        if not floor_data:
            await ctx.send(f"{ctx.author.mention}, you need to provide a name for your floor! Format: `!toweradd Floor Name | Floor Description`")
            return
            
        # Parse the floor name and description
        parts = floor_data.split('|', 1)
        floor_name = parts[0].strip()
        floor_description = parts[1].strip() if len(parts) > 1 else "No description provided."
            
        # Get the next floor number
        c.execute("SELECT MAX(floor_number) FROM tower_floors")
        result = c.fetchone()
        next_floor = 1 if result[0] is None else result[0] + 1
        
        # Add the new floor
        c.execute("""
        INSERT INTO tower_floors (floor_number, floor_name, floor_description, added_by_id, added_by_name, added_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (next_floor, floor_name, floor_description, ctx.author.id, ctx.author.display_name, datetime.now()))
        
        conn.commit()
        
        # Create an embed for the response
        embed = discord.Embed(
            title=f"New Floor Added: {floor_name}",
            description=f"Floor #{next_floor} has been added to the tower!",
            color=0x3498db
        )
        embed.add_field(name="Description", value=floor_description, inline=False)
        embed.add_field(name="Added by", value=ctx.author.mention, inline=True)
        embed.set_footer(text=f"The tower now has {next_floor} floors! Type !tower to see the entire tower.")
        
        await ctx.send(embed=embed)
        
    @commands.command(name="tower", aliases=["showtower", "viewtower"])
    async def show_tower(self, ctx, page: int = 1):
        """Display the tower floors with pagination"""
        # Get the total number of floors
        c.execute("SELECT COUNT(*) FROM tower_floors")
        total_floors = c.fetchone()[0]
        
        if total_floors == 0:
            await ctx.send("The tower hasn't been built yet! Use `!towernewfloor [name] | [description]` to add the first floor.")
            return
            
        # Calculate pagination
        floors_per_page = 10
        max_pages = (total_floors + floors_per_page - 1) // floors_per_page
        
        # Validate page number
        if page < 1 or page > max_pages:
            page = 1
            
        # Calculate offset
        offset = (page - 1) * floors_per_page
        
        # Get floor data for the requested page
        c.execute("""
        SELECT floor_number, floor_name, floor_description, added_by_name 
        FROM tower_floors
        ORDER BY floor_number DESC
        LIMIT ? OFFSET ?
        """, (floors_per_page, offset))
        
        floors = c.fetchall()
        
        # Create an embed for the tower display
        embed = discord.Embed(
            title="The Eternal Tower",
            description=f"A community-built tower with {total_floors} floors and counting!",
            color=0x9b59b6
        )
        
        # Add floors to the embed
        tower_text = ""
        for floor in floors:
            floor_num, name, description, added_by = floor
            tower_text += f"**Floor {floor_num}:** {name} (Added by {added_by})\n"
            
        embed.add_field(name="Floors", value=tower_text if tower_text else "No floors found", inline=False)
        embed.set_footer(text=f"Page {page}/{max_pages} • Use !tower [page] to view more floors")
        
        # Add navigation buttons
        message = await ctx.send(embed=embed)
        
        # Only add reaction controls if there are multiple pages
        if max_pages > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id
                
            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                    
                    if str(reaction.emoji) == "⬅️" and page > 1:
                        page -= 1
                    elif str(reaction.emoji) == "➡️" and page < max_pages:
                        page += 1
                    else:
                        await message.remove_reaction(reaction, user)
                        continue
                        
                    # Recalculate offset
                    offset = (page - 1) * floors_per_page
                    
                    # Get new floor data
                    c.execute("""
                    SELECT floor_number, floor_name, floor_description, added_by_name 
                    FROM tower_floors
                    ORDER BY floor_number DESC
                    LIMIT ? OFFSET ?
                    """, (floors_per_page, offset))
                    
                    floors = c.fetchall()
                    
                    # Update embed
                    tower_text = ""
                    for floor in floors:
                        floor_num, name, description, added_by = floor
                        tower_text += f"**Floor {floor_num}:** {name} (Added by {added_by})\n"
                        
                    embed.clear_fields()
                    embed.add_field(name="Floors", value=tower_text if tower_text else "No floors found", inline=False)
                    embed.set_footer(text=f"Page {page}/{max_pages} • Use !tower [page] to view more floors")
                    
                    await message.edit(embed=embed)
                    await message.remove_reaction(reaction, user)
                    
                except asyncio.TimeoutError:
                    await message.clear_reactions()
                    break
    
    @commands.command(name="towerinfo", aliases=["floorinfo"])
    async def tower_floor_info(self, ctx, floor_number: int):
        """Get detailed information about a specific floor"""
        c.execute("""
        SELECT floor_number, floor_name, floor_description, added_by_name, added_at
        FROM tower_floors
        WHERE floor_number = ?
        """, (floor_number,))
        
        floor = c.fetchone()
        
        if not floor:
            await ctx.send(f"Floor #{floor_number} doesn't exist yet! The highest floor is currently {self.get_highest_floor()}.")
            return
            
        floor_num, name, description, added_by, added_at = floor
        
        # Format the timestamp
        timestamp = datetime.strptime(added_at, "%Y-%m-%d %H:%M:%S.%f")
        formatted_time = timestamp.strftime("%B %d, %Y at %H:%M")
        
        # Create an embed for floor info
        embed = discord.Embed(
            title=f"Floor #{floor_num}: {name}",
            description=description,
            color=0x3498db
        )
        embed.add_field(name="Added by", value=added_by, inline=True)
        embed.add_field(name="Added on", value=formatted_time, inline=True)
        embed.set_footer(text=f"Use !towermodify {floor_number} [new description] to update this floor")
        
        await ctx.send(embed=embed)
    
    #@commands.command(name="towermodify", aliases=["modifyfloor"])
    #async def modify_floor(self, ctx, floor_number: int, *, new_description=None):
    #    """Modify the description of a floor"""
    #    if not new_description:
    #        await ctx.send(f"{ctx.author.mention}, you need to provide a new description!")
    #        return
    #        
    #    # Check if the floor exists
    #    c.execute("SELECT added_by_id FROM tower_floors WHERE floor_number = ?", (floor_number,))
    #    result = c.fetchone()
    #    
    #    if not result:
    #        await ctx.send(f"Floor #{floor_number} doesn't exist!")
    #        return
    #    
    #    # Update the floor description
    #    c.execute("""
    #    UPDATE tower_floors
    #    SET floor_description = ?
    #    WHERE floor_number = ?
    #    """, (new_description, floor_number))
    #    
    #    conn.commit()
    #    
    #    await ctx.send(f"Floor #{floor_number}'s description has been updated!")
        
    @commands.command(name="towerstats")
    async def tower_stats(self, ctx):
        """Display statistics about the tower"""
        # Get total floors
        c.execute("SELECT COUNT(*) FROM tower_floors")
        total_floors = c.fetchone()[0]
        
        if total_floors == 0:
            await ctx.send("The tower hasn't been built yet! Use `!towernewfloor [name] | [description]` to add the first floor.")
            return
            
        # Get top contributors
        c.execute("""
        SELECT added_by_name, COUNT(*) as floor_count
        FROM tower_floors
        GROUP BY added_by_id
        ORDER BY floor_count DESC
        LIMIT 5
        """)
        top_contributors = c.fetchall()
        
        # Create an embed for stats
        embed = discord.Embed(
            title="Tower Statistics",
            description=f"The tower currently has {total_floors} floors!",
            color=0xf1c40f
        )
        
        # Add top contributors to the embed
        contributors_text = ""
        for i, (name, count) in enumerate(top_contributors):
            rank = i + 1
            contributors_text += f"{rank}. **{name}**: {count} floors\n"
            
        embed.add_field(name="Top Contributors", value=contributors_text if contributors_text else "No contributors yet", inline=False)
        
        # Get the first and most recent floor
        c.execute("SELECT floor_number, floor_name, added_by_name FROM tower_floors ORDER BY floor_number ASC LIMIT 1")
        first_floor = c.fetchone()
        
        c.execute("SELECT floor_number, floor_name, added_by_name FROM tower_floors ORDER BY floor_number DESC LIMIT 1")
        newest_floor = c.fetchone()
        
        if first_floor:
            embed.add_field(name="Foundation (Floor #1)", value=f"**{first_floor[1]}** added by {first_floor[2]}", inline=True)
            
        if newest_floor:
            embed.add_field(name=f"Top Floor (#{newest_floor[0]})", value=f"**{newest_floor[1]}** added by {newest_floor[2]}", inline=True)
            
        await ctx.send(embed=embed)
    
    def get_highest_floor(self):
        """Helper method to get the highest floor number"""
        c.execute("SELECT MAX(floor_number) FROM tower_floors")
        result = c.fetchone()
        return result[0] if result[0] is not None else 0

# Function to setup the cog
def setup(bot):
    bot.add_cog(Tower(bot))