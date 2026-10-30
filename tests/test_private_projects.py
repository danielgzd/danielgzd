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
    def test_export_removes_private_identity_raw_metadata_and_exact_dates(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'data').mkdir()
            (root/'docs').mkdir()
            config={'projects':[{'repository':'DO_NOT_EXPORT_REPOSITORY', 'id':'private-012345abcdef',
                                'description':'DO_NOT_EXPORT_DESCRIPTION','category':'工具'}]}
            (root/'profile.json').write_text(json.dumps({'private_project_display':[{'id':'private-012345abcdef','name':'示例工具','description':'可公开的基本介绍','category':'工具'}]}))
            def api(path):
                if '/commits?' not in path:
                    return {'owner':{'login':'danielgzd'},'private':True,'language':'Swift','archived':False,
                            'description':'DO_NOT_EXPORT_RAW_DESCRIPTION','default_branch':'DO_NOT_EXPORT_BRANCH'}
                return [{'sha':'DO_NOT_EXPORT_SHA','commit':{'message':'DO_NOT_EXPORT_MESSAGE',
                         'author':{'email':'DO_NOT_EXPORT_EMAIL'},
                         'committer':{'date':'2026-10-29T01:02:03Z'}},
                         'files':[{'filename':'DO_NOT_EXPORT_PATH','patch':'DO_NOT_EXPORT_CODE'}]}]
            with patch.object(private,'ROOT',root), patch.object(private,'load_private_config',return_value=config), patch.object(private,'api',side_effect=api), contextlib.redirect_stdout(io.StringIO()):
                private.main()
            generated='\n'.join(p.read_text() for p in root.rglob('*') if p.is_file())
            self.assertNotIn('DO_NOT_EXPORT',generated)
            self.assertIn('示例工具',generated)
            self.assertIn('可公开的基本介绍',generated)
            self.assertNotIn('2026-10-29',generated)
            result=json.loads((root/'data/private-projects.json').read_text())
            self.assertEqual(set(result['projects'][0]),private.PROJECT_KEYS)
            self.assertEqual(result['projects'][0]['name'],'示例工具')
            self.assertEqual(result['projects'][0]['activity'],[{'month':'2026-10','commits':1}])
            self.assertTrue((root/'docs/private-projects/private-012345abcdef.md').exists())
            result['projects'][0]['repository']='DO_NOT_EXPORT_REPOSITORY'
            with self.assertRaises(ValueError):
                private.validate_snapshot(result)

    def test_monthly_aggregation_merges_dates(self):
        rows=[{'commit':{'committer':{'date':date}}} for date in ['2026-10-29T00:00:00Z','2026-10-01T00:00:00Z']]
        self.assertEqual(private.summarize_commits(rows),[{'month':'2026-10','commits':2}])
        with self.assertRaises(ValueError):
            private.summarize_commits([{'commit':{}}])

    def test_rejects_original_schema_before_rendering(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'data').mkdir()
            (root/'data/private-projects.json').write_text(json.dumps({'projects':[{'name':'DO_NOT_EXPORT_REPOSITORY'}]}))
            with self.assertRaises(ValueError):
                private.render_private(root)
            self.assertFalse((root/'docs/private-projects').exists())

if __name__=='__main__':
    unittest.main()
