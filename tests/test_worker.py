"""Exercise the real worker with fake IO, no Windows or API dependencies."""
import ast
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock
from snowvoice_core import format_transcript, error_message

source = ast.parse(Path('SnowVoice.pyw').read_text(encoding='utf-8'))
worker = next(n for n in source.body if isinstance(n, ast.ClassDef) and n.name == 'SnowVoice')
method = next(n for n in worker.body if isinstance(n, ast.FunctionDef) and n.name == '_transcribe_worker')


class WorkerTests(unittest.TestCase):
    def run_worker(self, fail=False, auto=False, changed=False):
        fd, path = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        create = Mock(side_effect=RuntimeError('private response')) if fail else Mock(return_value=NS(text=' 完成。 '))
        copy, controller, errors = Mock(), Mock(), Mock()
        env = dict(os=os, OpenAI=Mock(return_value=NS(audio=NS(transcriptions=NS(create=create)))),
                   CC=NS(convert=lambda t: t), format_transcript=format_transcript,
                   pyperclip=NS(copy=copy), log=Mock(), error_message=error_message,
                   messagebox=NS(showerror=errors), time=NS(sleep=lambda _:None),
                   ctypes=NS(windll=NS(user32=NS(GetForegroundWindow=lambda: 2 if changed else 1))),
                   keyboard=NS(Controller=controller))
        exec(compile(ast.Module(body=[method], type_ignores=[]), '<worker>', 'exec'), env)
        app = NS(get_api_key=lambda: 'fake-test-value', _write_wav=lambda:path,
                 cfg={'auto_paste':auto}, tray=NS(title=''), paste_target=1,
                 root=NS(after=lambda _, fn:fn()), frames=['audio'], transcribing=True)
        env['_transcribe_worker'](app)
        self.assertFalse(Path(path).exists())
        self.assertFalse(app.transcribing)
        self.assertEqual(app.frames, [])
        return copy, controller, errors

    def test_success_copies_and_cleans_up(self):
        copy, controller, errors = self.run_worker()
        copy.assert_called_once_with('完成。')
        controller.assert_not_called()
        errors.assert_not_called()

    def test_api_failure_cleans_up_without_copying(self):
        copy, controller, errors = self.run_worker(fail=True)
        copy.assert_not_called()
        errors.assert_called_once()
        self.assertNotIn('private', str(errors.call_args))

    def test_changed_window_skips_automatic_paste(self):
        copy, controller, errors = self.run_worker(auto=True, changed=True)
        copy.assert_called_once()
        controller.assert_not_called()
