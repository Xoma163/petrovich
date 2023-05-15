from tempfile import NamedTemporaryFile

from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.utils.DoTheLinuxComand import do_the_linux_command


class VideoTrimmer:
    def __init__(self):
        self.tmp_file_in = None
        self.tmp_file_out = None

    def trim(self, attachment_or_link, start_pos, end_pos=None):
        content = None
        url = None

        if isinstance(attachment_or_link, VideoAttachment):
            att = attachment_or_link
            content = att.download_content()
        else:
            url = attachment_or_link

        try:
            self.tmp_file_in = NamedTemporaryFile()
            self.tmp_file_out = NamedTemporaryFile()
            if url:
                do_the_linux_command(f"curl -o {self.tmp_file_in.name} {url}")
            else:
                with open(self.tmp_file_in.name, 'wb') as file:
                    file.write(content)
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
