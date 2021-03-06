from datetime import datetime

from apps.bot.classes.Consts import Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import normalize_datetime, get_attachments_for_upload, localize_datetime
from apps.service.models import LaterMessage, LaterMessageSession


class Later(CommonCommand):
    name = "потом"
    names = ["позже"]
    help_text = "добавляет сообщения и вложения из пересланных сообщений, чтобы посмотреть потом"
    help_texts = [
        "(Пересланные сообщения) - добавляет сообщения и вложения из пересланных сообщений чтобы посмотреть потом",
        "1 (Пересланные сообщения) - добавляет сообщения и вложения из пересланных сообщений ПО ОДНОМУ чтобы посмотреть потом",
        "- присылает последние сохранённые сообщения и удалет их из базы"
    ]
    platforms = [Platform.VK]

    def _append_message_to_lms(self, fwd, lms):
        lm = LaterMessage(
            text=fwd['text'],
            date=normalize_datetime(
                datetime.fromtimestamp(fwd['date']), "UTC"))

        if fwd['from_id'] > 0:
            lm.message_author = self.bot.get_user_by_id(fwd['from_id'])
        else:
            lm.message_bot = self.bot.get_bot_by_id(fwd['from_id'])

        attachments = self.event.parse_attachments(fwd['attachments'])
        if attachments:
            lm.attachments = attachments
        lm.save()
        lms.later_messages.add(lm)

    def start(self):
        if self.event.fwd:
            if self.event.args:
                if self.event.args[0] == '1':
                    for fwd in self.event.fwd:
                        lms = LaterMessageSession()
                        lms.date = localize_datetime(datetime.utcnow(), "UTC")
                        lms.author = self.event.sender
                        lms.save()
                        self._append_message_to_lms(fwd, lms)
                        lms.save()
                else:
                    raise PWarning("Не понял аргумента")
            else:
                lms = LaterMessageSession()
                lms.date = localize_datetime(datetime.utcnow(), "UTC")
                lms.author = self.event.sender
                lms.save()
                for fwd in self.event.fwd:
                    self._append_message_to_lms(fwd, lms)
                lms.save()
            return "Сохранил"
        else:
            lms = LaterMessageSession.objects.filter(author=self.event.sender).order_by('date').first()
            if not lms:
                raise PWarning("Ничего не нашёл :(")
            else:
                author = None
                msgs = []
                for lm in lms.later_messages.all().order_by('date'):
                    if lm.message_author:
                        author = lm.message_author
                    elif lm.message_bot:
                        author = lm.message_bot

                    msg = f"{author} ({lm.date.strftime('%d.%m.%Y %H:%M:%S')}):\n" \
                          f"{lm.text}"
                    attachments = []
                    if lm.attachments and lm.attachments != "null":
                        lm_attachments = lm.attachments
                        attachments = get_attachments_for_upload(self.bot, lm_attachments)
                    msgs.append({'msg': msg, 'attachments': attachments})

                    lm.delete()
                lms.delete()
                return msgs
