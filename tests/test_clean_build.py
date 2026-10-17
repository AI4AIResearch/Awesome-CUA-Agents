"""Every build starts from a clean output directory, and publication drops every page the build no longer emits."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import test_resource_payloads as payloads
from search_pages import resource_path

STALE = ('compare/retired/index.html', 'papers/page/99/index.html', 'downloads/retired-export.jsonl')


class CleanBuildTests(unittest.TestCase):
    # Reuse the small fixture catalog without collecting its tests a second time.
    setUp = payloads.ResourcePayloadTests.setUp
    write_json = payloads.ResourcePayloadTests.write_json
    write_inputs = payloads.ResourcePayloadTests.write_inputs
    build_site = payloads.ResourcePayloadTests.build_site
    publish = payloads.ResourcePayloadTests.publish
    folder = payloads.ResourcePayloadTests.folder

    def plant(self, output, names):
        for name in names:
            (output / name).parent.mkdir(parents=True, exist_ok=True)
            (output / name).write_text('<meta name="robots" content="index,follow">stale\n')

    def test_rebuild_after_a_removal_leaves_no_page_or_file_from_the_previous_build(self):
        self.build_site()
        self.assertTrue(self.folder(self.build, self.tool).is_dir())
        self.plant(self.build, STALE)
        sibling = self.build.parent / 'keep.txt'
        sibling.write_text('Outside the output directory.\n')
        self.write_inputs([row for row in self.rows if row is not self.tool])
        self.build_site()
        self.assertFalse(self.folder(self.build, self.tool).exists())
        for name in STALE:
            self.assertFalse((self.build / name).exists(), name)
        self.assertTrue((self.folder(self.build, self.reviewed) / 'index.html').exists())
        self.assertEqual(sibling.read_text(), 'Outside the output directory.\n')
        self.assertEqual(sorted(p.name for p in self.build.parent.iterdir()), ['keep.txt', 'site'])

    def test_a_failed_build_keeps_the_previous_output(self):
        self.build_site()
        before = (self.build / 'data/search-manifest.json').read_bytes()
        (self.root / 'data/coverage.json').write_text('{"total_records": 0}\n')
        with self.assertRaises(ValueError):
            self.build_site()
        self.assertEqual((self.build / 'data/search-manifest.json').read_bytes(), before)
        self.assertEqual([p.name for p in self.build.parent.iterdir()], ['site'])

    def test_build_refuses_to_replace_a_checkout_or_an_unrelated_folder(self):
        for name, files in [('checkout', ('.git/HEAD', 'data/search-manifest.json')), ('notes', ('notes.txt',))]:
            target = self.root / name
            self.plant(target, files)
            self.build = target
            with self.assertRaises(ValueError):
                self.build_site()
            for file in files:
                self.assertTrue((target / file).exists(), (name, file))

    def test_publication_drops_removed_pages_from_every_section(self):
        self.build_site()
        self.publish()
        self.plant(self.site, STALE[:2])
        manifest = json.loads((self.site / 'data/search-manifest.json').read_text())
        manifest['pages'] += [{'path': '/compare/retired/', 'indexable': True, 'sha256': 'e' * 64},
                              {'path': '/papers/page/99/', 'indexable': True, 'sha256': 'f' * 64}]
        self.write_json(self.site / 'data/search-manifest.json', manifest)
        self.write_inputs([row for row in self.rows if row is not self.tool])
        self.build_site()
        self.publish()
        for name in STALE[:2]:
            self.assertFalse((self.site / name).exists(), name)
        self.assertFalse((self.folder(self.site, self.tool) / 'index.html').exists())
        self.assertTrue((self.site / resource_path(self.reviewed).lstrip('/') / 'index.html').exists())

    def test_publication_refuses_old_manifest_pages_outside_the_checkout(self):
        self.build_site()
        self.publish()
        outside = self.site.parent / 'outside'
        self.plant(outside, ('index.html',))
        manifest = json.loads((self.site / 'data/search-manifest.json').read_text())
        manifest['pages'].append({'path': '/resources/../../outside/', 'indexable': False, 'sha256': 'a' * 64})
        self.write_json(self.site / 'data/search-manifest.json', manifest)
        with self.assertRaises(ValueError):
            self.publish()
        self.assertTrue((outside / 'index.html').exists())

    def test_publication_refuses_old_manifest_pages_in_git_or_dot_folders_before_deleting(self):
        self.build_site()
        self.publish()
        manifest = json.loads((self.site / 'data/search-manifest.json').read_text())
        for path in ('/.git/', '/resources/../.git/hooks/', '/.github/'):
            with self.subTest(path=path):
                planted = self.site / path.strip('/') / 'index.html'
                self.plant(self.site, ('compare/retired/index.html', str(planted.relative_to(self.site))))
                pages = manifest['pages'] + [{'path': '/compare/retired/', 'indexable': True, 'sha256': 'e' * 64},
                                             {'path': path, 'indexable': True, 'sha256': 'f' * 64}]
                self.write_json(self.site / 'data/search-manifest.json', {**manifest, 'pages': pages})
                with self.assertRaises(ValueError):
                    self.publish()
                self.assertTrue(planted.resolve().exists())
                self.assertTrue((self.site / 'compare/retired/index.html').exists())


if __name__ == '__main__':
    unittest.main()
