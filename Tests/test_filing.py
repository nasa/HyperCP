"""Offline regression tests for the Zhang database and LUT downloads."""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
from threading import Thread
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

import requests
from requests.structures import CaseInsensitiveDict

from Source.utils import filing


DOWNLOADS = (
    (filing.downloadZhangDB, 'Zhang_rho_db_expanded.mat', 'e4c155f8ce92dcfa012a450a56b64e28'),
    (filing.downloadZhangLUT, 'Z17_LUT_40.nc', 'd9197436125f97c3bd8f00c6ee0185be'),
    (filing.downloadZhangLUT, 'Z17_LUT_30.nc', '988cc08446dd00d689280397f2faa672'),
)


class TestZhangDownloads(unittest.TestCase):
    """Exercise the public download functions without external data or a GUI."""

    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.target = None
        self.response = MagicMock(spec=requests.Response)
        self.response.__enter__.return_value = self.response
        self.response.close.return_value = None
        self.response.__exit__.side_effect = lambda *args: self.response.close()
        self.response.headers = CaseInsensitiveDict()
        self.response.iter_content.return_value = [b'first', b'', b'second']
        self.session = MagicMock(spec=requests.Session)
        self.session.__enter__.return_value = self.session
        self.session.close.return_value = None
        self.session.__exit__.side_effect = lambda *args: self.session.close()
        self.session.get.return_value = self.response
        self.session.head.return_value.headers = CaseInsensitiveDict()
        self.patch('requests.Session', return_value=self.session)
        self.progress_factory = self.patch('tqdm')
        self.progress = self.progress_factory.return_value
        self.progress.__enter__.return_value = self.progress
        self.checksum = self.patch('md5')
        self.output = io.StringIO()
        self.patch('print', create=True, side_effect=lambda *args: print(*args, file=self.output))

    def patch(self, name, **kwargs):
        """Patch a filing dependency and restore it after each test."""
        parts = name.split('.')
        owner = filing
        for part in parts[:-1]:
            owner = getattr(owner, part)
        patcher = patch.object(owner, parts[-1], **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def run_download(self, download, expected):
        self.checksum.return_value = expected
        download(self.target, force=True)

    def set_target(self, filename):
        for path in Path(self.directory.name).iterdir():
            path.unlink()
        self.target = Path(self.directory.name) / filename

    def test_missing_content_length(self):
        for download, filename, expected in DOWNLOADS:
            with self.subTest(download=download.__name__, filename=filename):
                self.set_target(filename)
                self.run_download(download, expected)
                self.assertEqual(self.target.read_bytes(), b'firstsecond')
                self.session.head.assert_not_called()
                self.progress.__enter__.assert_called()
                self.response.close.assert_called()
                self.session.close.assert_called()
                self.target.unlink()

    def test_progress_uses_get_content_length(self):
        self.response.headers['content-length'] = '11'
        for download, filename, expected in DOWNLOADS:
            with self.subTest(download=download.__name__, filename=filename):
                self.set_target(filename)
                self.run_download(download, expected)
                self.assertEqual(self.progress_factory.call_args.kwargs['total'], 11)
                self.assertEqual(self.target.read_bytes(), b'firstsecond')
                self.assertEqual(self.session.get.call_args.kwargs['timeout'], (10, 60))
                self.session.head.assert_not_called()

    def test_invalid_content_length_does_not_block_download(self):
        for value in ('', 'unknown', '-1', None):
            for download, filename, expected in DOWNLOADS:
                with self.subTest(value=value, download=download.__name__,
                                  filename=filename):
                    self.set_target(filename)
                    self.response.headers['Content-Length'] = value
                    self.run_download(download, expected)
                    self.assertIsNone(self.progress_factory.call_args.kwargs['total'])
                    self.assertEqual(self.target.read_bytes(), b'firstsecond')

    def test_connection_failure_leaves_existing_file(self):
        self.session.get.side_effect = requests.ConnectionError('offline')
        for download, filename, expected in DOWNLOADS:
            with self.subTest(download=download.__name__, filename=filename):
                self.set_target(filename)
                self.target.write_bytes(b'original')
                self.run_download(download, expected)
                self.assertEqual(self.target.read_bytes(), b'original')
                self.assertEqual(list(self.target.parent.iterdir()), [self.target])
                self.checksum.assert_not_called()
                self.session.close.assert_called()

    def test_http_error_does_not_read_response_or_create_file(self):
        self.response.raise_for_status.side_effect = requests.HTTPError('503')
        for download, filename, expected in DOWNLOADS:
            with self.subTest(download=download.__name__, filename=filename):
                self.set_target(filename)
                self.run_download(download, expected)
                self.assertFalse(self.target.exists())
                self.response.iter_content.assert_not_called()
                self.checksum.assert_not_called()
                self.response.close.assert_called()
                self.session.close.assert_called()

    def test_interrupted_transfer_removes_partial_file(self):
        def interrupted():
            yield b'partial'
            raise requests.exceptions.ChunkedEncodingError('connection closed')

        for download, filename, expected in DOWNLOADS:
            with self.subTest(download=download.__name__, filename=filename):
                self.set_target(filename)
                self.response.iter_content.side_effect = lambda **kwargs: interrupted()
                self.target.write_bytes(b'original')
                self.run_download(download, expected)
                self.assertEqual(self.target.read_bytes(), b'original')
                self.assertEqual(list(self.target.parent.iterdir()), [self.target])
                self.checksum.assert_not_called()
                self.progress.__exit__.assert_called()
                self.response.close.assert_called()
                self.session.close.assert_called()

    def test_checksum_failure_does_not_publish_download(self):
        for download, filename, _ in DOWNLOADS:
            with self.subTest(download=download.__name__, filename=filename):
                self.set_target(filename)
                self.target.write_bytes(b'original')
                self.run_download(download, 'incorrect hash')
                self.assertEqual(self.target.read_bytes(), b'original')
                self.assertEqual(list(self.target.parent.iterdir()), [self.target])
                self.assertIn('Checksum mismatch', self.output.getvalue())

    def test_failed_publish_removes_temporary_file(self):
        self.patch('os.replace', side_effect=PermissionError('read-only destination'))
        for download, filename, expected in DOWNLOADS:
            with self.subTest(download=download.__name__, filename=filename):
                self.set_target(filename)
                self.target.write_bytes(b'original')
                self.run_download(download, expected)
                self.assertEqual(self.target.read_bytes(), b'original')
                self.assertEqual(list(self.target.parent.iterdir()), [self.target])

    def test_download_is_verified_before_replacing_destination(self):
        for download, filename, expected in DOWNLOADS:
            with self.subTest(download=download.__name__, filename=filename):
                self.set_target(filename)
                self.target.write_bytes(b'original')

                def verify(temporary):
                    self.assertEqual(Path(temporary).read_bytes(), b'firstsecond')
                    self.assertEqual(self.target.read_bytes(), b'original')
                    return expected

                self.checksum.side_effect = verify
                self.run_download(download, expected)
                self.assertEqual(self.target.read_bytes(), b'firstsecond')
                self.assertEqual(list(self.target.parent.iterdir()), [self.target])

    def test_failure_to_create_output_leaves_existing_file(self):
        self.patch('NamedTemporaryFile', side_effect=PermissionError('read-only directory'))
        for download, filename, expected in DOWNLOADS:
            with self.subTest(download=download.__name__, filename=filename):
                self.set_target(filename)
                self.target.write_bytes(b'original')
                self.run_download(download, expected)
                self.assertEqual(self.target.read_bytes(), b'original')
                self.assertEqual(list(self.target.parent.iterdir()), [self.target])
                self.checksum.assert_not_called()
                self.response.close.assert_called()
                self.session.close.assert_called()

    def test_cancel_does_not_start_download(self):
        self.patch('YNWindow', return_value=filing.QMessageBox.Cancel)
        for download, filename, _ in DOWNLOADS:
            self.set_target(filename)
            download(self.target)
        self.session.get.assert_not_called()
        self.session.head.assert_not_called()
        self.assertFalse(self.target.exists())


class TestZhangHTTP(unittest.TestCase):
    """Exercise real Requests streaming and checksum validation against localhost."""

    def test_redirect_and_chunked_response_without_length(self):
        body = b'local database fixture'
        seen = []

        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'

            def do_GET(self):
                seen.append(self.path)
                if self.path == '/redirect':
                    self.send_response(302)
                    self.send_header('Location', '/database')
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header('Transfer-Encoding', 'chunked')
                self.end_headers()
                for chunk in (body[:5], body[5:]):
                    self.wfile.write(f'{len(chunk):x}\r\n'.encode() + chunk + b'\r\n')
                self.wfile.write(b'0\r\n\r\n')

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with TemporaryDirectory() as directory:
                target = Path(directory) / 'database.nc'
                url = f'http://127.0.0.1:{server.server_port}/redirect'
                filing._download_zhang_file(target, url, hashlib.md5(body).hexdigest())
                self.assertEqual(target.read_bytes(), body)
                self.assertEqual(list(Path(directory).iterdir()), [target])
            self.assertEqual(seen, ['/redirect', '/database'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)



if __name__ == '__main__':
    unittest.main()
