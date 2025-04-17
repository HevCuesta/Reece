import discord
from discord.ext import commands
import sqlite3
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance, ImageTransform, ImageChops
import io
from datetime import datetime
import random
import math


class TowerVisualization(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect("tower.db")
        self.c = self.conn.cursor()
        
    @commands.command(name="seetower", aliases=["renderfloors", "visualize", "breakcore"])
    async def render_tower(self, ctx, max_floors: int = 10):
        """Generate a breakcore-themed visual representation of the tower floors"""
        # Get total floors in the database
        self.c.execute("SELECT COUNT(*) FROM tower_floors")
        total_floors = self.c.fetchone()[0]
        
        if total_floors == 0:
            await ctx.send("The tower hasn't been built yet! Use `!towernewfloor [name] | [description]` to add the first floor.")
            return
        
        # Limit the maximum number of floors to display
        display_floors = min(total_floors, max_floors)
        
        # Get the floors to display (most recent/highest floors first)
        self.c.execute("""
        SELECT floor_number, floor_name, added_by_name 
        FROM tower_floors
        ORDER BY floor_number DESC
        LIMIT ?
        """, (display_floors,))
        
        floors = self.c.fetchall()
        
        # Create the tower image
        await ctx.send("Rendering the tower... This may take a moment.")
        tower_image = await self.create_breakcore_tower_image(floors, total_floors)
        
        # Send the image to Discord
        file = discord.File(tower_image, filename="breakcore_tower.png")
        embed = discord.Embed(
            title="TOWER OF PAIN",
            description=f"The tower now has {total_floors} floors.",
            color=0xff00ff
        )
        embed.set_image(url="attachment://breakcore_tower.png")
        embed.set_footer(text=f"Showing {display_floors} out of {total_floors} floors • Generated on {datetime.now().strftime('%B %d, %Y')}")
        
        await ctx.send(file=file, embed=embed)
    
    async def create_breakcore_tower_image(self, floors, total_floors):
        """Creates a breakcore-themed tower image with the specified floors"""
        # Image dimensions and settings
        width = 800
        height = 1200
        
        # Breakcore color palette - vibrant, contrasting colors
        bg_color = (0, 0, 0)  # Black background
        neon_colors = [
            (255, 0, 255),    # Magenta
            (0, 255, 255),    # Cyan 
            (255, 255, 0),    # Yellow
            (0, 255, 0),      # Green
            (255, 0, 0),      # Red
            (0, 0, 255)       # Blue
        ]
        
        # Create a new image with a black background
        image = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(image)
        
        # Draw glitchy background patterns
        self.draw_breakcore_background(draw, width, height, neon_colors)
        
        # Try to load fonts, fall back to default if not available
        try:
            title_font = ImageFont.truetype("arial.ttf", 60)
            subtitle_font = ImageFont.truetype("arial.ttf", 30)
            floor_font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            # Use default font if truetype fonts are not available
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            floor_font = ImageFont.load_default()
        
        # Draw glitchy title
        self.draw_glitch_text(draw, width // 2, 80, "THE ETERNAL TOWER", title_font, neon_colors)
        self.draw_glitch_text(draw, width // 2, 130, f"{total_floors} FLOORS OF CHAOS", subtitle_font, neon_colors)
        
        # Calculate tower dimensions
        tower_width = 300
        tower_height = 800
        tower_x = (width - tower_width) // 2
        tower_y = height - tower_height - 100  # Leave space at bottom
        
        # Draw glitchy tower outline
        self.draw_glitch_tower_outline(draw, tower_x, tower_y, tower_width, tower_height, neon_colors)
        
        # Draw floors (windows) from bottom to top
        floor_display_count = len(floors)
        floor_height = min(40, (tower_height - 150) / floor_display_count)
        spacing = 30
        
        # Calculate entrance position
        entrance_height = 10
        entrance_y = height - 120 - entrance_height
        
        for i, floor in enumerate(reversed(floors)):  # Reverse to start from bottom
            floor_number, floor_name, added_by = floor
            
            # Calculate floor position with some random offset for glitch effect
            x_offset = random.randint(-1, 1)
            floor_y = entrance_y - (i + 1) * (floor_height + spacing) + random.randint(-1, 1)
            
            # Draw floor with glitch effect
            window_width = tower_width - 80 + random.randint(-20, 20)
            window_x = tower_x + (tower_width - window_width) // 2 + x_offset
            
            # Pick a random neon color for this floor
            floor_color = random.choice(neon_colors)
            
            # Draw distorted floor rectangle
            points = [
                (window_x, floor_y),
                (window_x + window_width, floor_y),
                (window_x + window_width + random.randint(-10, 10), floor_y + floor_height),
                (window_x + random.randint(-10, 10), floor_y + floor_height)
            ]
            draw.polygon(points, fill=floor_color)
            
            # Add scanlines effect to floor
            for y in range(int(floor_y), int(floor_y + floor_height), 2):
                draw.line([(window_x, y), (window_x + window_width, y)], fill=(0, 0, 0), width=1)
            
            # Draw floor text with glitch effect
            floor_text = f"FLOOR {floor_number}: {floor_name}"
            # Truncate long floor names
            if len(floor_text) > 25:
                floor_text = floor_text[:22] + "..."
            
            # Draw text with small offsets for glitch effect
            text_y = floor_y + floor_height // 2
            draw.text((window_x + window_width // 2 + 2, text_y - 1), floor_text, fill=(0, 0, 0), font=floor_font, anchor="mm")
            draw.text((window_x + window_width // 2 - 2, text_y + 1), floor_text, fill=(255, 255, 255), font=floor_font, anchor="mm")
            draw.text((window_x + window_width // 2, text_y), floor_text, fill=(255, 255, 255), font=floor_font, anchor="mm")
        

        
        # Convert to bytes for Discord upload
        byte_arr = io.BytesIO()
        image.save(byte_arr, format='PNG')
        byte_arr.seek(0)
        
        return byte_arr
    
    def draw_breakcore_background(self, draw, width, height, colors):
        """Draw a chaotic breakcore-style background"""
        # Draw random geometric shapes
        for _ in range(50):
            shape = random.choice(['line', 'rect', 'circle', 'triangle'])
            color = random.choice(colors)
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            
            if shape == 'line':
                x2 = random.randint(0, width)
                y2 = random.randint(0, height)
                draw.line([(x1, y1), (x2, y2)], fill=color, width=random.randint(1, 5))
            
            elif shape == 'rect':
                w = random.randint(20, 100)
                h = random.randint(20, 100)
                draw.rectangle([(x1, y1), (x1 + w, y1 + h)], outline=color, width=2)
            
            elif shape == 'circle':
                r = random.randint(10, 50)
                draw.ellipse([(x1 - r, y1 - r), (x1 + r, y1 + r)], outline=color, width=2)
            
            elif shape == 'triangle':
                x2 = x1 + random.randint(-100, 100)
                y2 = y1 + random.randint(-100, 100)
                x3 = x1 + random.randint(-100, 100)
                y3 = y1 + random.randint(-100, 100)
                draw.polygon([(x1, y1), (x2, y2), (x3, y3)], outline=color, width=2)
        
        # Draw grid patterns
        grid_spacing = random.randint(20, 40)
        for x in range(0, width, grid_spacing):
            opacity = random.randint(50, 150)
            color = (*random.choice(colors)[:3], opacity)
            draw.line([(x, 0), (x, height)], fill=color, width=1)
        
        for y in range(0, height, grid_spacing):
            opacity = random.randint(50, 150)
            color = (*random.choice(colors)[:3], opacity)
            draw.line([(0, y), (width, y)], fill=color, width=1)
    
    def draw_glitch_text(self, draw, x, y, text, font, colors):
        """Draw text with a glitchy effect"""
        # Draw multiple layers with small offsets
        for i in range(3):
            offset_x = random.randint(-1, 0)
            offset_y = random.randint(-1, 0)
            color = random.choice(colors)
            draw.text((x + offset_x, y + offset_y), text, fill=color, font=font, anchor="mm")
        
        # Draw main text on top
        draw.text((x, y), text, fill=(255, 255, 255), font=font, anchor="mm")
    
    def draw_glitch_tower_outline(self, draw, x, y, width, height, colors):
        """Draw a glitchy tower outline"""
        # Base tower shape with jagged edges
        points = []
        segments = 20
        segment_height = height / segments
        
        for i in range(segments + 1):
            y_pos = y + i * segment_height
            left_jitter = random.randint(-15, 15) if i > 0 and i < segments else 0
            right_jitter = random.randint(-15, 15) if i > 0 and i < segments else 0
            
            points.append((x + left_jitter, y_pos))
            
        for i in range(segments, -1, -1):
            y_pos = y + i * segment_height
            right_jitter = random.randint(-15, 15) if i > 0 and i < segments else 0
            
            points.append((x + width + right_jitter, y_pos))
            
        # Draw the tower outline multiple times with different colors
        for i in range(3):
            # Create a slightly distorted copy of the points
            distorted_points = [(p[0] + random.randint(-5, 5), p[1] + random.randint(-5, 5)) for p in points]
            draw.polygon(distorted_points, outline=random.choice(colors), fill=None, width=2)
        
        # Draw the main outline
        draw.polygon(points, outline=(255, 255, 255), fill=None, width=3)
        
        # Add some random horizontal glitch lines across the tower
        for _ in range(10):
            y_pos = random.randint(y, y + height)
            color = random.choice(colors)
            line_width = random.randint(2, 6)
            draw.line([(x - 20, y_pos), (x + width + 20, y_pos)], fill=color, width=line_width)
    
    def apply_breakcore_effects(self, image):
        """Apply post-processing effects to create a breakcore aesthetic"""
        processed = image.copy()
        
        # Apply glitch effects
        # 1. Create random RGB channel shifts
        channels = processed.split()
        if len(channels) >= 3:  # Make sure we have RGB channels
            # Shift red channel
            r_shift = ImageChops.offset(channels[0], random.randint(-10, 10), random.randint(-10, 10))
            # Shift blue channel
            b_shift = ImageChops.offset(channels[2], random.randint(-10, 10), random.randint(-10, 10))
            
            # Replace channels
            channels = [r_shift, channels[1], b_shift]
            processed = Image.merge('RGB', channels)
        
        # 2. Add noise 
        for _ in range(50):
            x = random.randint(0, processed.width - 1)
            y = random.randint(0, processed.height - 1)
            w = random.randint(5, 20)
            h = random.randint(1, 5)
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            
            # Create a small rectangle of noise
            noise = Image.new('RGB', (w, h), color)
            processed.paste(noise, (x, y))
        
        # 3. Add scan lines
        draw = ImageDraw.Draw(processed)
        for y in range(0, processed.height, 4):
            draw.line([(0, y), (processed.width, y)], fill=(0, 0, 0), width=1)
        
        # 4. Enhance contrast
        enhancer = ImageEnhance.Contrast(processed)
        processed = enhancer.enhance(1.5)
        
        return processed


def setup(bot):
    bot.add_cog(TowerVisualization(bot))