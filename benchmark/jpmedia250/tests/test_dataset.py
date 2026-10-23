import json
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from build import build, validate
from score import chrf_lite


class DatasetIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = build()

    def test_count_and_uniqueness(self):
        validate(self.rows)
        self.assertEqual(len(self.rows), 250)
        self.assertEqual(len({r['japanese'] for r in self.rows}),250)

    def test_all_difficulties_and_styles(self):
        self.assertEqual(Counter(r['difficulty'] for r in self.rows), {i:50 for i in range(1,6)})
        self.assertEqual(sorted(Counter(r['medium'] for r in self.rows).values()), [62,62,63,63])

    def test_every_stratum_has_one_dev_and_four_eval(self):
        cells = defaultdict(Counter)
        for r in self.rows:
            cells[r['primary_challenge'],r['difficulty']][r['split']] += 1
        self.assertEqual(len(cells),50)
        for cell in cells.values():
            self.assertEqual(cell,{'dev':1,'eval':4})

    def test_blind_sets_contain_no_gold(self):
        for kind in ('japanese_only', 'with_context'):
            p = ROOT/f'data/build/jpmedia250_blind_{kind}.jsonl'
            rows = [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]
            self.assertEqual(len(rows),250)
            self.assertEqual([r['id'] for r in rows],[r['id'] for r in self.rows])
            for r in rows:
                self.assertFalse(any(s in r for s in ('english_reference','alternate_references','translation_note','reference')))
                self.assertIn('japanese',r)
                self.assertEqual('scene_context' in r,kind=='with_context')

    def test_no_fake_quotes_or_empty_fields(self):
        for r in self.rows:
            self.assertEqual(r['provenance'],'independently_authored_original')
            self.assertTrue(r['japanese'])
            self.assertTrue(r['english_reference'])
            self.assertTrue(r['scene_context'])
            self.assertTrue(r['translation_note'])
            self.assertFalse(any(r['english_reference'] == x for x in r['alternate_references']))
            self.assertTrue(any(ord(c)>127 for c in r['japanese']))

    def test_chrf_basic(self):
        self.assertAlmostEqual(chrf_lite('How are you?', 'How are you?'),100)
        self.assertLess(chrf_lite('turn left', 'turn right'),100)


if __name__ == '__main__':
    unittest.main()
