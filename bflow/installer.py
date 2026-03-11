from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from bflow.templates import (
    SUPPORTED_AGENTS,
    agents_block,
    copilot_instructions_block,
    global_agent_files,
    project_agent_files,
    shared_project_files,
)


BEGIN_MARKER = "<!-- bflow:begin -->"
END_MARKER = "<!-- bflow:end -->"


@dataclass
class InitConfig:
    project_root: Path
    scope: str
    agents: list[str]
    prefix: str
    force: bool = False
    home_dir: Path = field(default_factory=Path.home)


@dataclass
class InitReport:
    created: list[Path] = field(default_factory=list)
    updated: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add(self, path: Path, existed: bool) -> None:
        if existed:
            self.updated.append(path)
        else:
            self.created.append(path)


def run_init(config: InitConfig) -> InitReport:
    requested_scope = config.scope
    config.scope = normalize_scope(config.scope)
    validate_config(config)
    report = InitReport()

    install_shared_assets(config, report)
    install_agents_md(config, report)

    if "copilot" in config.agents:
        install_copilot_instructions(config, report)

    install_project_agent_files(config, report)
    install_required_global_agent_files(config, report)

    if requested_scope not in {None, "project"}:
        report.warnings.append(
            "bflow init now always installs project-local workflow assets; only agent-specific command adapters that require home-directory locations are written globally."
        )

    return report


def validate_config(config: InitConfig) -> None:
    if not config.prefix or any(ch.isspace() for ch in config.prefix):
        raise ValueError("prefix must be a non-empty value without spaces")
    unknown = sorted(set(config.agents) - set(SUPPORTED_AGENTS))
    if unknown:
        raise ValueError(f"unsupported agents: {', '.join(unknown)}")


def normalize_scope(scope: str | None) -> str:
    return "project"


def install_shared_assets(config: InitConfig, report: InitReport) -> None:
    files = shared_project_files(config.prefix, config.agents, "project")
    for relative_path, content in files.items():
        path = config.project_root / relative_path
        write_file(path, content, config.force, report)


def install_agents_md(config: InitConfig, report: InitReport) -> None:
    path = config.project_root / "AGENTS.md"
    managed = agents_block(config.prefix)
    write_managed_block(path, managed, report)


def install_copilot_instructions(config: InitConfig, report: InitReport) -> None:
    path = config.project_root / ".github" / "copilot-instructions.md"
    managed = copilot_instructions_block(config.prefix)
    write_managed_block(path, managed, report)


def install_project_agent_files(config: InitConfig, report: InitReport) -> None:
    for agent in config.agents:
        files = project_agent_files(config.prefix, agent)
        for relative_path, content in files.items():
            path = config.project_root / relative_path
            write_file(path, content, config.force, report)


def install_required_global_agent_files(config: InitConfig, report: InitReport) -> None:
    for agent in config.agents:
        if agent != "codex":
            continue
        files = global_agent_files(config.prefix, agent, config.home_dir)
        for path, content in files.items():
            write_file(path, content, config.force, report)


def write_managed_block(path: Path, block: str, report: InitReport) -> None:
    existed = path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    managed_content = f"{BEGIN_MARKER}\n{block.rstrip()}\n{END_MARKER}\n"
    if existed:
        original = path.read_text(encoding="utf-8")
        if BEGIN_MARKER in original and END_MARKER in original:
            start = original.index(BEGIN_MARKER)
            end = original.index(END_MARKER) + len(END_MARKER)
            updated = original[:start].rstrip()
            if updated:
                updated += "\n\n"
            updated += managed_content
            trailing = original[end:].strip()
            if trailing:
                updated += "\n\n" + trailing + "\n"
        else:
            updated = original.rstrip()
            if updated:
                updated += "\n\n"
            updated += managed_content
    else:
        updated = managed_content
    path.write_text(updated, encoding="utf-8")
    report.add(path, existed)


def write_file(path: Path, content: str, force: bool, report: InitReport) -> None:
    existed = path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    if existed and not force:
        current = path.read_text(encoding="utf-8")
        if current == content:
            return
    path.write_text(content, encoding="utf-8")
    report.add(path, existed)


def load_saved_config(project_root: Path) -> InitConfig:
    config_path = project_root / ".bflow" / "config.json"
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return InitConfig(
        project_root=project_root,
        scope=normalize_scope(raw.get("scope")),
        agents=list(raw["agents"]),
        prefix=raw["prefix"],
    )
