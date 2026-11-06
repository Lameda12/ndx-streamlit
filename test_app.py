import copy
import json
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest
from metrics import historical_rows, metrics, metric_is_disputed, screen_rows

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT/'data/balance_sheets.json').read_text())
BY = {c['ticker']:c for c in DATA}

class FinancialTests(unittest.TestCase):
    def test_snapshot_and_apple(self):
        self.assertEqual(len(BY),100)
        self.assertNotIn('GOOG',BY)
        self.assertAlmostEqual(metrics(BY['AAPL'])['surplus'],-37757)
        self.assertEqual({c['scale'] for c in DATA},{'millions'})
        self.assertTrue(all(len(c['dates']) == 5 for c in DATA))

    def test_missing_debt_is_not_zero(self):
        for t in ['ISRG','MNST']:
            self.assertIsNone(metrics(BY[t])['debt'])
            self.assertIsNone(metrics(BY[t])['surplus'])
        c=copy.deepcopy(BY['ISRG'])
        c['values']['Total Debt'][0]=0
        self.assertEqual(metrics(c)['surplus'],metrics(c)['liquid'])

    def test_fallback_requires_both_components(self):
        c=copy.deepcopy(BY['AEP'])
        self.assertEqual(metrics(c)['liquid'],670)
        c['values']['Short-Term Investments'][0]=None
        self.assertIsNone(metrics(c)['liquid'])

    def test_currencies_dates_and_flags(self):
        rows=screen_rows(DATA)
        self.assertEqual(sum(r['currency']=='USD' for r in rows),96)
        hist=historical_rows([BY['AAPL']],'assets')
        self.assertEqual([r['period'] for r in hist],BY['AAPL']['dates'])
        self.assertTrue(metric_is_disputed('NVDA','surplus'))
        self.assertFalse(metric_is_disputed('NVDA','assets'))

class AppTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()

    def test_default_and_company(self):
        at=self.app()
        self.assertFalse(at.exception)
        self.assertEqual(at.metric[0].value,'96')
        at.selectbox(key='company').select('NVDA').run()
        self.assertFalse(at.exception)
        self.assertTrue(any('5,883' in w.value for w in at.warning))

    def test_currency_and_empty_search(self):
        at=self.app()
        at.selectbox(key='currency').select('EUR').run()
        self.assertFalse(at.exception)
        self.assertEqual(at.metric[0].value,'3')
        self.assertEqual(set(at.selectbox(key='company').options),set(f'{c["ticker"]} · {c["name"]}' for c in DATA if c['currency']=='EUR'))
        at.text_input(key='search').set_value('doesnotexist987').run()
        self.assertFalse(at.exception)
        self.assertTrue(any('No companies match' in i.value for i in at.info))

    def test_missing_metric_and_empty_comparison(self):
        at=self.app()
        at.multiselect(key='compare_tickers').set_value([]).run()
        self.assertFalse(at.exception)
        self.assertTrue(any('Choose at least one' in i.value for i in at.info))
        at.text_input(key='search').set_value('ISRG').run()
        self.assertFalse(at.exception)
        self.assertTrue(any('not treated as zero' in w.value for w in at.warning))

if __name__=='__main__': unittest.main()
