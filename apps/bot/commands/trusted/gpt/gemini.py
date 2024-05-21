from apps.bot.api.gpt.geminigptapi import GeminiGPTAPI
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.commands.abstract.gpt_command import GPTCommand
from apps.service.models import GPTPrePrompt


class Gemini(GPTCommand):
    name = "gemini"
    names = ["гемини"]
    access = Role.TRUSTED
    abstract = False

    help_text = HelpText(
        commands_text="чат Gemini",
        help_texts=[
            HelpTextItem(
                access,
                GPTCommand.DEFAULT_HELP_TEXT_ITEMS + \
                [GPTCommand.VISION_HELP_TEXT_ITEM] + \
                GPTCommand.PREPROMPT_HELP_TEXT_ITEMS
            )
        ],
        extra_text=GPTCommand.DEFAULT_EXTRA_TEXT
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

    def completions(self, messages, use_statistics=True) -> ResponseMessageItem:
        new_messages = self._transform_messages(messages)
        # Если картинка, то просто игнорируем препромпт
        if len(new_messages[-1]['parts']) == 2:
            new_messages = [new_messages[-1]]
        return super().completions(new_messages, use_statistics=False)

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
