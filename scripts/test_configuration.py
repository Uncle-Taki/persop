import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
import preflight

spec = importlib.util.spec_from_file_location('setup_env', Path(__file__).with_name('setup-env.py'))
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class ConfigurationTest(unittest.TestCase):
    def test_random_private_production_configuration_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = (Path(directory) / name for name in ('first', 'second'))
            setup.create_environment(first)
            setup.create_environment(second)
            values = preflight.read_environment(first)
            self.assertEqual([], preflight.validate(values, offline=True))
            self.assertEqual(0o600, first.stat().st_mode & 0o777)
            self.assertNotEqual(values['OPERATOR_USER_ID'], preflight.read_environment(second)['OPERATOR_USER_ID'])
            original = first.read_bytes()
            with self.assertRaises(FileExistsError):
                setup.create_environment(first)
            self.assertEqual(original, first.read_bytes())

    def test_demo_is_rejected_and_messages_do_not_disclose_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'demo'
            setup.create_environment(path, demo=True)
            values = preflight.read_environment(path)
            values['REDIS_PASSWORD'] = values['API_TOKEN']
            errors = preflight.validate(values, public=True)
            self.assertTrue(errors)
            for key in preflight.SECRET_KEYS:
                self.assertNotIn(values[key], '\n'.join(errors))


if __name__ == '__main__':
    unittest.main()

class DemoConfigurationTest(unittest.TestCase):
    def test_demo_mock_credential_is_private_and_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'demo'
            setup.create_environment(path, demo=True)
            values = preflight.read_environment(path)
            self.assertEqual(64, len(values['LLM_MOCK_TOKEN']))
            self.assertNotEqual(values['API_TOKEN'], values['LLM_MOCK_TOKEN'])
            self.assertEqual('false', values['OUTREACH_ENABLED'])
