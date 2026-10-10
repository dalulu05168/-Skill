"""Visual contract tests for the unified 65-person workspace.

These are static safeguards for key CSS regressions. The rendered Chrome QA
is performed separately and is not replaced by these assertions.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_layout import SHELL_CSS
from trading_65_ui import SECTION


class VisualAcceptanceTests(unittest.TestCase):
    def test_mobile_sidebar_links_cannot_expand_to_global_nav_minwidth(self):
        self.assertIn(".ws-frame .ws-rail .ws-rail-links{display:flex;flex-direction:column;flex-wrap:nowrap;", SHELL_CSS)
        self.assertIn(".ws-frame .ws-rail .ws-rail-link{width:100%;min-width:0;max-width:100%;", SHELL_CSS)
        self.assertIn(".ws-frame .ws-rail-link{font-size:11px;min-height:62px}", SHELL_CSS)

    def test_shared_forms_tables_and_actions_have_consistent_tokens(self):
        for snippet in (
            ".ws-frame .ws-filter{font-size:12px!important;min-height:40px!important;",
            ".ws-frame .ws-row-action,.ws-frame .ws-secondary-button{font-size:12px;min-height:40px;",
            ".ws-frame .ws-table{font-size:13px}",
            ".ws-frame .ws-table th{font-size:12px}",
            ".ws-frame .ws-person-cell small{font-size:12px}",
            ".ws-frame .ws-clarification{font-size:12px;line-height:1.6}",
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, SHELL_CSS)

    def test_trade_cards_and_mobile_actions_follow_shared_scale(self):
        for snippet in (
            ".sim-table{font-size:13px}",
            ".sim-candidate-card{border-color:#e4e8ed;border-radius:12px;padding:18px}",
            ".sim-person-actions button{font-size:13px;min-height:40px}",
            ".sim-person-facts{grid-template-columns:1fr}",
            ".sim-person-head{flex-wrap:wrap}",
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, SECTION)


if __name__=="__main__":
    unittest.main()
