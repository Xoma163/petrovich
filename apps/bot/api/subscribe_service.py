class SubscribeService:
    def get_data_to_add_new_subscribe(self, url: str) -> dict:
        """
        Метод по выдаче информации для добавления новой подписки
        Используется в команде для добавления подписок

        return {
            'channel_id': str,
            'title': str,
            'last_video_id':str,
            'playlist_id': str
        }
        """
        raise NotImplementedError

    def get_filtered_new_videos(self, channel_id: str, last_video_id: str, **kwargs) -> dict:
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
