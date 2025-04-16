from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()

def get_spotify_client():
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_SECRET"),
        redirect_uri="http://localhost:8888/callback",  # o lo que tengas registrado
        scope="playlist-modify-public playlist-modify-private",
        cache_path="token_cache.json",
        open_browser=False  # ¡Evita que abra Firefox!
    )

    return Spotify(auth_manager=auth_manager)
