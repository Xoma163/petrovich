from enum import Enum


class ActivitiesEnum(Enum):
    TYPING = 'typing'
    UPLOAD_VIDEO = 'send_video'
    UPLOAD_PHOTO = 'send_photo'
    RECORD_AUDIO = 'record_audio'


TG_ACTIVITIES = {
    ActivitiesEnum.TYPING: 'typing',
    ActivitiesEnum.UPLOAD_VIDEO: 'upload_video',
    ActivitiesEnum.UPLOAD_PHOTO: 'upload_photo',
    ActivitiesEnum.RECORD_AUDIO: 'record_audio',
}

VK_ACTIVITIES = {
    ActivitiesEnum.TYPING: 'typing',
    ActivitiesEnum.RECORD_AUDIO: 'audiomessage',
}
