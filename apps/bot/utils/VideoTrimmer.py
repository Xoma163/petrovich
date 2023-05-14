from tempfile import NamedTemporaryFile

from apps.bot.utils.DoTheLinuxComand import do_the_linux_command


class VideoTrimmer:
    def __init__(self):
        self.tmp_file_in = None
        self.tmp_file_out = None

    def trim(self, url, start_pos, end_pos=None):
        try:
            self.tmp_file_in = NamedTemporaryFile()
            self.tmp_file_out = NamedTemporaryFile()
            do_the_linux_command(f"curl -o {self.tmp_file_in.name} {url}")

            cmd = [f"ffmpeg -i {self.tmp_file_in.name} -ss {start_pos}"]
            if end_pos:
                cmd.append(f"-to {end_pos}")
            cmd.append(f"-f mp4 -y {self.tmp_file_out.name}")
            cmd = " ".join(cmd)
            do_the_linux_command(cmd)
            with open(self.tmp_file_out.name, 'rb') as file:
                file_bytes = file.read()
        finally:
            self.tmp_file_out.close()
            self.tmp_file_out.close()
        return file_bytes
