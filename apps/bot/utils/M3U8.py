import m3u8


class M3U8(m3u8.M3U8):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.playlists.sort(key=lambda x: x.stream_info.resolution[0])

    def dumps(self, use_absolute_uri=True):
        if not use_absolute_uri:
            return super().dumps()
        if self.segments:
            self.segments = SegmentList(self.segments)
        return super().dumps()

    def dumps_bytes(self, use_absolute_uri=True):
        return str.encode(self.dumps(use_absolute_uri=use_absolute_uri))


class SegmentList(m3u8.SegmentList):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_absolute_uri_as_uri()

    def _set_absolute_uri_as_uri(self):
        new_list = list(map(self.__absolute_setter, self))
        super().__init__(new_list)

    def __absolute_setter(self, x):
        x.uri = x.absolute_uri
        return x
