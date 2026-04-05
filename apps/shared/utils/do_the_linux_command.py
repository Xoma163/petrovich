import subprocess


def do_the_linux_command(command: str) -> str:
    output: str
    try:
        process = subprocess.Popen(command.split(" "), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output_bytes, error = process.communicate()
        output = output_bytes.decode("utf-8")
        if error:
            output += f"\nОшибка:\n{error.decode('utf-8')}"
    except Exception as e:
        output = str(e)
    return output


def is_systemd_service_active(service_name: str) -> bool:
    command = f"systemctl status {service_name}"
    response = do_the_linux_command(command)
    index1 = response.find("Active: ") + len("Active: ")
    index2 = response.find("(", index1) - 1
    status = response[index1:index2]
    return status == "active"
