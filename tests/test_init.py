from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from bflow.cli import print_report
from bflow.doctor import run_doctor
from bflow.installer import InitConfig, load_saved_config, run_init


class InitTest(unittest.TestCase):
    def test_project_scope_scaffolds_shared_assets_and_project_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            home_dir = Path(tmp) / "home"
            project_root.mkdir()
            report = run_init(
                InitConfig(
                    project_root=project_root,
                    scope="project",
                    agents=["claude", "opencode", "copilot", "codex"],
                    prefix="bflow",
                    home_dir=home_dir,
                )
            )
            self.assertTrue((project_root / ".bflow" / "config.json").exists())
            self.assertTrue((project_root / ".claude" / "skills" / "bflow-new" / "SKILL.md").exists())
            self.assertTrue((project_root / ".opencode" / "commands" / "bflow-replay.md").exists())
            self.assertTrue((project_root / ".github" / "prompts" / "bflow-diagnose.prompt.md").exists())
            self.assertTrue((project_root / "AGENTS.md").exists())
            self.assertTrue(any("Codex native slash prompts" in warning for warning in report.warnings))
            claude_skill = (project_root / ".claude" / "skills" / "bflow-new" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn('argument-hint: "[natural-language test request]"', claude_skill)
            self.assertIn("Example: /bflow-new", claude_skill)
            copilot_prompt = (project_root / ".github" / "prompts" / "bflow-replay.prompt.md").read_text(encoding="utf-8")
            self.assertIn("${input:case:Enter the case name or path}", copilot_prompt)
            case_template = (project_root / ".bflow" / "cases" / "templates" / "test-flow.template.yaml").read_text(encoding="utf-8")
            self.assertIn("lifecycle:", case_template)
            self.assertIn("stage: draft", case_template)

    def test_global_scope_writes_global_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            home_dir = Path(tmp) / "home"
            project_root.mkdir()
            report = run_init(
                InitConfig(
                    project_root=project_root,
                    scope="global",
                    agents=["claude", "opencode", "copilot", "codex"],
                    prefix="bflow",
                    home_dir=home_dir,
                )
            )
            self.assertTrue((home_dir / ".claude" / "skills" / "bflow-new" / "SKILL.md").exists())
            self.assertTrue((home_dir / ".config" / "opencode" / "commands" / "bflow-new.md").exists())
            self.assertTrue((home_dir / ".codex" / "prompts" / "bflow-new.md").exists())
            self.assertTrue((project_root / ".github" / "copilot-instructions.md").exists())
            self.assertTrue((project_root / ".github" / "prompts" / "bflow-new.prompt.md").exists())
            self.assertTrue(any("GitHub Copilot slash prompts are workspace-scoped in bflow" in warning for warning in report.warnings))

    def test_update_uses_saved_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            project_root.mkdir()
            run_init(
                InitConfig(
                    project_root=project_root,
                    scope="project",
                    agents=["claude"],
                    prefix="bflow",
                )
            )
            loaded = load_saved_config(project_root)
            self.assertEqual(loaded.prefix, "bflow")
            self.assertEqual(loaded.scope, "project")
            self.assertEqual(loaded.agents, ["claude"])

    def test_doctor_reports_healthy_installation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            home_dir = Path(tmp) / "home"
            project_root.mkdir()
            run_init(
                InitConfig(
                    project_root=project_root,
                    scope="both",
                    agents=["claude", "opencode", "copilot", "codex"],
                    prefix="bflow",
                    home_dir=home_dir,
                )
            )
            report = run_doctor(project_root=project_root, home_dir=home_dir)
            self.assertFalse(report.has_failures)
            names = {check.name: check.status for check in report.checks}
            self.assertEqual(names["shared-assets"], "ok")
            self.assertEqual(names["project-adapters"], "ok")
            self.assertEqual(names["global-adapters"], "ok")

    def test_print_report_lists_both_browser_tool_prerequisites(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            project_root.mkdir()
            config = InitConfig(
                project_root=project_root,
                scope="project",
                agents=["codex"],
                prefix="bflow",
            )
            report = run_init(config)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                print_report(report, config)
            output = stdout.getvalue()
            self.assertIn("chrome-devtools-mcp", output)
            self.assertIn("https://github.com/ChromeDevTools/chrome-devtools-mcp", output)
            self.assertIn("agent-browser", output)
            self.assertIn("https://github.com/vercel-labs/agent-browser", output)


if __name__ == "__main__":
    unittest.main()
