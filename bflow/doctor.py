from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from bflow.installer import InitConfig, normalize_scope
from bflow.templates import project_agent_files


@dataclass
class CheckResult:
    name: str
    status: str
    details: str


@dataclass
class DoctorReport:
    config: InitConfig | None = None
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return any(check.status == "fail" for check in self.checks)

    @property
    def has_warnings(self) -> bool:
        return any(check.status == "warn" for check in self.checks)

    def add(self, name: str, status: str, details: str) -> None:
        self.checks.append(CheckResult(name=name, status=status, details=details))


def run_doctor(project_root: Path, home_dir: Path) -> DoctorReport:
    report = DoctorReport()
    config_path = project_root / ".bflow" / "config.json"
    if not config_path.exists():
        report.add("config", "fail", f"Missing {config_path}. Run `bflow init` in this project first.")
        return report

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    config = InitConfig(
        project_root=project_root,
        scope=normalize_scope(raw.get("scope")),
        agents=list(raw["agents"]),
        prefix=raw["prefix"],
        home_dir=home_dir,
    )
    report.config = config

    check_shared_assets(report, config)
    check_project_adapters(report, config)
    check_global_adapters(report, config)
    return report


def check_shared_assets(report: DoctorReport, config: InitConfig) -> None:
    expected = [
        config.project_root / ".bflow" / "README.md",
        config.project_root / ".bflow" / "agent-browser-setup.md",
        config.project_root / ".bflow" / "config.json",
        config.project_root / ".bflow" / "prompts" / "router.md",
        config.project_root / ".bflow" / "prompts" / "new.md",
        config.project_root / ".bflow" / "prompts" / "explore.md",
        config.project_root / ".bflow" / "prompts" / "replay.md",
        config.project_root / ".bflow" / "prompts" / "diagnose.md",
        config.project_root / ".bflow" / "cases" / "README.md",
        config.project_root / ".bflow" / "cases" / "templates" / "test-flow.template.yaml",
        config.project_root / ".bflow" / "cases" / "examples" / "login-admin-smoke.yaml",
    ]
    missing = [str(path) for path in expected if not path.exists()]
    if missing:
        report.add("shared-assets", "fail", "Missing shared workflow files:\n- " + "\n- ".join(missing))
    else:
        report.add("shared-assets", "ok", "Shared `.bflow/` assets are present.")


def check_project_adapters(report: DoctorReport, config: InitConfig) -> None:
    expected: list[Path] = [config.project_root / "AGENTS.md"]
    copilot_instructions_path = config.project_root / ".github" / "copilot-instructions.md"
    if "copilot" in config.agents:
        expected.append(copilot_instructions_path)
    for agent in config.agents:
        for relative_path in project_agent_files(config.prefix, agent):
            expected.append(config.project_root / relative_path)
    missing = [str(path) for path in expected if not path.exists()]
    if missing:
        status = "fail"
        report.add("project-adapters", status, "Missing project adapter files:\n- " + "\n- ".join(missing))
    else:
        report.add("project-adapters", "ok", "Project adapter files are present.")


def check_global_adapters(report: DoctorReport, config: InitConfig) -> None:
    report.add("global-adapters", "ok", "Global adapter files are no longer used. bflow commands rely on project-local assets under .bflow/.")


def summarize_status(report: DoctorReport) -> str:
    if report.has_failures:
        return "fail"
    if report.has_warnings:
        return "warn"
    return "ok"


def format_report(report: DoctorReport) -> str:
    lines = ["", "bflow doctor / 健康检查", ""]
    if report.config:
        lines.append(f"Project root: {report.config.project_root}")
        lines.append(f"Prefix: /{report.config.prefix}-*")
        lines.append(f"Scope: {report.config.scope}")
        lines.append(f"Agents: {', '.join(report.config.agents)}")
    else:
        lines.append("Project root is missing a valid `.bflow/config.json`.")
    lines.append("")
    for check in report.checks:
        icon = {"ok": "OK", "warn": "WARN", "fail": "FAIL"}[check.status]
        lines.append(f"[{icon}] {check.name}")
        lines.append(check.details)
        lines.append("")
    overall = summarize_status(report)
    overall_text = {"ok": "healthy", "warn": "healthy with warnings", "fail": "action required"}[overall]
    lines.append(f"Overall status: {overall_text}")
    return "\n".join(lines).rstrip() + "\n"
