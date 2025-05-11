import dataclasses


@dataclasses.dataclass
class VideoData:
    title: str
    description: str | None = None
    video_id: str | int | None = None
    channel_id: str | int | None = None
    channel_title: str | None = None
    video_download_url: str | None = None
    video_download_chunk_size: int | None = None
    audio_download_url: str | None = None
    audio_download_chunk_size: int | None = None
    filesize: int | None = None
    duration: int | None = None
    width: int | None = None
    height: int | None = None
    start_pos: str | None = None
    end_pos: str | None = None
    thumbnail_url: str | None = None
    filename: str | None = None
    m3u8_master_url: str | None = None
    extra_data: dict | None = None  # to save smth in context
    is_short_video: bool | None = None


@dataclasses.dataclass
class AudioData:
    artists: str
    title: str
    duration: int | None = None
    thumbnail_url: str | None = None
    format: str | None = None
    content: bytes | None = None
    download_url: str | None = None
    text: str | None = None
