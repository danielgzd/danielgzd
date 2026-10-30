import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import update_private_projects as private

class PrivateProjectsTests(unittest.TestCase):
    def test_export_excludes_raw_commit_and_repository_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'data').mkdir()
            (root/'docs').mkdir()
            (root/'profile.json').write_text(json.dumps({'private_projects':[{'name':'demo','description':'基本介绍','category':'工具'}]}))
            def api(path):
                if '/commits?' not in path:
                    return {'owner':{'login':'danielgzd'},'private':True,'language':'Swift','archived':False,
                            'description':'DO_NOT_EXPORT_RAW_DESCRIPTION','default_branch':'DO_NOT_EXPORT_BRANCH'}
                return [{'sha':'DO_NOT_EXPORT_SHA','commit':{'message':'DO_NOT_EXPORT_MESSAGE',
                         'author':{'email':'DO_NOT_EXPORT_EMAIL'},
                         'committer':{'date':'2026-10-29T01:02:03Z'}},
                         'files':[{'filename':'DO_NOT_EXPORT_PATH','patch':'DO_NOT_EXPORT_CODE'}]}]
            with patch.object(private,'ROOT',root), patch.object(private,'api',side_effect=api), contextlib.redirect_stdout(io.StringIO()):
                private.main()
            private.render_private(root)
            generated='\n'.join(p.read_text() for p in root.rglob('*') if p.is_file())
            self.assertNotIn('DO_NOT_EXPORT',generated)
            result=json.loads((root/'data/private-projects.json').read_text())
            self.assertEqual(set(result['projects'][0]),{'name','description','category','language','archived','commit_count','activity'})
            self.assertEqual(result['projects'][0]['activity'],[{'date':'2026-10-29','commits':1}])
            self.assertTrue((root/'docs/private-projects/demo.md').exists())

    def test_daily_aggregation_and_missing_date(self):
        rows=[{'commit':{'committer':{'date':'2026-10-29T00:00:00Z'}}}]*2
        self.assertEqual(private.summarize_commits(rows),[{'date':'2026-10-29','commits':2}])
        with self.assertRaises(ValueError):
            private.summarize_commits([{'commit':{}}])

if __name__=='__main__':
    unittest.main()
