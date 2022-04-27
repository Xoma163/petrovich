from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.service.models import MilanaTranslate


class Discord(Command):
    name = "милана"
    names = ["милок", "мил"]

    help_text = "переводчик с языка Миланы"
    help_texts = [
        "- (пересланное сообщение) - переводит",
        "- (пересланное сообщение) + текст - парсит слова и добавляет новые в словарь"
    ]

    access = Role.TRUSTED
    fwd = True

    def start(self):
        milana_text = self.event.fwd[0].message.clear.split(' ')
        if self.event.message.args:
            original_text = self.event.message.args
            new_words = self.add_new_words(milana_text, original_text)
            if not new_words:
                return "Не добавил новых слов"
            return "Добавил новые слова\n" + "\n".join(new_words)
        else:
            return self.translate(milana_text)

    @staticmethod
    def get_only_letters(text_list):
        new_text_list = []
        for word in text_list:
            new_word = []
            for letter in word:
                if letter.isalpha():
                    new_word.append(letter)
            new_text_list.append("".join(new_word))
        return new_text_list

    def add_new_words(self, milana_text, original_text):
        milana_text = self.get_only_letters(milana_text)
        original_text = self.get_only_letters(original_text)
        new_words = {x[0]: x[1] for x in zip(milana_text, original_text) if x[0] != x[1]}
        created_words = []
        for new_word in new_words:
            translated_word = new_words[new_word]
            _, created = MilanaTranslate.objects.get_or_create(milana_text=new_word, translated_text=translated_word)
            if created:
                created_words.append(f"{new_word} - {translated_word}")
        return created_words

    @staticmethod
    # ToDo: обработка символов
    def translate(milana_text):
        translated = []
        for word in milana_text:
            try:
                translated_text = MilanaTranslate.objects.get(milana_text=word).translated_text
                translated.append(translated_text)
            except MilanaTranslate.DoesNotExist:
                translated.append(word)
        return " ".join(translated)
