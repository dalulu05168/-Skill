import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import gate
import browser_checks

class AcceptanceGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.policy = self.root / 'policy.json'
        self.policy.write_text(json.dumps({
            'project': 'acceptance-self-test',
            'commands': {k: [sys.executable, '-c', 'print("OK")'] for k in ('build', 'unit', 'security')},
            'pages': [], 'screens': [], 'scenarios': [], 'auth': [], 'data_checks': []
        }), encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def test_template_without_real_target_is_rejected(self):
        r = gate.run(self.policy, self.root, self.root / 'output', None)
        self.assertEqual('REJECTED', r['overall'])
        self.assertTrue((self.root / 'output' / 'acceptance-report.md').is_file())
        self.assertEqual('BLOCKED', r['checks']['auth']['status'])

    def test_forged_old_browser_report_does_not_pass(self):
        outdir = self.root / 'output'
        outdir.mkdir()
        (outdir / 'browser-evidence.json').write_text(json.dumps({'checks': {k: {'status': 'PASS'} for k in browser_checks.BROWSER_GATES}}))
        r = gate.run(self.policy, self.root, outdir, None)
        self.assertEqual('REJECTED', r['overall'])
        self.assertEqual('BLOCKED', r['checks']['functional']['status'])

    def test_failing_build_rejects(self):
        p = json.loads(self.policy.read_text())
        p['commands']['build'] = [sys.executable, '-c', 'raise SystemExit(3)']
        self.policy.write_text(json.dumps(p))
        r = gate.run(self.policy, self.root, self.root / 'output', None)
        self.assertEqual('FAIL', r['checks']['build']['status'])
        self.assertEqual('REJECTED', r['overall'])

    def test_forged_child_success_on_nonzero_exit_is_rejected(self):
        outdir = self.root / 'output'
        checks = {k: {'status': 'PASS', 'reason': 'forged', 'evidence': []}
                  for k in browser_checks.BROWSER_GATES}
        original_runner = gate.run_command

        def malicious_runner(argv, cwd, timeout, log_file):
            if 'browser_checks.py' in ' '.join(argv):
                (outdir / 'browser-evidence.json').write_text(json.dumps({'checks': checks}))
                log_file.write_text('browser process failed')
                return ('FAIL', 'exit=1', str(log_file))
            return original_runner(argv, cwd, timeout, log_file)

        with patch.object(gate, 'run_command', side_effect=malicious_runner):
            result = gate.run(self.policy, self.root, outdir, 'http://127.0.0.1:9999')
        self.assertEqual('REJECTED', result['overall'])
        self.assertTrue(all(result['checks'][k]['status'] == 'FAIL' for k in browser_checks.BROWSER_GATES))

    def test_missing_security_audit_cannot_pass(self):
        p = json.loads(self.policy.read_text())
        del p['commands']['security']
        self.policy.write_text(json.dumps(p))
        r = gate.run(self.policy, self.root, self.root / 'output', None)
        self.assertEqual('REJECTED', r['overall'])
        self.assertIn('fatal_error', r)

    def test_downgraded_required_checks_rejected(self):
        p = json.loads(self.policy.read_text())
        p['required_gates'] = ['build']
        self.policy.write_text(json.dumps(p))
        r = gate.run(self.policy, self.root, self.root / 'output', None)
        self.assertEqual('REJECTED', r['overall'])

    def test_browser_config_missing_any_category_blocks_all(self):
        p = json.loads(self.policy.read_text())
        r = browser_checks.evaluate(p, 'http://127.0.0.1:9999', self.root / 'browser')
        self.assertTrue(all(x['status'] == 'BLOCKED' for x in r.values()))

    def test_real_proof_not_just_script_name(self):
        p = json.loads(self.policy.read_text())
        p['commands']['security'] = [sys.executable, '-c', 'raise SystemExit(1)']
        self.policy.write_text(json.dumps(p))
        r = gate.run(self.policy, self.root, self.root / 'output', None)
        self.assertEqual('FAIL', r['checks']['security']['status'])

if __name__ == '__main__':
    unittest.main()
