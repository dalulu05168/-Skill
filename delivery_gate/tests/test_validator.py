import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from delivery_gate.validator import evaluate

REQUIRED = ('build','unit','integration','login','navigation','ui_desktop','ui_mobile','data','security','regression','independent_review')
SHA = 'a' * 40

class DeliveryGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'evidence').mkdir()
        self.report = {'schema_version': 1, 'project_id':'test-project', 'target_sha': SHA, 'checks': {}}
        for item in REQUIRED:
            name = f'evidence/{item}.log'
            body = f'{item}: actual test output\n'
            (self.root/name).write_text(body, encoding='utf-8')
            self.report['checks'][item] = {'status':'pass','artifact':name,
                'sha256':hashlib.sha256(body.encode()).hexdigest(), 'executor':'ci', 'command':f'run {item}'}

    def evaluate(self, report=None):
        return evaluate(report if report is not None else self.report, self.root, SHA, 'web')

    def test_complete_evidence_passes(self):
        self.assertEqual(self.evaluate()['decision'], 'PASS')

    def test_missing_login_fails(self):
        del self.report['checks']['login']
        self.assertEqual(self.evaluate()['decision'], 'BLOCK')

    def test_fail_or_not_run_blocks(self):
        for status in ('fail','blocked','not_run','not_applicable'):
            with self.subTest(status=status):
                changed = copy.deepcopy(self.report)
                changed['checks']['login']['status'] = status
                self.assertEqual(self.evaluate(changed)['decision'], 'BLOCK')

    def test_missing_or_modified_artifact_blocks(self):
        (self.root/'evidence/ui_mobile.log').write_text('tampered', encoding='utf-8')
        self.assertEqual(self.evaluate()['decision'], 'BLOCK')

    def test_old_commit_blocks(self):
        self.report['target_sha'] = 'b' * 40
        self.assertEqual(self.evaluate()['decision'], 'BLOCK')

    def test_unsafe_path_blocks(self):
        self.report['checks']['navigation']['artifact'] = '../secrets.log'
        self.assertEqual(self.evaluate()['decision'], 'BLOCK')

    def test_missing_artifact_blocks(self):
        self.report['checks']['login']['artifact'] = 'evidence/does-not-exist.log'
        self.assertEqual(self.evaluate()['decision'], 'BLOCK')

    def test_unknown_profile_blocks(self):
        self.assertEqual(evaluate(self.report, self.root, SHA, 'unknown')['decision'], 'BLOCK')

if __name__ == '__main__':
    unittest.main()
