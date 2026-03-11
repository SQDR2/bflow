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
    def test_init_scaffolds_shared_assets_and_project_adapters(self) -> None:
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
            self.assertTrue((project_root / ".bflow" / "agent-browser-setup.md").exists())
            self.assertTrue((project_root / ".claude" / "skills" / "bflow-new" / "SKILL.md").exists())
            self.assertTrue((project_root / ".opencode" / "commands" / "bflow-replay.md").exists())
            self.assertTrue((project_root / ".github" / "prompts" / "bflow-diagnose.prompt.md").exists())
            self.assertTrue((project_root / "AGENTS.md").exists())
            claude_skill = (project_root / ".claude" / "skills" / "bflow-new" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn('argument-hint: "[natural-language test request]"', claude_skill)
            self.assertIn("Example: /bflow-new", claude_skill)
            copilot_prompt = (project_root / ".github" / "prompts" / "bflow-replay.prompt.md").read_text(encoding="utf-8")
            self.assertIn("agent: agent", copilot_prompt)
            self.assertIn("${input:case:Enter the case name or path}", copilot_prompt)
            self.assertIn("pause browser actions and inspect the relevant workspace source code", copilot_prompt)
            explore_prompt = (project_root / ".github" / "prompts" / "bflow-explore.prompt.md").read_text(encoding="utf-8")
            self.assertIn("If verification fails, stop immediately", explore_prompt)
            self.assertIn("Do not use `chrome-devtools`, `chrome-devtools-mcp`", explore_prompt)
            diagnose_prompt = (project_root / ".github" / "prompts" / "bflow-diagnose.prompt.md").read_text(encoding="utf-8")
            self.assertIn("inspect the relevant workspace source code", diagnose_prompt)
            case_template = (project_root / ".bflow" / "cases" / "templates" / "test-flow.template.yaml").read_text(encoding="utf-8")
            self.assertIn("lifecycle:", case_template)
            self.assertIn("stage: draft", case_template)
            setup_guide = (project_root / ".bflow" / "agent-browser-setup.md").read_text(encoding="utf-8")
            self.assertIn("github-copilot", setup_guide)
            self.assertIn("npx skills add vercel-labs/agent-browser --skill agent-browser --agent codex -y", setup_guide)

    def test_non_project_scope_is_normalized_to_project(self) -> None:
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
            self.assertTrue((project_root / ".github" / "copilot-instructions.md").exists())
            self.assertTrue((project_root / ".github" / "prompts" / "bflow-new.prompt.md").exists())
            self.assertFalse((home_dir / ".config" / "Code" / "User" / "prompts" / "bflow-new.prompt.md").exists())
            self.assertTrue(any("bflow init now always installs project-local files" in warning for warning in report.warnings))

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
                    scope="project",
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
            self.assertIn(".bflow/agent-browser-setup.md", output)
            self.assertIn("npm install -g agent-browser", output)
            self.assertIn("agent-browser install --with-deps", output)
            self.assertIn("--agent codex -y", output)


if __name__ == "__main__":
    unittest.main()
