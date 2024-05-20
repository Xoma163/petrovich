from apps.bot.api.gpt.geminigptapi import GeminiGPTAPI
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.commands.chatgpt import ChatGPT
from apps.service.models import GPTPrePrompt


class Gemini(ChatGPT):
    name = "gemini"
    names = ["гемини"]

    help_text = HelpText(
        commands_text="чат GigaChat",
        help_texts=[
            HelpTextItem(Role.TRUSTED, [
                HelpTextItemCommand("(фраза)", "общение с ботом"),
                HelpTextItemCommand("(пересланное сообщение)", "общение с ботом"),
                HelpTextItemCommand("препромпт [конфа]", "посмотреть текущий препромпт"),
                HelpTextItemCommand("препромпт [конфа] (текст)", "добавить препромпт"),
                HelpTextItemCommand("препромпт [конфа] удалить", "удаляет препромпт"),
            ])
        ],
        extra_text=(
            "Если отвечать на сообщения бота через кнопку \"Ответить\" то будет продолжаться непрерывный диалог.\n"
            "В таком случае необязательно писать команду, можно просто текст\n\n"
            "Порядок использования препромптов в конфах:\n"
            "1) Персональный препромт конфы\n"
            "2) Персональный препромт\n"
            "3) Препромпт конфы"
        )
    )

    PREPROMPT_PROVIDER = GPTPrePrompt.GEMINI
    GPT_API_CLASS = GeminiGPTAPI


    def start(self) -> ResponseMessage:
        arg0 = self.event.message.args[0] if self.event.message.args else None
        menu = [
            [["препромпт", "препромт", "промпт", "preprompt", "prepromp", "prompt"], self.menu_preprompt],
            [['default'], self.default]
        ]
        method = self.handle_menu(menu, arg0)
        answer = method()
        return ResponseMessage(answer)

    def completions(self, messages, use_stats=True) -> ResponseMessageItem:
        new_messages = self._transform_messages(messages)
        # Если картинка, то просто игнорируем препромпт
        if len(new_messages[-1]['parts']) == 2:
            new_messages = [new_messages[-1]]
        return super().completions(new_messages, use_stats=False)

    def default(self, with_vision=True):
        return super().default(with_vision=True)

    @staticmethod
    def _transform_messages(messages: list[dict]) -> list[dict]:
        roles_map = {
            'user': 'user',
            'assistant': 'model',
            'system': 'user'
        }
        new_messages = []
        for message in messages:
            content = message['content']

            # image
            if isinstance(content, list):
                text = content[0]['text']
                text = text if text else ""
                image = content[1]['image_url']['url'].replace('data:image/jpeg;base64,', '')
                new_messages.append({
                    'role': roles_map[message['role']],
                    'parts': [
                        {
                            "text": text
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image
                            }
                        }
                    ]
                })
                continue

            text = content
            if not text:
                continue

            if message['role'] == 'system':
                text = f"System prompt: {text}"
            new_messages.append({
                'role': roles_map[message['role']],
                'parts': [{'text': text}]
            })
        return new_messages
