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


    def test_overview_body_text_meets_normal_text_contrast(self):
        """Readable 12–13px text against the white dashboard canvas."""
        def luminance(hex_color):
            rgb = [int(hex_color[n:n+2], 16) / 255 for n in (1, 3, 5)]
            linear = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in rgb]
            return sum(a * b for a, b in zip(linear, (0.2126, 0.7152, 0.0722)))
        def ratio(a, b):
            x, y = sorted((luminance(a), luminance(b)), reverse=True)
            return (x + 0.05) / (y + 0.05)
        expected = {
            ".ws-frame .ws-pageheading p": "#4f5a66",
            ".ws-frame .ws-eyebrow,.ws-frame .ws-section-label": "#2c625d",
            ".ws-frame .ws-kpi-top small,.ws-frame .ws-kpi-note": "#52606d",
            ".ws-frame .ws-search-label,.ws-frame .ws-table-foot,.ws-frame .ws-clarification": "#52606d",
            ".ws-frame .ws-person-cell small,.ws-frame .ws-unknown": "#52606d",
            ".ws-frame .ws-tabs a:not(.active)": "#52606d",
            ".ws-frame .ws-section-label span": "#52606d",
            ".ws-frame>.app small": "#52606d",
            ".ws-frame .ws-filter:not(.active)": "#52606d",
        }
        for selector, color in expected.items():
            with self.subTest(selector=selector):
                self.assertIn(selector + "{color:" + color + ("!important" if selector in (".ws-frame .ws-person-cell small,.ws-frame .ws-unknown", ".ws-frame .ws-filter:not(.active)") else "") + "}", SHELL_CSS)
                self.assertGreaterEqual(ratio(color, "#ffffff"), 4.5)

    def test_pale_metric_icons_retain_readable_ink(self):
        expected = (
            (".ws-frame .ws-kpi-icon.teal", "#eef8f6", "#28665f"),
            (".ws-frame .ws-kpi-icon.blue", "#f1f6ff", "#275d93"),
            (".ws-frame .ws-kpi-icon.purple", "#f5f1ff", "#654f91"),
            (".ws-frame .ws-kpi-icon.orange", "#fff6e9", "#855b21"),
        )
        for selector, start, ink in expected:
            with self.subTest(selector=selector):
                self.assertIn(selector + "{background:linear-gradient(135deg," + start, SHELL_CSS)
                self.assertIn(";color:" + ink + "}", SHELL_CSS)

    def test_action_text_and_kpi_notes_do_not_revert_to_tiny_clipped_controls(self):
        for snippet in (
            ".ws-frame>.app button:not(.ws-filter):not(.ws-row-action):not(.ws-secondary-button){font-size:13px;line-height:1.5;min-height:40px}",
            ".ws-frame>.app input:not([type=\"checkbox\"]),.ws-frame>.app select,.ws-frame>.app textarea{font-size:13px;line-height:1.5}",
            ".ws-frame .ws-kpi-note{white-space:normal;text-overflow:clip;overflow-wrap:anywhere;min-height:36px}",
            ".ws-frame .ws-table-foot{flex-wrap:wrap;line-height:1.65}",
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, SHELL_CSS)


if __name__=="__main__":
    unittest.main()
