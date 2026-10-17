from pathlib import Path
import sys
import unittest
import urllib.parse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog


PAPER = ("arxiv:2408.07199", "https://arxiv.org/abs/2408.07199", "arxiv")


def links(text):
    return [url for _, _, url in catalog.source_links({"parser": "links"}, text.encode())]


class UrlPreprocessingTests(unittest.TestCase):
    def test_http_in_a_query_value_is_preserved(self):
        for url in ("https://example.org/login?next=http://example.org/x", "http://example.org/login?next=http://example.org/x"):
            with self.subTest(url=url):
                rid, clean, provider = catalog.canonical(url)
                self.assertEqual(urllib.parse.parse_qs(urllib.parse.urlsplit(clean).query), {"next": ["http://example.org/x"]})
                self.assertEqual((clean.split("?")[0], provider), ("https://example.org/login", "url"))
        self.assertEqual(catalog.canonical("https://example.org/login?next=http://example.org/x"), catalog.canonical("http://example.org/login?next=http://example.org/x"))

    def test_scheme_is_case_insensitive(self):
        for scheme in ("HTTP", "Http", "HTTPS", "http"):
            with self.subTest(scheme=scheme):
                self.assertEqual(catalog.canonical(f"{scheme}://arxiv.org/abs/2404.07972"), ("arxiv:2404.07972", "https://arxiv.org/abs/2404.07972", "arxiv"))
                self.assertEqual(catalog.canonical(f"{scheme}://github.com/xlang-ai/OSWorld")[0], "github:xlang-ai/osworld")
                self.assertEqual(catalog.canonical(f"{scheme}://example.org/item"), catalog.canonical("https://example.org/item"))
                self.assertEqual(catalog.publication_identity(f"{scheme}://doi.org/10.1000/XYZ"), catalog.publication_identity("https://doi.org/10.1000/xyz"))
        self.assertIsNone(catalog.canonical("ftp://example.org/item"))

    def test_balanced_trailing_parenthesis_is_kept(self):
        mercury = "https://en.wikipedia.org/wiki/Mercury_(planet)"
        self.assertEqual(catalog.canonical(mercury)[1], mercury)
        for text in (mercury + ").", mercury + ",", mercury + ";"):
            with self.subTest(text=text):
                self.assertEqual(catalog.canonical(text), catalog.canonical(mercury))
        self.assertEqual(catalog.canonical("https://example.org/a)."), catalog.canonical("https://example.org/a"))
        self.assertEqual(catalog.canonical("https://arxiv.org/abs/2408.07199),")[0], PAPER[0])

    def test_link_extraction_keeps_balanced_parentheses_only(self):
        self.assertEqual(links("[x](https://example.org/a) and [Mercury](https://en.wikipedia.org/wiki/Mercury_(planet))."),
                         ["https://example.org/a", "https://en.wikipedia.org/wiki/Mercury_(planet)"])
        self.assertEqual(links("see (https://example.org/a) or <https://example.org/b>"), ["https://example.org/a", "https://example.org/b"])
        self.assertEqual(links("unclosed https://example.org/a(b c"), ["https://example.org/a(b"])


class ArxivPathIdentityTests(unittest.TestCase):
    def test_query_and_fragment_cannot_claim_arxiv_identity(self):
        for url in ("https://huggingface.co/spaces/org/demo?paper=huggingface.co/papers/2408.07199",
                    "https://huggingface.co/datasets/org/data?source=arxiv.org/abs/2408.07199",
                    "https://huggingface.co/org/model#huggingface.co/papers/2408.07199",
                    "https://arxiv.org/a/smith_j_1?from=arxiv.org/abs/2408.07199",
                    "https://arxiv.org/list/cs.AI/recent#arxiv.org/abs/2408.07199"):
            with self.subTest(url=url):
                self.assertEqual(catalog.canonical(url)[2], "url")

    def test_malformed_ids_are_not_truncated_into_another_id(self):
        for url in ("https://arxiv.org/abs/2408.071990", "https://arxiv.org/abs/2408.07199v1v2", "https://arxiv.org/abs/2408.07199abc",
                    "https://huggingface.co/papers/2408.071990", "https://arxiv.org/pdf/2408.07199_v2.pdf"):
            with self.subTest(url=url):
                self.assertEqual(catalog.canonical(url)[2], "url")

    def test_path_forms_still_fold_to_the_paper(self):
        for url in ("https://arxiv.org/abs/2408.07199", "http://arxiv.org/abs/2408.07199v2", "https://arxiv.org/pdf/2408.07199v3.pdf",
                    "https://arxiv.org/pdf/2408.07199", "https://arxiv.org/html/2408.07199v1/#S2", "https://arxiv.org/abs/2408.07199/",
                    "https://www.arxiv.org/abs/2408.07199?context=cs", "https://export.arxiv.org/abs/2408.07199", "https://ARXIV.org/ABS/2408.07199",
                    "https://huggingface.co/papers/2408.07199", "https://huggingface.co/papers/2408.07199#community",
                    "https://arxiv.org/abs/2408.07199},", "https://arxiv.org/abs/2408.07199**",
                    # Chinese prose often runs straight into a link; only an ASCII word character extends the ID.
                    "https://arxiv.org/abs/2408.07199中文", "https://huggingface.co/papers/2408.07199论文"):
            with self.subTest(url=url):
                self.assertEqual(catalog.canonical(url), PAPER)

    def test_bibtex_and_markdown_links_resolve_to_the_paper(self):
        found = links("url = {https://arxiv.org/abs/2408.07199},\n[paper](https://huggingface.co/papers/2408.07199)")
        self.assertEqual([catalog.canonical(url) for url in found], [PAPER, PAPER])


if __name__ == "__main__":
    unittest.main()
