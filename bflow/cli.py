from __future__ import annotations

import argparse
from pathlib import Path

from bflow import __version__
from bflow.doctor import format_report, run_doctor, summarize_status
from bflow.installer import InitConfig, load_saved_config, run_init
from bflow.templates import SUPPORTED_AGENTS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bflow", description="Initialize browser-test workflows for multiple coding agents.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize bflow in the current project.")
    add_common_args(init_parser)

    update_parser = subparsers.add_parser("update", help="Regenerate files using .bflow/config.json.")
    update_parser.add_argument("--project-root", default=".", help=argparse.SUPPRESS)
    update_parser.add_argument("--home-dir", default=None, help=argparse.SUPPRESS)
    update_parser.add_argument("--force", action="store_true", help="Overwrite generated files even if they already exist.")

    doctor_parser = subparsers.add_parser("doctor", help="Check the current bflow installation and generated files.")
    doctor_parser.add_argument("--project-root", default=".", help=argparse.SUPPRESS)
    doctor_parser.add_argument("--home-dir", default=None, help=argparse.SUPPRESS)

    agents_parser = subparsers.add_parser("agents", help="List supported agent adapters.")
    agents_parser.add_argument("--plain", action="store_true", help="Print one agent per line.")
    return parser


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--scope", choices=("project", "global", "both"), help="Where to install agent adapters.")
    parser.add_argument("--agents", help="Comma-separated agents. Supported: claude,opencode,copilot,codex")
    parser.add_argument("--prefix", default=None, help="Slash-command prefix. Default: bflow")
    parser.add_argument("--force", action="store_true", help="Overwrite generated files even if they already exist.")
    parser.add_argument("--project-root", default=".", help=argparse.SUPPRESS)
    parser.add_argument("--home-dir", default=None, help=argparse.SUPPRESS)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "agents":
            return run_agents(args.plain)
        if args.command == "init":
            return run_init_command(args)
        if args.command == "update":
            return run_update_command(args)
        if args.command == "doctor":
            return run_doctor_command(args)
        parser.error("unknown command")
        return 2
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 2
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2


def run_agents(plain: bool) -> int:
    if plain:
        for agent in SUPPORTED_AGENTS:
            print(agent)
        return 0
    print("Supported agents:")
    for agent in SUPPORTED_AGENTS:
        print(f"- {agent}")
    return 0


def run_init_command(args: argparse.Namespace) -> int:
    interactive = not any([args.scope, args.agents, args.prefix])
    config = InitConfig(
        project_root=Path(args.project_root).resolve(),
        scope=args.scope or ask_scope(),
        agents=parse_agents(args.agents) if args.agents else ask_agents(),
        prefix=args.prefix or ask_prefix(),
        force=args.force,
        home_dir=Path(args.home_dir).expanduser().resolve() if args.home_dir else Path.home(),
    )
    if interactive and not ask_confirmation(config):
        print("Initialization cancelled.")
        return 1
    report = run_init(config)
    print_report(report, config)
    return 0


