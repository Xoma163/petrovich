import subprocess


def do_the_linux_command(command):
    try:
        process = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, error = process.communicate()
        output = output.decode("utf-8")
        if error:
            output += f"\nОшибка:\n{error}"
    except Exception as e:
        output = str(e)
    return output
