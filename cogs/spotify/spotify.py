# spotify.py
import discord
from discord.ext import commands
from cogs.spotify.spotify_auth import get_spotify_client
import re
import asyncio
import traceback

PLAYLIST_ID = "1R2zNS22jWAEsfeJWUiqyk"

class SpotifyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sp = None
        # Initialize Spotify in the background to avoid blocking
        self.bot.loop.create_task(self.initialize_spotify())
        
    async def initialize_spotify(self):
        """Initialize Spotify client in the background"""
        try:
            # Run the Spotify authentication in a separate thread to avoid blocking
            self.sp = await self.bot.loop.run_in_executor(None, get_spotify_client)
            print("Spotify client initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Spotify: {e}")
            traceback.print_exc()

    async def ensure_spotify_client(self):
        """Ensure we have a working Spotify client"""
        if self.sp is None:
            await asyncio.sleep(2)  # Give some time for initialization
            if self.sp is None:
                raise Exception("Spotify client not initialized. Please check authentication.")
        return self.sp
            

    @commands.command(name="addsong")
    async def add_song(self, ctx, *, query: str):
        """Adds a song to the Spotify playlist. Accepts search terms or a Spotify track link."""
        try:
            # Get Spotify client
            sp = await self.ensure_spotify_client()

            # Show "typing" indicator while processing
            async with ctx.typing():
                # Check if query is a Spotify track URL or URI
                match = re.match(r'(https?://open\.spotify\.com/track/|spotify:track:)([a-zA-Z0-9]+)', query)
                if match:
                    track_id = match.group(2)
                    uri = f"spotify:track:{track_id}"
                    # Get track details
                    track = sp.track(uri)
                else:
                    # Perform search
                    result = sp.search(q=query, type='track', limit=1)
                    if not result['tracks']['items']:
                        await ctx.send("❌ No song found with that query. Try with more specific search terms.")
                        return
                    track = result['tracks']['items'][0]
                    uri = track['uri']

                # Add the track to the playlist
                sp.playlist_add_items(PLAYLIST_ID, [uri])

                # Create an embed for better display
                embed = discord.Embed(
                    title="✅ Song Added",
                    description=f"Successfully added to playlist:",
                    color=0x1DB954  # Spotify green
                )
                embed.add_field(name="Song", value=track['name'], inline=True)
                embed.add_field(name="Artist", value=track['artists'][0]['name'], inline=True)

                # Add album art if available
                if track['album']['images']:
                    embed.set_thumbnail(url=track['album']['images'][0]['url'])

                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
            traceback.print_exc()

    @commands.command(name="playlist")
    async def list_songs(self, ctx):
        await ctx.send("https://open.spotify.com/playlist/1R2zNS22jWAEsfeJWUiqyk?si=5d3eba2d4df04a26")

    @commands.command(name="search")
    async def search_song(self, ctx, *, query: str):
        """Search for a song on Spotify."""
        try:
            # Get Spotify client
            sp = await self.ensure_spotify_client()
            
            # Show "typing" indicator while processing
            async with ctx.typing():
                # Search for the track
                result = sp.search(q=query, type='track', limit=5)
                
                if not result['tracks']['items']:
                    await ctx.send("❌ No songs found with that query.")
                    return
                    
                # Create an embed
                embed = discord.Embed(
                    title=f"🔍 Search results for '{query}'",
                    color=0x1DB954  # Spotify green
                )
                
                # Add top 5 results
                for i, track in enumerate(result['tracks']['items'], 1):
                    artists = ", ".join([artist['name'] for artist in track['artists']])
                    embed.add_field(
                        name=f"{i}. {track['name']}", 
                        value=f"by {artists} - from {track['album']['name']}", 
                        inline=False
                    )
                    
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(SpotifyCog(bot))