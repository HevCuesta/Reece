import discord
from discord.ext import commands
import asyncio
import datetime
import random

class AnonymousControl(commands.Cog):
    """Cog to allow users to control the bot anonymously for a limited time"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_controllers = {}  # {user_id: (channel_id, end_time)}
        self.control_duration = 300  # Default duration: 5 minutes (in seconds)
        self.cooldown = 1800  # Cooldown between uses: 30 minutes (in seconds)
        self.user_cooldowns = {}  # {user_id: end_cooldown_time}
        self.is_processing = False
        self.available_channels = {}  # {guild_id: [channel_ids]} - Channels where anonymous control is allowed
        self.initial_message_sent = set()  # Set to track users who have already received the initial message
        print("Anonymous Control Cog loaded")
        
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from the bot itself
        if message.author.bot:
            return
        
        # If it's a direct message (DM) to the bot
        if isinstance(message.channel, discord.DMChannel):
            user_id = message.author.id
            
            # If it's a command to request anonymous control
            if message.content.startswith("!anoncontrol") or message.content.startswith("!acontrol"):
                await self.handle_anon_control_request(message)
                return
                
            # If it's a message from a user with active control
            elif user_id in self.active_controllers and message.content.startswith("!a "):
                await self.handle_anonymous_message(message)
                return
                
            # If the user hasn't received the initial instruction message yet
            elif user_id not in self.initial_message_sent:
                self.initial_message_sent.add(user_id)
                help_embed = discord.Embed(
                    title="🎭 Anonymous Control System",
                    description="You can use the following commands in this private chat:",
                    color=discord.Color.blue()
                )
                help_embed.add_field(
                    name="Request anonymous control", 
                    value="To request anonymous control in a server:\n`!anoncontrol <server_id> <channel_id> [duration]`\n\nExample: `!anoncontrol 123456789 987654321 180`", 
                    inline=False
                )
                help_embed.add_field(
                    name="List servers and channels", 
                    value="To view available servers and channels:\n`!anonlist`", 
                    inline=False
                )
                help_embed.set_footer(text="Your privacy is guaranteed - no other user will know who is controlling the bot.")
                await message.channel.send(embed=help_embed)
                return
    
    async def handle_anon_control_request(self, message):
        """Handles anonymous control requests sent via DM"""
        parts = message.content.split()
        user_id = message.author.id
        current_time = datetime.datetime.now()
        
        # Check command format
        if len(parts) < 3:
            # If only !anoncontrol is written, show available servers and channels
            if len(parts) == 1:
                await self.list_available_channels(message)
                return
            await message.channel.send("❌ Incorrect format. Usage: `!anoncontrol <server_id> <channel_id> [duration]`")
            return
        
        # Check if the user is on cooldown
        if user_id in self.user_cooldowns:
            cooldown_end = self.user_cooldowns[user_id]
            if current_time < cooldown_end:
                remaining = (cooldown_end - current_time).total_seconds()
                await message.channel.send(f"⏱️ You must wait {int(remaining)} more seconds before requesting anonymous control again.")
                return
        
        # Check if there is already an active controller
        if self.active_controllers:
            await message.channel.send("❌ Someone is already controlling the bot anonymously. Try again later.")
            return
        
        try:
            # Get server and channel IDs
            guild_id = int(parts[1])
            channel_id = int(parts[2])
            
            # Check if the bot has access to the server and channel
            guild = self.bot.get_guild(guild_id)
            if not guild:
                await message.channel.send("❌ I don't have access to that server or the ID is invalid.")
                return
                
            channel = guild.get_channel(channel_id)
            if not channel:
                await message.channel.send("❌ I can't find that channel in the specified server.")
                return
            
            # Check bot permissions in the channel
            bot_member = guild.get_member(self.bot.user.id)
            if not channel.permissions_for(bot_member).send_messages:
                await message.channel.send("❌ I don't have permission to send messages in that channel.")
                return
                
            # Set the duration (with a maximum)
            if len(parts) >= 4 and parts[3].isdigit():
                duration = min(int(parts[3]), self.control_duration)
            else:
                duration = self.control_duration
                
            # Configure control
            end_time = current_time + datetime.timedelta(seconds=duration)
            self.active_controllers[user_id] = (channel_id, end_time)
            
            # Inform the user via DM
            control_key = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
            
            dm_embed = discord.Embed(
                title="Anonymous Control Activated",
                description=f"You can now control the bot anonymously for {duration} seconds.",
                color=discord.Color.green()
            )
            dm_embed.add_field(name="Server", value=f"{guild.name}", inline=True)
            dm_embed.add_field(name="Channel", value=f"#{channel.name}", inline=True)
            dm_embed.add_field(name="Remaining time", value=f"{duration} seconds", inline=True)
            dm_embed.add_field(name="How to use", value="Send me messages via DM starting with `!a` and I will forward them anonymously to the channel.", inline=False)
            dm_embed.add_field(name="Session key", value=f"`{control_key}`", inline=False)
            dm_embed.set_footer(text="Your identity is hidden. Use responsibly.")
            
            await message.channel.send(embed=dm_embed)
            
            
            # Start timer to end control
            self.bot.loop.create_task(self.end_control_after_duration(user_id, duration))
            
        except ValueError:
            await message.channel.send("❌ Server and channel IDs must be integers.")
        except Exception as e:
            await message.channel.send(f"❌ Error activating anonymous control: {str(e)}")
            
    async def handle_anonymous_message(self, message):
        """Handles messages sent by a user with anonymous control"""
        user_id = message.author.id
        channel_id, _ = self.active_controllers[user_id]
        channel = self.bot.get_channel(channel_id)
        
        if channel:
            # Extract content without the prefix
            content = message.content[3:]
            
            # Check for attachments
            files = []
            for attachment in message.attachments:
                file = await attachment.to_file()
                files.append(file)
            
            # Send the anonymous message
            embed = discord.Embed(
                description=content,
                color=discord.Color.dark_purple()
            )
            embed.set_footer(text="Anonymous message")
            
            try:
                if files:
                    await channel.send(embed=embed, files=files)
                else:
                    await channel.send(embed=embed)
                await message.add_reaction("✅")
            except Exception as e:
                await message.channel.send(f"❌ Error sending anonymous message: {str(e)}")
        else:
            await message.channel.send("❌ Could not find the channel. Anonymous control has been deactivated.")
            del self.active_controllers[user_id]
            
    async def list_available_channels(self, channel):
        """Shows the user the list of available servers and channels"""
        embed = discord.Embed(
            title="🔍 Available Servers and Channels",
            description="You can request anonymous control in the following servers and channels:",
            color=discord.Color.blue()
        )
        
        # Get all servers where the bot is present
        guilds = self.bot.guilds
        
        if not guilds:
            embed.description = "I am not currently in any servers."
            await channel.send(embed=embed)
            return
            
        for guild in guilds:
            # Get text channels where the bot can send messages
            text_channels = []
            for channel_item in guild.text_channels:
                bot_permissions = channel_item.permissions_for(guild.me)
                if bot_permissions.send_messages and bot_permissions.embed_links:
                    text_channels.append(channel_item)
            
            if text_channels:
                channel_list = "\n".join([f"• #{channel_item.name}: `{channel_item.id}`" for channel_item in text_channels[:5]])
                if len(text_channels) > 5:
                    channel_list += f"\n• ... and {len(text_channels) - 5} more"
                    
                embed.add_field(
                    name=f"📁 {guild.name} (`{guild.id}`)",
                    value=channel_list,
                    inline=False
                )
        
        embed.set_footer(text="Use !anoncontrol <server_id> <channel_id> [duration] to start")
        await channel.send(embed=embed)
        
    async def end_control_after_duration(self, user_id, duration, channel_msg):
        """Ends control after the specified duration"""
        await asyncio.sleep(duration)
        
        if user_id in self.active_controllers:
            channel_id, _ = self.active_controllers[user_id]
            channel = self.bot.get_channel(channel_id)
            
            # Remove from the list of active controllers
            del self.active_controllers[user_id]
            
            # Set cooldown for the user
            cooldown_end = datetime.datetime.now() + datetime.timedelta(seconds=self.cooldown)
            self.user_cooldowns[user_id] = cooldown_end
            
            # Notify the user
            user = self.bot.get_user(user_id)
            if user:
                await user.send("Your anonymous control time has ended. You can request control again after the cooldown period.")
    
    @commands.command(name="anonconfig", aliases=["aconfig"])
    @commands.has_permissions(administrator=True)
    async def config_anon_control(self, ctx, setting: str, value: int = None):
        """Configures anonymous control parameters (admin only)
        
        Args:
            setting: The parameter to configure ('duration', 'cooldown', 'status')
            value: The new value in seconds (not needed for 'status')
        """
        if setting.lower() == "duration" and value is not None:
            self.control_duration = value
            await ctx.send(f"✅ Anonymous control duration set to {value} seconds.")
        elif setting.lower() == "cooldown" and value is not None:
            self.cooldown = value
            await ctx.send(f"✅ Cooldown between uses set to {value} seconds.")
        elif setting.lower() == "status":
            # Show current configuration status
            embed = discord.Embed(
                title="⚙️ Anonymous Control Configuration",
                color=discord.Color.blue()
            )
            embed.add_field(name="Maximum duration", value=f"{self.control_duration} seconds", inline=True)
            embed.add_field(name="Cooldown time", value=f"{self.cooldown} seconds", inline=True)
            
            # Show active controller if exists
            if self.active_controllers:
                active_count = len(self.active_controllers)
                embed.add_field(
                    name="Current status", 
                    value=f"There are {active_count} active session(s)", 
                    inline=False
                )
            else:
                embed.add_field(name="Current status", value="No active sessions", inline=False)
                
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Unknown parameter or missing value. Use 'duration <seconds>', 'cooldown <seconds>' or 'status'.")
    
    @commands.command(name="anonstop")
    @commands.has_permissions(administrator=True)
    async def stop_anon_control(self, ctx):
        """Stops any active anonymous control sessions (admin only)"""
        if not self.active_controllers:
            await ctx.send("❌ There are no active anonymous control sessions.")
            return
        
        # Notify active users
        for user_id in list(self.active_controllers.keys()):
            user = self.bot.get_user(user_id)
            if user:
                await user.send("⚠️ An administrator has ended your anonymous control session.")
            
            # Set cooldown
            cooldown_end = datetime.datetime.now() + datetime.timedelta(seconds=self.cooldown)
            self.user_cooldowns[user_id] = cooldown_end
        
        # Clear the list of controllers
        self.active_controllers.clear()
        await ctx.send("✅ All anonymous control sessions have been terminated.")
        
    @commands.command(name="anonlist", aliases=["alist"])
    async def list_channels_command(self, ctx):
        """Shows the channels where anonymous control can be used"""
        # If it's a server, delete the command and send via DM
        if not isinstance(ctx.channel, discord.DMChannel):
            try:
                await ctx.message.delete()
            except:
                pass
            await ctx.author.send("Here is the list of available servers and channels:")
            await self.list_available_channels(await ctx.author.create_dm())
        else:
            # If it's already a DM, just show the list
            await self.list_available_channels(ctx.channel)

async def setup(bot):
    """Setup function to load the cog"""
    await bot.add_cog(AnonymousControl(bot))
