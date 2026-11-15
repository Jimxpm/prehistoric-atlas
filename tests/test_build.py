import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from scripts.build import ROOT, build, read_json, validate_species, load_species, check_links


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ("data", "templates", "assets"):
            shutil.copytree(ROOT / name, self.root / name)
        self.path = self.root / "data/species/anomalocaris-canadensis.json"
        self.data = read_json(self.path)

    def save(self, data, path=None):
        (path or self.path).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def test_build_links_and_placeholders(self):
        for path in [*self.path.parent.glob('*.json'), self.root / 'data/site.json']:
            data = read_json(path)
            data['image'] = None
            data['image_metadata']['type'] = 'placeholder'
            self.save(data, path)
        out = build(self.root)
        self.assertEqual(len(out), len(load_species(self.root)) + 1)
        for html in out.values():
            self.assertIn('lang="zh-Hant"', html)
            self.assertIn('暫代', html)
            self.assertNotIn('<img', html)
            self.assertNotIn('href="/', html)

    def test_required_fields(self):
        for field in ("id", "period", "features", "story", "sources", "image", "image_metadata"):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                del data[field]
                with self.assertRaises(ValueError):
                    validate_species(data, self.path.name, self.root)

    def test_bad_json(self):
        self.path.write_text('{broken', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, 'JSON'):
            build(self.root)

    def test_duplicate_id(self):
        self.save(self.data, self.path.with_name('duplicate-test.json'))
        with self.assertRaisesRegex(ValueError, '重複 id'):
            load_species(self.root)

    def test_missing_and_unsafe_image(self):
        for image in ('assets/images/missing.webp', '../outside.webp', 'https://example.com/a.webp'):
            with self.subTest(image=image):
                data = copy.deepcopy(self.data)
                data['image'] = image
                with self.assertRaises(ValueError):
                    validate_species(data, self.path.name, self.root)

    def test_source_and_story_validation(self):
        for change in ('url', 'date', 'refs'):
            data = copy.deepcopy(self.data)
            if change == 'url':
                data['sources'][0]['url'] = 'javascript:alert(1)'
            elif change == 'date':
                data['sources'][0]['accessed_date'] = '2026-99-99'
            else:
                data['story'][0]['source_refs'] = [99]
            with self.assertRaises(ValueError):
                validate_species(data, self.path.name, self.root)

    def test_new_fixture_updates_both_pages(self):
        data = copy.deepcopy(self.data)
        data.update(id='fixture-species', name_zh='測試用資料', scientific_name='Fixture species')
        self.save(data, self.path.with_name('fixture-species.json'))
        build(self.root)
        self.assertIn('pages/fixture-species.html', (self.root / 'index.html').read_text(encoding='utf-8'))
        self.assertIn('fixture-species.html', (self.root / 'pages/anomalocaris-canadensis.html').read_text(encoding='utf-8'))
        self.assertTrue((self.root / 'pages/fixture-species.html').is_file())

    def test_html_escaping(self):
        self.data['summary'] = '<script>alert("x")</script>'
        self.save(self.data)
        out = build(self.root)
        for path in (self.root / 'index.html', self.root / 'pages/anomalocaris-canadensis.html'):
            html = out[path]
            self.assertNotIn('<script>', html)
            self.assertIn('&lt;script&gt;', html)

    def test_broken_link_and_fragment(self):
        for link in ('missing.html', '#absent', '/index.html', '../escape.html'):
            with self.subTest(link=link):
                with self.assertRaises(ValueError):
                    check_links(self.root, {self.root / 'index.html': f'<a href="{link}">x</a>'})

    def test_image_switch_without_template_change(self):
        # A real 1x1 PNG used solely in the temporary fixture.
        import base64
        image = self.root / 'assets/images/test-image.png'
        image.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j4uoAAAAASUVORK5CYII='))
        self.data['image'] = 'assets/images/test-image.png'
        self.data['image_metadata']['type'] = 'licensed'
        self.save(self.data)
        out = build(self.root)
        self.assertIn('src="assets/images/test-image.png"', out[self.root / 'index.html'])
        self.assertIn('src="../assets/images/test-image.png"', out[self.root / 'pages/anomalocaris-canadensis.html'])

    def test_catalog_navigation_and_subpath(self):
        from urllib.parse import urljoin, urlsplit
        from scripts.build import Document
        species = load_species(self.root)
        out = build(self.root)
        home = out[self.root / 'index.html']
        self.assertEqual(home.count('<article class="card">'), len(species))
        for item in species:
            self.assertIn(f'pages/{item["id"]}.html', home)
            page = out[self.root / 'pages' / (item['id'] + '.html')]
            for other in species:
                if other['id'] != item['id']:
                    self.assertIn(f'href="{other["id"]}.html"', page)
            if item['image'] is None:
                self.assertNotIn('<img', page)
                self.assertIn('復原圖待提供', page)
            else:
                self.assertIn('../' + item['image'], page)
        for path, html in out.items():
            base = 'https://example.org/repository-name/' + path.relative_to(self.root).as_posix()
            for link in Document(html).links:
                if not urlsplit(link).scheme:
                    self.assertTrue(urlsplit(urljoin(base, link)).path.startswith('/repository-name/'))

    def test_mixed_image_states(self):
        self.data['image'] = None
        self.data['image_metadata']['type'] = 'placeholder'
        self.save(self.data)
        out = build(self.root)
        self.assertIn('復原圖待提供', out[self.root / 'pages' / (self.data['id'] + '.html')])
        for item in load_species(self.root):
            if item['image'] is not None:
                page = out[self.root / 'pages' / (item['id'] + '.html')]
                self.assertIn('../' + item['image'], page)
                self.assertNotIn('復原圖待提供', page)

    def test_configured_images_have_no_placeholder_copy(self):
        out = build(self.root)
        for item in load_species(self.root):
            if item['image'] is not None:
                html = out[self.root / 'pages' / (item['id'] + '.html')]
                self.assertNotIn('復原圖待提供', html)
                self.assertIn('圖片說明', html)

    def test_deterministic_build(self):
        first = build(self.root)
        self.assertEqual(first, build(self.root))


if __name__ == '__main__':
    unittest.main()
