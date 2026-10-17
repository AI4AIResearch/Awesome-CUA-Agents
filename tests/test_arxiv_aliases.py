from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog
from publication_metadata import publication_aliases


PAPER = ("arxiv:2408.07199", "https://arxiv.org/abs/2408.07199", "arxiv")


class ArxivAliasTests(unittest.TestCase):
    def test_arxiv_mirrors_and_hub_aliases_fold_to_the_paper(self):
        for url in ("https://web3.arxiv.org/abs/2408.07199v1", "https://browse.arxiv.org/abs/2408.07199", "https://ar5iv.labs.arxiv.org/html/2408.07199",
                    "https://ar5iv.org/abs/2408.07199", "https://hf.co/papers/2408.07199", "https://www.huggingface.co/papers/2408.07199",
                    "http://HF.co/papers/2408.07199#community", "https://hf.co/papers/2408.07199?from=arxiv.org/abs/2101.00001"):
            with self.subTest(url=url):
                self.assertEqual(catalog.canonical(url), PAPER)

    def test_arxiv_doi_folds_to_the_paper(self):
        for url in ("https://doi.org/10.48550/arXiv.2408.07199", "http://dx.doi.org/10.48550/ARXIV.2408.07199", "https://www.doi.org/10.48550/arxiv.2408.07199v2",
                    "https://doi.org/10.48550/arXiv.2408.07199.", "https://doi.org/10.48550%2FarXiv.2408.07199?utm_source=x"):
            with self.subTest(url=url):
                self.assertEqual(catalog.canonical(url), PAPER)
                self.assertEqual(catalog.publication_identity(url), PAPER)

    def test_unrelated_and_malformed_links_do_not_become_arxiv(self):
        for url in ("https://doi.org/10.1145/3544548.3580000", "https://doi.org/10.48550/arXiv.2408.071990", "https://doi.org/10.48550/arXiv.2408.07199?download=1"):
            with self.subTest(url=url):
                self.assertIsNone(catalog.canonical(url))
        self.assertEqual(catalog.publication_identity("https://doi.org/10.1145/3544548.3580000")[2], "url")
        for url in ("https://web3.arxiv.org.example.com/abs/2408.07199", "https://notarxiv.org/abs/2408.07199", "https://hf.co/org/model",
                    "https://web3.arxiv.org/a/smith_j_1?from=arxiv.org/abs/2408.07199", "https://ar5iv.org/abs/2408.071990", "https://arxiv.org/abs/cs/0601001"):
            with self.subTest(url=url):
                self.assertEqual(catalog.canonical(url)[2], "url")

    def test_publisher_record_cannot_claim_another_papers_arxiv_doi(self):
        observation = lambda rid: {"id": rid, "publication": {"doi": "10.48550/arXiv.2408.07199"}}
        self.assertEqual(publication_aliases([observation(PAPER[0])], catalog.publication_identity), {PAPER[0]: PAPER[0]})
        with self.assertRaisesRegex(ValueError, "attach it to arxiv:2408.07199"):
            publication_aliases([observation("arxiv:2404.07972")], catalog.publication_identity)


if __name__ == "__main__":
    unittest.main()
