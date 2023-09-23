import m3u8
import requests


class M3U8(m3u8.M3U8):
    def __init__(self, *args, load_playlists=False, load_high_quality_playlist=False, base_playlists_uri=None,
                 **kwargs, ):
        self.load_playlists = load_playlists
        self.segments = []  # PEP
        super().__init__(*args, **kwargs)
        self.playlists = PlaylistList(*self.playlists, base_playlists_uri=base_playlists_uri)

        if self.playlists:
            if load_high_quality_playlist:
                self.get_playlist_with_best_quality().load()
            elif self.load_playlists:
                self.playlists.load()

    def dumps(self, use_absolute_uri=True):
        if not use_absolute_uri:
            return super().dumps()
        if self.segments:
            self.segments = SegmentList(self.segments)
        return super().dumps()

    def dumps_bytes(self, use_absolute_uri=True):
        return str.encode(self.dumps(use_absolute_uri=use_absolute_uri))

    def get_playlist_with_best_quality(self):
        return self.playlists[-1]


class SegmentList(m3u8.SegmentList):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_absolute_uri_as_uri()

    def _set_absolute_uri_as_uri(self):
        new_list = list(map(self.__absolute_setter, self))
        super().__init__(new_list)

    @staticmethod
    def __absolute_setter(x):
        x.uri = x.absolute_uri
        return x


class PlayList(m3u8.Playlist):
    def __init__(self, *args, base_playlists_uri, **kwargs):
        super().__init__(*args, **kwargs)
        self.loaded = None
        self.base_playlists_uri = base_playlists_uri if base_playlists_uri else self.base_uri

    def load(self):
        self.loaded = M3U8(requests.get(self.absolute_uri).text, base_uri=self.base_playlists_uri)


class PlaylistList(m3u8.PlaylistList):
    def __init__(self, *args, base_playlists_uri):
        super().__init__()
        for item in args:
            stream_info = item.stream_info.__dict__
            stream_info['resolution'] = f"{stream_info['resolution'][0]}x{stream_info['resolution'][1]}"
            self.append(PlayList(item.uri, item.stream_info.__dict__, item.media, item.base_uri,
                                 base_playlists_uri=base_playlists_uri))
        self.sort_by_quality()

    def load(self):
        for x in self:
            x.load()

    def sort_by_quality(self):
        self.sort(key=lambda x: x.stream_info.resolution[0])
