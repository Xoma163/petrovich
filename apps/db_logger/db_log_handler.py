import logging

db_default_formatter = logging.Formatter()


class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        from .models import Logger

        traceback = None

        if record.exc_info:
            traceback = db_default_formatter.formatException(record.exc_info)

        kwargs = {
            'logger_name': record.name,
            'level': record.levelno,
            'msg': record.getMessage(),
            'traceback': traceback
        }

        if isinstance(record.msg, dict):
            if 'event' in record.msg:
                kwargs['sender'] = record.msg['event'].sender
                kwargs['chat'] = record.msg['event'].chat
                kwargs['user_msg'] = record.msg['event'].msg
                kwargs['event'] = "\n".join(str(record.msg['event']).split(','))

                Logger.objects.create(**kwargs)
            else:
                last_log = Logger.objects.first()
                if not last_log.result:
                    kwargs.update(record.msg)
                    for kwarg in kwargs:
                        setattr(last_log, kwarg, kwargs[kwarg])
                    last_log.level = record.levelno
                    last_log.save()
                else:
                    Logger.objects.create(**kwargs)
        else:
            kwargs['msg'] = record.msg
            Logger.objects.create(**kwargs)
