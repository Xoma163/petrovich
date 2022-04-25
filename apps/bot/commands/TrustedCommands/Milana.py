from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.service.models import MilanaTranslate


class Discord(Command):
    name = "милана"
    names = ["милок", "мил"]

    help_text = "переводчик с языка Миланы"
    help_texts = [
        "- (пересланное сообщение) - переводит"
        "- (пересланное сообщение) + текст - парсит слова и добавляет новые в словарь"
    ]

    access = Role.TRUSTED
    fwd = True

    def start(self):
        milana_text = self.event.fwd[0].message.clear.split(' ')
        if self.event.message.args:
            original_text = self.event.message.args
            new_words = self.add_new_words(milana_text, original_text)
            return "Добавил новые слова\n" + "\n".join(new_words)
        else:
            return self.translate(milana_text)

    @staticmethod
    def add_new_words(milana_text, original_text):
        new_words = {x[0]: x[1] for x in zip(milana_text, original_text) if x[0] != x[1]}
        created_words = []
        for new_word in new_words:
            translated_word = new_words[new_word]
            asd, created = MilanaTranslate.objects.get_or_create(milana_text=new_word, translated_text=translated_word)
            if created:
                created_words.append(f"{new_word} - {translated_word}")
        return created_words

    @staticmethod
    def translate(milana_text):
        translated = []
        for word in milana_text:
            try:
                translated_text = MilanaTranslate.objects.get(milana_text=word).translated_text
                translated.append(translated_text)
            except MilanaTranslate.DoesNotExist:
                translated.append(word)
        return " ".join(translated)
