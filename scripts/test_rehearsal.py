import importlib.util
import unittest
from pathlib import Path
from unittest.mock import call, patch

spec = importlib.util.spec_from_file_location('rehearsal', Path(__file__).with_name('container-rehearsal.py'))
rehearsal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rehearsal)


class RehearsalReadinessTest(unittest.TestCase):
    def test_rotation_waits_for_new_credential_even_when_old_process_is_ready(self):
        # The old API may still answer readiness during container replacement.
        # Do not continue until a request with the newly configured key is accepted.
        with patch.object(rehearsal, 'request', side_effect=[
            (200, b'{"data":{"ready":true}}'), (401, b''), (200, b'{"data":{"ready":true}}'), (503, b'gateway not started'),
        ]) as request, patch.object(rehearsal.time, 'sleep'):
            rehearsal.wait_api(31880, 'new-test-credential')
        self.assertEqual(request.call_args_list, [
            call(31880, '/ready'),
            call(31880, '/api/v1/operations/status', 'new-test-credential'),
            call(31880, '/ready'),
            call(31880, '/api/v1/operations/status', 'new-test-credential'),
        ])

    def test_frontend_html_does_not_count_as_api_readiness(self):
        with patch.object(rehearsal, 'request', side_effect=[
            (200, b'<html>frontend shell</html>'),
            (200, b'{"data":{"ready":true}}'), (200, b'{}'),
        ]) as request, patch.object(rehearsal.time, 'sleep'):
            rehearsal.wait_api(31880, 'test-credential')
        self.assertEqual(request.call_count, 3)


if __name__ == '__main__':
    unittest.main()
