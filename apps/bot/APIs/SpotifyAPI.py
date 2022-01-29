import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


class SpotifyAPI:
    CLIENT_ID = "4d3a8a2c5c5949b8978eed0430b6e826"
    CLIENT_SECRET = "41c67af265da424d9669b5b9f46d5e7e"

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
