import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import collect_traffic
from update_profile import category, clean

class ProfileTests(unittest.TestCase):
    def test_override_precedes_keyword_and_unknown_stays_unknown(self):
        config = {'overrides':{'ios-demo':'人工分类'}, 'categories':[{'name':'Apple','keywords':['ios']}]}
        self.assertEqual(category({'name':'ios-demo'}, config), '人工分类')
        self.assertEqual(category({'name':'unknown'}, config), '其他探索')
        self.assertEqual(clean('<b>|\n'), '&lt;b&gt;&#124; ')

    def test_overlapping_traffic_windows_replace_days_and_failures_preserve_data(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'data').mkdir()
            (root/'docs').mkdir()
            (root/'data/public.json').write_text(json.dumps({'repositories':[{'name':'demo','fork':False}]}))
            def response(path):
                kind = 'views' if '/views?' in path else 'clones'
                return {kind:[{'timestamp':'2026-10-29T00:00:00Z','count':5,'uniques':2}]}
            with patch.object(collect_traffic, 'ROOT', root), patch.object(collect_traffic,'api',side_effect=response), contextlib.redirect_stdout(io.StringIO()):
                collect_traffic.main()
                collect_traffic.main()
            history = json.loads((root/'data/traffic.json').read_text())
            self.assertEqual(sum(x['count'] for x in history['repositories']['demo']['views'].values()),5)
            original = history['repositories']['demo']
            with patch.object(collect_traffic,'ROOT',root), patch.object(collect_traffic,'api',side_effect=RuntimeError('denied')), contextlib.redirect_stdout(io.StringIO()):
                collect_traffic.main()
            failed = json.loads((root/'data/traffic.json').read_text())
            self.assertEqual(failed['repositories']['demo'], original)
            self.assertEqual(len(failed['unavailable']), 2)

if __name__ == '__main__':
    unittest.main()
