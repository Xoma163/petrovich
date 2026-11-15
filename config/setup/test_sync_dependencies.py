import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASH = os.environ.get("TEST_BASH") or shutil.which("bash")


@unittest.skipUnless(BASH, "Bash is required to test the Linux deployment helper")
class SyncDependenciesTests(unittest.TestCase):
    def run_helper(self, fail_export=False):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            log = directory / "calls.log"
            bootstrap = directory / "mock-uv.sh"
            bootstrap.write_text(
                'uv() {\n'
                '  printf "%s\\n" "$*" >> "$MOCK_LOG"\n'
                '  if [[ "$1" == export && "$MOCK_FAIL_EXPORT" == 1 ]]; then\n'
                '    return 17\n'
                '  fi\n'
                '}\n',
                encoding="utf-8",
            )
            environment = {
                **os.environ,
                "BASH_ENV": bootstrap.as_posix(),
                "MOCK_LOG": log.as_posix(),
                "MOCK_FAIL_EXPORT": "1" if fail_export else "0",
                "TMPDIR": directory.as_posix(),
            }
            result = subprocess.run(
                [BASH, str(ROOT / "config/setup/sync_dependencies.sh")],
                cwd=directory,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            calls = log.read_text().splitlines() if log.exists() else []
            remaining = {path.name for path in directory.iterdir()}
            self.assertEqual(remaining, {"calls.log", "mock-uv.sh"}, result.stderr)
            return result, calls

    def test_sync_uses_locked_hashes_and_explicit_build_exceptions(self):
        result, calls = self.run_helper()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0].startswith("export --locked --no-emit-project --output-file "))
        self.assertTrue(calls[0].endswith(" --quiet"))
        self.assertTrue(calls[1].startswith("pip sync --python .venv/bin/python --require-hashes "))
        self.assertIn("--only-binary :all: --no-binary crontab,yandex-music,psycopg2 ", calls[1])
        exported_file = calls[0].split("--output-file ", 1)[1].removesuffix(" --quiet")
        self.assertTrue(calls[1].endswith(exported_file))

    def test_stale_lock_stops_before_sync_and_removes_temporary_export(self):
        result, calls = self.run_helper(fail_export=True)

        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0].startswith("export --locked "))


if __name__ == "__main__":
    unittest.main()
