from apps.bot.classes.const.exceptions import PSubscribeIndexError


class SubscribeService:
    def get_data_to_add_new_subscribe(self, url: str) -> dict:
        """
        Метод по выдаче информации для добавления новой подписки
        Используется в команде для добавления подписок

        return {
            'channel_id': str,
            'playlist_id': str
            'channel_title': str,
            'playlist_title': str,
            'last_videos_id':List[str],
        }

        """
        raise NotImplementedError

    def get_filtered_new_videos(self, channel_id: str, last_videos_id: list[str], **kwargs) -> dict:
        """
        Метод по выдаче новых видео
        Используется в проверке новых подписок

        return {
            ids: list,
            titles: list,
            urls: list
        }
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
