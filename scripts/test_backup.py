import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import backup


class BackupTest(unittest.TestCase):
    def fixture(self, directory, unsafe=False):
        for name in backup.FILES[:2]:
            (directory / name).write_bytes(b'fixture')
        with tarfile.open(directory / 'sessions.tar.gz', 'w:gz') as archive:
            member = tarfile.TarInfo('../escape' if unsafe else './session.enc')
            member.size = 7
            archive.addfile(member, io.BytesIO(b'fixture'))
        return {'version': 1, 'project': 'source', 'session_key_sha256': 'unused',
                'files': {name: backup.digest(directory / name) for name in backup.FILES}}

    def test_checksum_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest = self.fixture(directory)
            backup.validate_archive(directory, manifest)
            (directory / 'postgres.dump').write_bytes(b'tampered')
            with self.assertRaises(ValueError):
                backup.validate_archive(directory, manifest)

    def test_archive_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with self.assertRaises(ValueError):
                backup.validate_archive(directory, self.fixture(directory, unsafe=True))

    def test_restore_rejects_source_project_before_running_commands(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / 'manifest.json').write_text(json.dumps(self.fixture(directory)))
            with patch.object(backup.Deployment, 'run', side_effect=AssertionError('must not run')):
                deployment = object.__new__(backup.Deployment)
                deployment.project = 'source'
                with self.assertRaisesRegex(ValueError, 'different'):
                    backup.restore(deployment, directory)


if __name__ == '__main__':
    unittest.main()
