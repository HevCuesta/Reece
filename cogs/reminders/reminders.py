import discord
from discord.ext import commands, tasks
import sqlite3
import asyncio
from datetime import datetime, timedelta
import re

class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "reminders.db"
        self.init_database()
        self.check_reminders.start()
        print("Reminders cog loaded")
    
    def init_database(self):
        """Initialize the reminders database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                remind_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    
    def parse_time(self, time_str):
        """Parse time string like '1h', '30m', '2d', '1h30m' into a timedelta"""
        time_str = time_str.lower().strip()
        
        # Match patterns like: 1h, 30m, 2d, 1w, 1h30m, 2d5h30m
        pattern = r'(?:(\d+)w)?(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
        match = re.match(pattern, time_str)
        
        if not match or not any(match.groups()):
            return None
        
        weeks = int(match.group(1) or 0)
        days = int(match.group(2) or 0)
        hours = int(match.group(3) or 0)
        minutes = int(match.group(4) or 0)
        seconds = int(match.group(5) or 0)
        
        return timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
    
    @commands.command(name="remindme", aliases=["remind", "reminder"])
    async def remind_me(self, ctx, time: str, *, message: str = "Something!"):
        """Set a reminder. Usage: !remindme <time> <message>
        Time format: 1w (week), 1d (day), 1h (hour), 1m (minute), 1s (second)
        You can combine them: 1d12h30m"""
        
        delta = self.parse_time(time)
        
        if delta is None:
            await ctx.send(
                f"{ctx.author.mention}, invalid time format! Use formats like: "
                "`1h`, `30m`, `2d`, `1w`, `1h30m`, `2d5h`"
            )
            return
        
        # Check if time is too short or too long
        if delta.total_seconds() < 10:
            await ctx.send(f"{ctx.author.mention}, reminder must be at least 10 seconds!")
            return
        
        if delta.total_seconds() > 365 * 24 * 60 * 60:  # 1 year
            await ctx.send(f"{ctx.author.mention}, reminder can't be more than 1 year!")
            return
        
        remind_at = datetime.utcnow() + delta
        created_at = datetime.utcnow()
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reminders (user_id, channel_id, message, remind_at, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (ctx.author.id, ctx.channel.id, message, remind_at.isoformat(), created_at.isoformat()))
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Create embed
        embed = discord.Embed(
            title="⏰ Reminder Set!",
            description=f"I'll remind you about: **{message}**",
            color=discord.Color.green()
        )
        embed.add_field(name="When", value=f"<t:{int(remind_at.timestamp())}:R>", inline=False)
        embed.set_footer(text=f"Reminder ID: {reminder_id}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="reminders", aliases=["myreminders", "listreminders"])
    async def list_reminders(self, ctx):
        """List all your active reminders"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, message, remind_at
            FROM reminders
            WHERE user_id = ?
            ORDER BY remind_at ASC
        """, (ctx.author.id,))
        reminders = cursor.fetchall()
        conn.close()
        
        if not reminders:
            await ctx.send(f"{ctx.author.mention}, you have no active reminders!")
            return
        
        embed = discord.Embed(
            title=f"⏰ {ctx.author.display_name}'s Reminders",
            color=discord.Color.blue()
        )
        
        for reminder_id, message, remind_at_str in reminders[:10]:  # Limit to 10
            remind_at = datetime.fromisoformat(remind_at_str)
            timestamp = int(remind_at.timestamp())
            embed.add_field(
                name=f"ID: {reminder_id}",
                value=f"{message}\n<t:{timestamp}:R>",
                inline=False
            )
        
        if len(reminders) > 10:
            embed.set_footer(text=f"Showing 10 of {len(reminders)} reminders")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="cancelreminder", aliases=["deletereminder", "rmreminder"])
    async def cancel_reminder(self, ctx, reminder_id: int):
        """Cancel a reminder by ID. Usage: !cancelreminder <id>"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if reminder exists and belongs to user
        cursor.execute("""
            SELECT id FROM reminders
            WHERE id = ? AND user_id = ?
        """, (reminder_id, ctx.author.id))
        
        if cursor.fetchone() is None:
            conn.close()
            await ctx.send(f"{ctx.author.mention}, reminder not found or doesn't belong to you!")
            return
        
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()
        conn.close()
        
        await ctx.send(f"✅ {ctx.author.mention}, reminder #{reminder_id} has been cancelled!")
    
    @tasks.loop(seconds=30)
    async def check_reminders(self):
        """Background task to check for due reminders"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.utcnow()
            cursor.execute("""
                SELECT id, user_id, channel_id, message, created_at
                FROM reminders
                WHERE remind_at <= ?
            """, (now.isoformat(),))
            
            due_reminders = cursor.fetchall()
            
            for reminder_id, user_id, channel_id, message, created_at_str in due_reminders:
                try:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        user = await self.bot.fetch_user(user_id)
                        
                        created_at = datetime.fromisoformat(created_at_str)
                        time_ago = int(created_at.timestamp())
                        
                        embed = discord.Embed(
                            title="⏰ Reminder!",
                            description=f"{user.mention}, you asked me to remind you:",
                            color=discord.Color.gold()
                        )
                        embed.add_field(name="Message", value=message, inline=False)
                        embed.add_field(name="Set", value=f"<t:{time_ago}:R>", inline=False)
                        
                        await channel.send(embed=embed)
                    
                    # Delete the reminder
                    cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
                    conn.commit()
                    
                except Exception as e:
                    print(f"Error sending reminder {reminder_id}: {e}")
                    # Still delete the reminder even if sending fails
                    cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
                    conn.commit()
            
            conn.close()
        except Exception as e:
            print(f"Error in check_reminders: {e}")
    
    @check_reminders.before_loop
    async def before_check_reminders(self):
        """Wait until the bot is ready before starting the task"""
        await self.bot.wait_until_ready()
    
    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        self.check_reminders.cancel()

async def setup(bot):
    await bot.add_cog(Reminders(bot))
