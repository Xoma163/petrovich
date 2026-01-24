from enum import StrEnum


class ActivitiesEnum(StrEnum):
    TYPING = 'typing'
    UPLOAD_VIDEO = 'upload_video'
    UPLOAD_PHOTO = 'upload_photo'
    UPLOAD_DOCUMENT = 'upload_document'
    RECORD_AUDIO = 'record_audio'
    UPLOAD_AUDIO = 'upload_audio'
    UPLOAD_VIDEO_NOTE = 'upload_video_note'


TG_ACTIVITIES = {
    ActivitiesEnum.TYPING: 'typing',
    ActivitiesEnum.UPLOAD_VIDEO: 'upload_video',
    ActivitiesEnum.UPLOAD_PHOTO: 'upload_photo',
    ActivitiesEnum.UPLOAD_DOCUMENT: 'upload_document',
    ActivitiesEnum.RECORD_AUDIO: 'record_audio',
    ActivitiesEnum.UPLOAD_AUDIO: 'upload_audio',
    ActivitiesEnum.UPLOAD_VIDEO_NOTE: 'upload_video_note',
}
