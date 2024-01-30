import spotipy
import yt_dlp
from spotipy import SpotifyClientCredentials

from apps.bot.api.youtube.music import YoutubeMusic
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.nothing_logger import NothingLogger
from petrovich.settings import env


class Spotify:
    CLIENT_ID = env.str("SPOTIFY_CLIENT_ID")
    CLIENT_SECRET = env.str("SPOTIFY_CLIENT_SECRET")

    def __init__(self):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=self.CLIENT_ID, client_secret=self.CLIENT_SECRET
            )
        )

    def get_info(self, track_id):
        track = self.sp.track(track_id=track_id)
        artists = ", ".join([artist["name"] for artist in track['artists']])

        ydl = yt_dlp.YoutubeDL({'logger': NothingLogger()})
        query = f"{artists} - {track['name']}"
        data = ydl.extract_info(f"ytsearch:{query}", False)
        if not data['entries']:
            raise PWarning("Не справился, сори((")
        yt_url = data['entries'][0]['original_url']

        ytm_api = YoutubeMusic()
        data = ytm_api.get_info(yt_url)
        data['artists'] = artists
        data['title'] = track['name']
        data['cover_url'] = track['album']['images'][-1]['url']
        return data
