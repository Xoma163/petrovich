import dataclasses

from apps.bot.classes.const.exceptions import PSubscribeIndexError


@dataclasses.dataclass
class SubscribeServiceData:
    channel_id: str
    playlist_id: str
    channel_title: str
    playlist_title: str
    last_videos_id: list[str]
    service: int


@dataclasses.dataclass
class SubscribeServiceNewVideoData:
    id: str | int
    title: str
    url: str


@dataclasses.dataclass
class SubscribeServiceNewVideosData:
    videos: list[SubscribeServiceNewVideoData]

    @property
    def ids(self):
        return [x.id for x in self.videos]

    @property
    def titles(self):
        return [x.title for x in self.videos]

    @property
    def urls(self):
        return [x.url for x in self.videos]


class SubscribeService:
    def get_channel_info(self, url: str) -> SubscribeServiceData:
        """
        Метод по выдаче информации для добавления новой подписки
        Используется в команде для добавления подписок
        Может распознавать плейлист
        """
        raise NotImplementedError

    def get_filtered_new_videos(
            self,
            channel_id: str,
            last_videos_id: list[str],
            **kwargs
    ) -> SubscribeServiceNewVideosData:
        """
        Метод по выдаче новых видео
        Используется в проверке новых подписок
        """
        raise NotImplementedError

    @staticmethod
    def filter_by_id(ids, last_videos_id):
        for last_video_id in reversed(last_videos_id):
            try:
                return ids.index(last_video_id) + 1
            except ValueError:
                continue
        raise PSubscribeIndexError(ids)
