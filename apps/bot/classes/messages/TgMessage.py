from apps.bot.classes.messages.Message import Message
from petrovich.settings import env


class TgMessage(Message):
    MENTION = env.str('TG_BOT_LOGIN')

    def __init__(self, raw_str=None, _id=None, entities=None):
        has_mention, text = self.setup_message_with_entities(raw_str, entities)
        super().__init__(text, _id)

        self.has_mention = has_mention
        self.raw = raw_str

    def setup_message_with_entities(self, text, entities):
        """
        Находит и заменяет упоминания бота на пустоту
        """
        if not entities:
            return False, text
        bot_commands = list(filter(lambda x: x['type'] in ['bot_command'], entities))
        bot_commands_positions = [(x['offset'], x['length']) for x in bot_commands]
        mentions = list(filter(lambda x: x['type'] in ['mention'], entities))
        mentions_positions = [(x['offset']) for x in mentions]
        has_mention = False
        if bot_commands_positions:
            has_mention, text = self.parse_bot_command_entities(text, bot_commands_positions)
        elif mentions_positions:
            has_mention, text = self.parse_mentions_entities(text, mentions_positions)
        return has_mention, text

    def parse_mentions_entities(self, text, mentions_start_positions):
        """
        Находит и заменяет упоминания бота на пустоту по mention
        """
        tg_bot_mention = f"@{self.MENTION}".lower()
        text_lower = text.lower()
        if tg_bot_mention in text_lower:
            first_pos = text_lower.index(tg_bot_mention)
            if first_pos in mentions_start_positions:
                last_pos = first_pos + len(tg_bot_mention)
                text = text[:first_pos] + text[last_pos:]
                return True, text
        return False, text

    def parse_bot_command_entities(self, text, mentions_positions):
        """
        Находит и заменяет упоминания бота на пустоту по bot_command
        """
        result_text = text
        delete_positions = []
        for offset, length in mentions_positions:
            start_pos = offset
            end_pos = start_pos + length
            bot_command = text[start_pos:end_pos]
            if '@' in bot_command:
                command, mention = bot_command.split("@", 1)
            else:
                command, mention = bot_command, None

            if mention and mention == self.MENTION.lower():
                delete_positions.append((start_pos + len(command), end_pos))
        delete_positions = list(reversed(delete_positions))
        for start_pos, end_pos in delete_positions:
            result_text = result_text[:start_pos] + result_text[end_pos:]
        return len(delete_positions) > 0, result_text