def run_update_command(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    config = load_saved_config(project_root)
    config.force = args.force
    if args.home_dir:
        config.home_dir = Path(args.home_dir).expanduser().resolve()
    report = run_init(config)
    print_report(report, config)
    return 0


def run_doctor_command(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    home_dir = Path(args.home_dir).expanduser().resolve() if args.home_dir else Path.home()
    report = run_doctor(project_root=project_root, home_dir=home_dir)
    print(format_report(report), end="")
    return 1 if summarize_status(report) == "fail" else 0


def ask_scope() -> str:
    options = [
        ("project", "Install project-local files only"),
        ("global", "Install global agent files only"),
        ("both", "Install both project-local and global files"),
    ]
    while True:
        print("")
        print("Install scope / 安装范围:")
        for index, (value, description) in enumerate(options, start=1):
            print(f"{index}. {value:<7} {description}")
        value = input("Choose 1-3 (default: 1): ").strip().lower()
        if not value:
            return "project"
        if value in {"1", "2", "3"}:
            return options[int(value) - 1][0]
        if value in {"project", "global", "both"}:
            return value
        print("Please enter 1, 2, 3, or one of: project, global, both.")


def ask_agents() -> list[str]:
    print("")
    print("Agents / 目标 Agent:")
    descriptions = {
        "claude": "Claude Code skills",
        "opencode": "OpenCode commands",
        "copilot": "GitHub Copilot prompt files",
        "codex": "Codex prompts and AGENTS guidance",
    }
    for index, agent in enumerate(SUPPORTED_AGENTS, start=1):
        print(f"{index}. {agent:<8} {descriptions[agent]}")
    print("a. all")
    while True:
        value = input("Choose numbers or names, comma-separated (default: all): ").strip().lower()
        if not value or value == "a" or value == "all":
            return list(SUPPORTED_AGENTS)
        tokens = [part.strip() for part in value.split(",") if part.strip()]
        mapped = []
        for token in tokens:
            if token.isdigit():
                index = int(token) - 1
                if index < 0 or index >= len(SUPPORTED_AGENTS):
                    mapped = []
                    break
                mapped.append(SUPPORTED_AGENTS[index])
            else:
                mapped.append(token)
        try:
            return parse_agents(",".join(mapped))
        except SystemExit as exc:
            print(exc)


def ask_prefix() -> str:
    default = "bflow"
    print("")
    value = input("Command prefix / 命令前缀 (default: bflow): ").strip()
    return value or default


def ask_confirmation(config: InitConfig) -> bool:
    print("")
    print("Initialization summary / 初始化摘要:")
    print(f"- Project root: {config.project_root}")
    print(f"- Scope: {config.scope}")
    print(f"- Agents: {', '.join(config.agents)}")
    print(f"- Slash commands: /{config.prefix}-new, /{config.prefix}-explore, /{config.prefix}-replay, /{config.prefix}-diagnose")
    value = input("Continue? [Y/n]: ").strip().lower()
    return value in {"", "y", "yes"}


def parse_agents(raw: str) -> list[str]:
    agents = []
    for part in raw.split(","):
        name = part.strip().lower()
        if name:
            agents.append(name)
    ordered = []
    for agent in SUPPORTED_AGENTS:
        if agent in agents and agent not in ordered:
            ordered.append(agent)
    unknown = sorted(set(agents) - set(SUPPORTED_AGENTS))
    if unknown:
        raise SystemExit(f"Unsupported agents: {', '.join(unknown)}")
    if not ordered:
        raise SystemExit("No agents selected.")
    return ordered


def print_report(report, config: InitConfig) -> None:
    shared_paths, project_paths, global_paths = partition_paths(report, config)
    print("")
    print("bflow initialization complete / 初始化完成。")
    print(f"Project root: {config.project_root}")
    print(f"Prefix: /{config.prefix}-*")
    print(f"Scope: {config.scope}")
    print(f"Agents: {', '.join(config.agents)}")
    print("")
    print(f"Created: {len(report.created)}")
    print(f"Updated: {len(report.updated)}")
    if shared_paths:
        print("")
        print("Shared workflow files / 共享工作流文件:")
        for path in shared_paths:
            print(f"- {path}")
    if project_paths:
        print("")
        print("Project adapter files / 项目级适配文件:")
        for path in project_paths:
            print(f"- {path}")
    if global_paths:
        print("")
        print("Global adapter files / 全局适配文件:")
        for path in global_paths:
            print(f"- {path}")
    if report.warnings:
        print("")
        print("Warnings / 警告:")
        for warning in report.warnings:
            print(f"- {warning}")
    print("")
    print("Prerequisites / 前置依赖:")
    print("1. Install `chrome-devtools-mcp` in each target agent before using replay or diagnose workflows.")
    print("   在使用 replay 或 diagnose 工作流之前，请先在对应的 Agent 中安装 `chrome-devtools-mcp`。")
    print("   https://github.com/ChromeDevTools/chrome-devtools-mcp")
    print("2. Install or connect `agent-browser` in each target agent before using explore workflows.")
    print("   在使用 explore 工作流之前，请先在对应的 Agent 中安装或接入 `agent-browser`。")
    print("   https://github.com/vercel-labs/agent-browser")
    print("")
    print("Next steps / 下一步:")
    print(f"1. Restart your agent UI if slash commands are loaded only on startup.")
    print(f"   如果你的 Agent 只在启动时加载命令，请先重启。")
    print(f"2. Try /{config.prefix}-new with a natural-language browser test request.")
    print(f"   先试一下 /{config.prefix}-new，并输入一段自然语言测试需求。")
    print(f"3. After the draft case is created, run /{config.prefix}-explore to confirm stable steps.")
    print(f"   case 草稿生成后，再执行 /{config.prefix}-explore 来确认稳定步骤。")


def partition_paths(report, config: InitConfig) -> tuple[list[Path], list[Path], list[Path]]:
    all_paths = report.created + report.updated
    shared: list[Path] = []
    project: list[Path] = []
    global_files: list[Path] = []
    project_root = config.project_root
    home_dir = config.home_dir
    for path in all_paths:
        try:
            relative_to_project = path.relative_to(project_root)
        except ValueError:
            relative_to_project = None
        if relative_to_project is not None:
            if relative_to_project.parts and relative_to_project.parts[0] == ".bflow":
                shared.append(path)
            else:
                project.append(path)
            continue
        try:
            path.relative_to(home_dir)
            global_files.append(path)
        except ValueError:
            project.append(path)
    return shared, project, global_files


if __name__ == "__main__":
    raise SystemExit(main())
