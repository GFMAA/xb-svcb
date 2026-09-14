import base64
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.bridge import Api


class AudioImportTests(unittest.TestCase):
    @staticmethod
    def make_api() -> Api:
        api = object.__new__(Api)
        api._audio_import_lock = threading.RLock()
        api._audio_imports = {}
        return api

    def test_streamed_audio_import_preserves_chunked_content(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            payload = (b"RIFF" + bytes(range(256))) * 4096
            api = self.make_api()
            with patch("api.bridge.config.TEMP_DIR", Path(td) / "temp"):
                token = api.start_audio_import("large-song.wav")
                self.assertIsNotNone(token)
                assert token is not None
                for offset in range(0, len(payload), 777):
                    chunk = payload[offset : offset + 777]
                    encoded = base64.b64encode(chunk).decode("ascii")
                    self.assertTrue(api.append_audio_import(token, f"data:audio/wav;base64,{encoded}"))

                path = api.finish_audio_import(token)
                self.assertIsNotNone(path)
                assert path is not None
                self.assertEqual(Path(path).suffix, ".wav")
                self.assertEqual(Path(path).read_bytes(), payload)
                self.assertFalse(Path(f"{path}.part").exists())

    def test_cancelled_audio_import_removes_partial_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            api = self.make_api()
            with patch("api.bridge.config.TEMP_DIR", Path(td) / "temp"):
                token = api.start_audio_import("cancelled.mp3")
                self.assertIsNotNone(token)
                assert token is not None
                self.assertTrue(api.append_audio_import(token, "data:audio/mpeg;base64,QUJD"))
                self.assertTrue(api.cancel_audio_import(token))
                self.assertIsNone(api.finish_audio_import(token))
                self.assertEqual(list((Path(td) / "temp" / "dropped-audio").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
