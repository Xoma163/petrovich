from enum import StrEnum


class ChatActionEnum(StrEnum):
    TYPING = 'typing'
    UPLOAD_VIDEO = 'upload_video'
    UPLOAD_PHOTO = 'upload_photo'
    UPLOAD_DOCUMENT = 'upload_document'
    RECORD_AUDIO = 'record_audio'
    UPLOAD_AUDIO = 'upload_audio'
    UPLOAD_VIDEO_NOTE = 'upload_video_note'


TG_CHAT_ACTIONS = {
    ChatActionEnum.TYPING: 'typing',
    ChatActionEnum.UPLOAD_VIDEO: 'upload_video',
    ChatActionEnum.UPLOAD_PHOTO: 'upload_photo',
    ChatActionEnum.UPLOAD_DOCUMENT: 'upload_document',
    ChatActionEnum.RECORD_AUDIO: 'record_audio',
    ChatActionEnum.UPLOAD_AUDIO: 'upload_audio',
    ChatActionEnum.UPLOAD_VIDEO_NOTE: 'upload_video_note',
}
