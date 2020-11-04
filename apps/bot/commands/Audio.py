from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_attachments_from_attachments_or_fwd, decl_of_num
from apps.service.models import AudioList


# ToDo: Deprecated
class Audio(CommonCommand):
    def __init__(self):
        names = ["аудио", "плейлист"]
        help_text = "Аудио - сохраняет аудио в базу"
        detail_help_text = "Аудио [количество=5] - присылает рандомные треки \n" \
                           "Аудио (Прикреплённые аудио/Пересланное сообщение с аудио/Пересланное сообщение с постом " \
                           "в котором аудио) - сохраняет аудио в базу"
        super().__init__(names, help_text, detail_help_text, int_args=[0], platforms=[Platform.VK], enabled=False)

    def start(self):
        audios_att = get_attachments_from_attachments_or_fwd(self.event, ['audio', 'wall'])
        if audios_att:
            self.save_attachments(audios_att)
            return "Добавил"
        else:
            count = 5
            if self.event.args:
                count = self.event.args[0]
                self.check_number_arg_range(count, 1, 10)
            # Fix issue with delete where limit
            audios = AudioList.objects.filter(
                pk__in=AudioList.objects.filter(author=self.event.sender).order_by('?')[:count])
            if len(audios) == 0:
                raise RuntimeWarning("Не нашёл ваших аудио")
            attachments = [audio.attachment for audio in audios]
            if len(audios) != count:
                msg = f"Нашёл только {len(audios)} {decl_of_num(len(audios), ['штуку', 'штуки', 'штук'])}"
            else:
                msg = "Лови"
            audios.delete()
            return {"msg": msg, "attachments": attachments}

    def save_attachments(self, attachments):
        for att in attachments:
            if att['type'] == 'audio':
                AudioList(author=self.event.sender,
                          name=f"{att['artist']} - {att['title']}",
                          attachment=self.bot.get_attachment_by_id('audio', att['owner_id'], att['id'])).save()

            elif att['type'] == 'wall':
                self.save_attachments(att['attachments'])
