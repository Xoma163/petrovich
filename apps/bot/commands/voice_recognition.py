from apps.bot.api.gpt.chatgpt import ChatGPTAPI
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import AcceptExtraCommand
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.const.exceptions import PSkip
from apps.bot.classes.event.event import Event
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.videonote import VideoNoteAttachment
from apps.bot.classes.messages.attachments.voice import VoiceAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.audio_converter import AudioConverter
from apps.service.models import GPTUsage


class VoiceRecognition(AcceptExtraCommand):
    name = 'распознай'
    names = ["голос", "голосовое"]

    help_text = HelpText(
        commands_text="распознаёт голосовое сообщение",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand("(Пересланное сообщение с голосовым сообщением)",
                                    "распознаёт голосовое сообщение на основе ChatGPT")
            ])
        ],
        extra_text=(
            "Если дан доступ к переписке и указан gpt api key, то распознает автоматически"
        )
    )

    platforms = [Platform.TG]
    attachments = [VoiceAttachment, VideoNoteAttachment, AudioAttachment]
    priority = -100

    bot: TgBot
    gpt_key = True

    def accept_extra(self, event: Event) -> bool:
        if event.has_voice_message or event.has_video_note:
            # check gpt key
            if not event.sender.check_role(Role.TRUSTED) and not event.sender.settings.gpt_key:
                return False

            if event.is_from_chat and event.chat.settings.recognize_voice:
                return True
            elif event.is_from_pm:
                return True
            else:
                raise PSkip()
        return False

    def start(self) -> ResponseMessage:
        audio_messages = self.event.get_all_attachments([VoiceAttachment, VideoNoteAttachment, AudioAttachment])
        audio_message = audio_messages[0]
        audio_mp3 = AudioConverter.convert(audio_message, 'mp3')
        audio_message.content = audio_mp3

        chat_gpt_api = ChatGPTAPI(sender=self.event.sender)
        answer: str = chat_gpt_api.recognize_voice(audio_message)

        GPTUsage(
            author=self.event.sender,
            voice_recognition_seconds=chat_gpt_api.usage['duration'],
            cost=chat_gpt_api.usage['voice_recognition_cost'] * chat_gpt_api.usage['duration']
        ).save()

        answer = self.spoiler_text(answer)

        return ResponseMessage(ResponseMessageItem(text=answer, reply_to=self.event.message.id))

    def spoiler_text(self, answer: str) -> str:
        spoiler_text = "спойлер"

        if spoiler_text in answer.lower():
            spoiler_index = answer.lower().index(spoiler_text)
            text_before_spoiler = answer[:spoiler_index]
            text_after_spoiler = answer[spoiler_index + len(spoiler_text):]

            answer = text_before_spoiler + self.bot.get_bold_text(spoiler_text) + self.bot.get_spoiler_text(
                text_after_spoiler)
        return answer
