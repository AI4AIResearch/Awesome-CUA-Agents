from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from search_pages import clip, description, page, resource_path

ROOT=Path(__file__).resolve().parents[1]


class MetaParser(HTMLParser):
    def __init__(self,text):
        super().__init__();self.meta={}
        self.feed(text.split('</head>',1)[0])
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);key=a.get('name') or a.get('property')
        if tag=='meta' and key in {'description','og:description'}:self.meta[key]=a['content']


class ClipTests(unittest.TestCase):
    def assertWholeWordClip(self,text,clipped,limit=300):
        self.assertLessEqual(len(clipped),limit);self.assertTrue(clipped.endswith('…'),clipped)
        kept=clipped[:-1];self.assertTrue(text.startswith(kept));self.assertFalse(kept[-1].isspace())
        self.assertTrue(text[len(kept)].isspace() or text[len(kept)] in ',;:.',text[len(kept)-10:len(kept)+10])
    def test_short_and_exact_length_text_is_unchanged(self):
        self.assertEqual(clip('A short summary.'),'A short summary.')
        exact=('word '*60)[:299]+'x';self.assertEqual(len(exact),300);self.assertEqual(clip(exact),exact)
    def test_long_text_is_cut_at_a_word_boundary_with_an_ellipsis(self):
        text='Introduces Sidekick. '+'A user study examines progress awareness, error traceability, and multitasking across background and foreground work. '*3
        self.assertGreater(len(text),300);self.assertWholeWordClip(text,clip(text))
        self.assertNotIn('foreground w…',clip(text))
    def test_word_ending_just_before_the_limit_is_kept(self):
        text='a'*298+' bb';self.assertEqual(clip(text),'a'*298+'…')
        text='a'*296+' bb cc';self.assertEqual(clip(text),'a'*296+' bb…')
    def test_trailing_punctuation_is_not_left_before_the_ellipsis(self):
        self.assertEqual(clip('alpha, beta, gamma',limit=14),'alpha, beta…')
    def test_text_without_whitespace_is_still_bounded(self):
        clipped=clip('x'*400);self.assertEqual(len(clipped),300);self.assertTrue(clipped.endswith('…'))
    def test_generated_meta_and_social_descriptions_end_on_whole_words(self):
        rows=[json.loads(line) for line in (ROOT/'data/catalog.jsonl').read_text().splitlines() if line.strip()]
        long_rows=0
        for r in rows:
            text=description(r);meta=MetaParser(page(r['name'],text,resource_path(r),'<h1>x</h1>')).meta
            with self.subTest(id=r['id']):
                self.assertEqual(meta['description'],meta['og:description'])
                self.assertLessEqual(len(meta['description']),300);self.assertFalse(meta['description'][-1].isspace())
                if len(text)>300:long_rows+=1;self.assertWholeWordClip(text,meta['description'])
                else:self.assertEqual(meta['description'],text)
        self.assertGreater(long_rows,0)


if __name__=='__main__':unittest.main()
