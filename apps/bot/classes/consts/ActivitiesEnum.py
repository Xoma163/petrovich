from enum import Enum


class ActivitiesEnum(Enum):
    TYPING = 'typing'
    UPLOAD_VIDEO = 'send_video'
    UPLOAD_PHOTO = 'send_photo'
    UPLOAD_DOCUMENT = 'send_file'
    RECORD_AUDIO = 'record_audio'
    UPLOAD_AUDIO = 'upload_audio'


TG_ACTIVITIES = {
    ActivitiesEnum.TYPING: 'typing',
    ActivitiesEnum.UPLOAD_VIDEO: 'upload_video',
    ActivitiesEnum.UPLOAD_PHOTO: 'upload_photo',
    ActivitiesEnum.UPLOAD_DOCUMENT: 'upload_document',
    ActivitiesEnum.RECORD_AUDIO: 'record_audio',
    ActivitiesEnum.UPLOAD_AUDIO: 'upload_audio',
}
