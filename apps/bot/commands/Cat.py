from apps.bot.classes.Consts import Role, Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_attachments_from_attachments_or_fwd
from apps.service.models import Cat as CatModel
from petrovich.settings import MAIN_SITE


class Cat(CommonCommand):
    names = ["кот"]
    help_text = "Кот - присылает рандомного всратого кота"
    detail_help_text = "Кот - присылает рандомного всратого кота\n\n" \
                       "Для доверенных:\n" \
                       "Кот (Изображения/Пересылаемое сообщение с изображениями) - добавляет кота в базу\n\n" \
                       "Для админа:\n" \
                       "Кот аватар - присылает нового кота для аватарки, которого ещё не было"
    platforms = [Platform.VK, Platform.TG]

    def add_cat(self, cat_image):
        cat = CatModel(author=self.event.sender)
        cat.save_remote_image(cat_image['private_download_url'])
        cat.save()
        return MAIN_SITE + cat.image.url

    def start(self):
        if self.event.args and self.event.args[0].lower() in ['аватар']:
            self.check_sender(Role.ADMIN)
            cat = CatModel.objects.filter(to_send=True).order_by('?').first()
            if not cat:
                raise PWarning("Нет котов")
            cat.to_send = False
            cat.save()
            attachments = self.bot.upload_photos(cat.image.path)
            return {'msg': "Держи нового кота на аватарку", 'attachments': attachments}

        images = get_attachments_from_attachments_or_fwd(self.event, 'photo')

        if len(images) == 0:
            cat = CatModel.objects.filter().order_by('?').first()
            if not cat:
                raise PWarning("Нет котов")
            attachments = self.bot.upload_photos(cat.image.path)

            return {
                'attachments': attachments,
                "keyboard": self.bot.get_inline_keyboard(self.names[0])
            }
        else:
            self.check_sender(Role.TRUSTED)
            new_urls = []
            for image in images:
                new_url = self.add_cat(image)
                new_urls.append(new_url)
            return "\n".join(new_urls)
