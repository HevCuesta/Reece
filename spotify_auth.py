# spotify_auth.py
import spotipy
from spotipy.oauth2 import SpotifyPKCE
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
REDIRECT_URI = "http://127.0.0.1:9090"
SCOPE = "playlist-modify-public playlist-read-private playlist-modify-private"
CACHE_PATH = os.path.join(os.path.expanduser("~"), ".spotify_token_pkce")

def get_spotify_client():
    """Get a Spotify client using PKCE authentication flow"""
    try:
        auth_manager = SpotifyPKCE(
            client_id=CLIENT_ID,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            cache_path=CACHE_PATH,
            open_browser=True
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        print("Spotify client initialized successfully using PKCE flow")
        return sp
    except Exception as e:
        print(f"Failed to initialize Spotify client with PKCE: {e}")
        raise