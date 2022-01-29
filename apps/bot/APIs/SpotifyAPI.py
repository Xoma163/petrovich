import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from petrovich.settings import env


class SpotifyAPI:
    CLIENT_ID = env.str("SPOTIFY_CLIENT_ID")
    CLIENT_SECRET = env.str("SPOTIFY_CLIENT_SECRET")

    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET)
        )

    def search_music(self, q, limit):
        results = self.sp.search(q=q, limit=limit, market="RU")
        return [{
            'artists': [y['name'] for y in x['artists']],
            'album': {'title': x['album']['name'], 'image': x['album']['images'][1]['url']},
            'name': x['name'],
            'url': x['external_urls']['spotify']
        } for x in results['tracks']['items']]
