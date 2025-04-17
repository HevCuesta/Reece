from spotipy import Spotify
from spotipy.oauth2 import SpotifyPKCE
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
REDIRECT_URI = "http://localhost:8888/callback"
SCOPE = "playlist-modify-public playlist-modify-private"
CACHE_PATH = "token_cache.json"

def get_spotify_client():
    auth_manager = SpotifyPKCE(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=CACHE_PATH,
        open_browser=True
    )

    # This triggers token fetching/refresh if needed
    token = auth_manager.get_access_token()

    if not token:
        raise Exception("Failed to obtain a Spotify access token.")

    return Spotify(auth_manager=auth_manager)
