import logging
import subprocess


logger = logging.getLogger("bot")


def do_the_linux_command(command: str, log_filter: dict | None = None, check: bool = False) -> str:
    output: str
    try:
        process = subprocess.Popen(command.split(" "), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output_bytes, error = process.communicate()
        output = output_bytes.decode("utf-8")
        if error:
            output += f"\nОшибка:\n{error.decode('utf-8')}"

        log_data = {
            "linux_command": {
                "command": command,
                "returncode": process.returncode,
                "output": output,
            },
        }
        if log_filter:
            log_data.update({"log_filter": log_filter})

        if process.returncode:
            logger.error(log_data)
            if check:
                raise subprocess.CalledProcessError(process.returncode, command, output=output)
        else:
            logger.debug(log_data)
    except subprocess.CalledProcessError:
        raise
    except Exception as e:
        output = str(e)
        log_data = {
            "linux_command": {
                "command": command,
                "returncode": getattr(e, "returncode", None),
                "output": output,
            },
        }
        if log_filter:
            log_data.update({"log_filter": log_filter})
        logger.error(log_data)
        if check:
            raise
    return output


def is_systemd_service_active(service_name: str) -> bool:
    command = f"systemctl status {service_name}"
    response = do_the_linux_command(command)
    index1 = response.find("Active: ") + len("Active: ")
    index2 = response.find("(", index1) - 1
    status = response[index1:index2]
    return status == "active"
