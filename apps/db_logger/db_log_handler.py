import logging

from apps.bot.classes.events.Event import Event

db_default_formatter = logging.Formatter()


class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        from apps.db_logger.models import TgLogger, VkLogger

        traceback = None

        if record.name == 'tg_bot':
            Logger = TgLogger
        elif record.name == 'vk_bot':
            Logger = VkLogger
        else:
            return

        if record.exc_info:
            traceback = db_default_formatter.formatException(record.exc_info)

        kwargs = {
            'logger_name': record.name,
            'level': record.levelno,
            'msg': record.getMessage(),
            'traceback': traceback
        }

        if isinstance(record.msg, dict):
            last_log = Logger.objects.first()
            if not last_log.result:
                kwargs.update(record.msg)
                for kwarg in kwargs:
                    setattr(last_log, kwarg, kwargs[kwarg])
                last_log.level = record.levelno
                last_log.save()
            else:
                Logger.objects.create(**kwargs)
        elif isinstance(record.msg, Event):
            kwargs['sender'] = record.msg.sender
            kwargs['chat'] = record.msg.chat
            kwargs['user_msg'] = record.msg.msg
            kwargs['event'] = "\n".join(str(record.msg).split(','))

            Logger.objects.create(**kwargs)
        else:
            kwargs['msg'] = record.msg
            Logger.objects.create(**kwargs)
