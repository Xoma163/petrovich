from apps.service.models import Statistic


def append_command_to_statistics(command):
    if not command or len(command) == 0:
        return
    if command[-1] == '?':
        command = "?"
    elif command[0] == '=':
        command = '='
    statistics = Statistic.objects.filter(command=command).first()
    if statistics:
        statistics.count_queries += 1
        statistics.save()
    else:
        statistics = Statistic()
        statistics.command = command
        statistics.count_queries = 1
        statistics.save()
