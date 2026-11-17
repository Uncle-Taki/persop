import tempfile
import unittest
from pathlib import Path

from perso_ops import read_environment


class SharedOperatorPrimitivesTest(unittest.TestCase):
    def test_environment_parser_preserves_values_and_rejects_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            path.write_text('# comment\nTOKEN=abc=def\n')
            self.assertEqual({'TOKEN': 'abc=def'}, read_environment(path))
            path.write_text('TOKEN=one\nTOKEN=two\n')
            with self.assertRaises(ValueError):
                read_environment(path)


if __name__ == '__main__':
    unittest.main()
