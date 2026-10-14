import unittest
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attributes):
        self.tags.append((tag, dict(attributes)))


class SiteTests(unittest.TestCase):
    def test_entry_page_is_content_instead_of_an_advertised_redirect(self):
        page = Page()
        page.feed((ROOT / 'index.html').read_text())
        self.assertEqual(sum(tag == 'h1' for tag, _ in page.tags), 1)
        self.assertFalse(any(tag == 'meta' and attrs.get('http-equiv', '').lower() == 'refresh'
                             for tag, attrs in page.tags))
        robots = [attrs.get('content', '') for tag, attrs in page.tags
                  if tag == 'meta' and attrs.get('name') == 'robots']
        self.assertEqual(robots, ['index,follow'])
        self.assertFalse(any(tag == 'script' and 'adsbygoogle' in attrs.get('src', '')
                             for tag, attrs in page.tags))
        canonicals = [attrs.get('href') for tag, attrs in page.tags
                      if tag == 'link' and attrs.get('rel') == 'canonical']
        self.assertEqual(canonicals, ['https://iafuture10.github.io/'])

    def test_root_sitemap_delegates_to_the_project_instead_of_copying_legacy_urls(self):
        ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
        index = ElementTree.parse(ROOT / 'sitemap.xml').getroot()
        self.assertEqual(index.tag, ns + 'sitemapindex')
        self.assertEqual({node.text for node in index.iter(ns + 'loc')}, {
            'https://iafuture10.github.io/sitemap-root.xml',
            'https://iafuture10.github.io/CODIGOERROR/sitemap.xml',
        })
        own = ElementTree.parse(ROOT / 'sitemap-root.xml').getroot()
        self.assertEqual({node.text for node in own.iter(ns + 'loc')},
                         {'https://iafuture10.github.io/'})

    def test_publisher_identity_remains_available_at_the_host_root(self):
        record = (ROOT / 'ads.txt').read_text().strip().split(',')
        self.assertEqual([field.strip() for field in record],
                         ['google.com', 'pub-7507181626477156', 'DIRECT', 'f08c47fec0942fa0'])


if __name__ == '__main__':
    unittest.main()
