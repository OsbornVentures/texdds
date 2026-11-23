"""Regression checks for the publication and production safety boundaries."""
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import static_release as release


class ReleaseBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_root = (release.ROOT / 'dist').resolve()
        cls.temp_root.mkdir(exist_ok=True)

    def test_credentials_and_traversal_cannot_be_packaged(self):
        for name in ['.env', '.env.backup-20260622', 'assets/private.key',
                     'a/credentials.json', 'a/../secret.txt', '.git/config', 'a/.env.production']:
            self.assertFalse(release.safe_path(name), name)
        for name in ['.env.example', '.well-known/agent-discovery.json', 'okf/AGENTS.md']:
            self.assertTrue(release.safe_path(name), name)

    def test_static_ignored_file_cannot_bypass_clean_worktree(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as folder:
            root = Path(folder)
            site = root / 'texddssitefull'
            site.mkdir()
            (site / 'index.html').write_text('public')
            (site / '.env').write_text('private')
            with patch.object(release, 'ROOT', root), patch.object(release, 'SITE', site), \
                 patch.object(release, 'git', side_effect=['', 'texddssitefull/index.html']):
                with self.assertRaisesRegex(ValueError, 'Every static file'):
                    release.require_clean()

    def test_dirty_worktree_is_rejected(self):
        with patch.object(release, 'git', return_value=' M texddssitefull/index.html'):
            with self.assertRaisesRegex(ValueError, 'clean checkout'):
                release.require_clean()

    def test_only_current_remote_main_is_accepted(self):
        self.assertTrue(release.remote_main_matches('abc', 'abc\trefs/heads/main\n'))
        self.assertFalse(release.remote_main_matches('abc', 'def\trefs/heads/main\n'))
        self.assertFalse(release.remote_main_matches('abc', 'abc\trefs/heads/preview\n'))

    def test_zip_is_deterministic_and_preserves_dotfiles(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as folder:
            a, b = Path(folder) / 'a.zip', Path(folder) / 'b.zip'
            data = {'index.html': b'<p>Hello</p>\r\n', '.well-known/test.json': b'{}', '_headers': b'/*\n'}
            release.write_zip(a, data)
            release.write_zip(b, dict(reversed(list(data.items()))))
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with zipfile.ZipFile(a) as archive:
                self.assertEqual({name: archive.read(name) for name in archive.namelist()}, data)

    def test_change_without_changelog_is_rejected(self):
        with patch.object(release, 'git', return_value='texddssitefull/index.html'):
            with self.assertRaisesRegex(ValueError, 'CHANGELOG.md'):
                release.check_changelog('base')


if __name__ == '__main__':
    unittest.main()
