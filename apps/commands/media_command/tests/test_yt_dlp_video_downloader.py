import os
from tempfile import mkstemp

from django.test import SimpleTestCase

from apps.shared.exceptions import PWarning
from apps.shared.utils.video.yt_dlp_video_downloader import YtDlpVideoDownloader


class YtDlpVideoDownloaderTests(SimpleTestCase):
    def test_get_first_playlist_entry_returns_plain_video(self):
        video_info = {"id": "video-id"}

        self.assertEqual(
            YtDlpVideoDownloader.get_first_playlist_entry(video_info),
            video_info,
        )

    def test_get_first_playlist_entry_returns_first_non_empty_entry(self):
        self.assertEqual(
            YtDlpVideoDownloader.get_first_playlist_entry(
                {
                    "_type": "playlist",
                    "entries": [None, {"id": "video-id"}],
                },
            ),
            {"id": "video-id"},
        )

    def test_get_first_playlist_entry_rejects_empty_playlist(self):
        with self.assertRaises(PWarning):
            YtDlpVideoDownloader.get_first_playlist_entry({"_type": "playlist", "entries": []})

    def test_get_downloaded_file_finds_non_empty_output(self):
        descriptor, tmp_video_file = mkstemp()
        os.close(descriptor)

        try:
            os.remove(tmp_video_file)
            expected_path = f"{tmp_video_file}.webm"
            with open(expected_path, "wb") as file:
                file.write(b"content")

            self.assertEqual(
                YtDlpVideoDownloader._get_downloaded_file(tmp_video_file),
                expected_path,
            )
        finally:
            YtDlpVideoDownloader._remove_tmp_files(tmp_video_file)

    def test_filesize_key_prefers_precise_size(self):
        self.assertEqual(
            YtDlpVideoDownloader.filesize_key(
                {
                    "filesize": 10,
                    "filesize_approx": 20,
                    "tbr": 30,
                },
            ),
            10,
        )

    def test_concurrent_fragment_downloads_default(self):
        self.assertEqual(
            YtDlpVideoDownloader.DEFAULT_CONCURRENT_FRAGMENT_DOWNLOADS,
            10,
        )

    def test_http_chunk_size_default(self):
        self.assertEqual(
            YtDlpVideoDownloader.DEFAULT_HTTP_CHUNK_SIZE,
            10 * 1024 * 1024,
        )
