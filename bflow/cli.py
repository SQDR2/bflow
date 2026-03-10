from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

try:
    import termios
    import tty
except ImportError:  # pragma: no cover - non-Unix fallback
    termios = None
    tty = None

from bflow import __version__
from bflow.doctor import format_report, run_doctor, summarize_status
from bflow.installer import InitConfig, load_saved_config, run_init
from bflow.templates import SUPPORTED_AGENTS


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"


def use_color() -> bool:
    return sys.stdout.isatty() and os.environ.get("TERM") != "dumb" and "NO_COLOR" not in os.environ


def style(text: str, *codes: str) -> str:
    if not use_color() or not codes:
        return text
    return "".join(codes) + text + RESET


def print_section(title: str) -> None:
    print("")
    print(style(f"◆ {title}", BOLD, CYAN))


def print_banner() -> None:
    banner = [
        " ____  ____   ___  _ _ _ _____ ____  ____  ",
        "| __ )|  _ \\ / _ \\| | | | ____|  _ \\/ ___| ",
        "|  _ \\| |_) | | | | | | |  _| | |_) \\___ \\",
        "| |_) |  _ <| |_| | |_| | |___|  _ < ___) |",
        "|____/|_| \\_\\___/ \\___/|_____|_| \\_\\____/ ",
        "                 browers flow                 ",
    ]
    width = max(len(line) for line in banner)
    print("")
    print(style("─" * width, DIM, CYAN))
    for line in banner:
        print(style(line, BOLD, MAGENTA))
    print(style("─" * width, DIM, CYAN))


def print_kv(label: str, value: str) -> None:
    print(f"  {style(label + ':', BOLD)} {value}")


def render_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def format_commands(prefix: str) -> str:
    return ", ".join(
        [f"/{prefix}-new", f"/{prefix}-explore", f"/{prefix}-replay", f"/{prefix}-diagnose"]
    )


def print_path_group(title: str, paths: list[Path], project_root: Path) -> None:
    if not paths:
        return
    print_section(title)
    for path in paths:
        print(f"  {style('•', CYAN)} {render_path(path, project_root)}")


def supports_interactive_menu() -> bool:
    return termios is not None and tty is not None and sys.stdin.isatty() and sys.stdout.isatty()


def read_key() -> str:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        first = sys.stdin.read(1)
        if first == "\x1b":
            second = sys.stdin.read(1)
            third = sys.stdin.read(1)
            return first + second + third
        return first
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def ask_agents_with_menu(descriptions: dict[str, str]) -> list[str]:
    index = 0
    options = list(SUPPORTED_AGENTS)
    print_section("Agents / 目标 Agent")
    print(style("  ↑/↓ 切换    Space 选择    Enter 确认", DIM))
    for _ in options:
        print("")

    try:
        print("\033[?25l", end="")
        while True:
            print(f"\033[{len(options)}A", end="")
            for current, agent in enumerate(options):
                active = current == index
                prefix = style("›", BOLD, CYAN) if active else " "
                radio = style("◉", BOLD, GREEN) if active else style("○", DIM)
                description = style(descriptions[agent], DIM) if not active else descriptions[agent]
                print(f"\r\033[2K  {prefix} {radio} {agent:<8} {description}")

            key = read_key()
            if key == "\x1b[A":
                index = (index - 1) % len(options)
                continue
            if key == "\x1b[B":
                index = (index + 1) % len(options)
                continue
            if key in {" ", "\r", "\n"}:
                print(f"\r\033[2K  {style('✓', BOLD, GREEN)} Selected: {options[index]}")
                return [options[index]]
            if key == "\x03":
                raise KeyboardInterrupt
    finally:
        print("\033[?25h", end="")


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
    parser.add_argument("--scope", choices=("project", "global", "both"), help=argparse.SUPPRESS)
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
    print_section("Supported agents / 支持的 Agent")
    for agent in SUPPORTED_AGENTS:
        print(f"  {style('•', CYAN)} {agent}")
    return 0


def run_init_command(args: argparse.Namespace) -> int:
    interactive = not any([args.agents, args.prefix])
    print_banner()
    config = InitConfig(
        project_root=Path(args.project_root).resolve(),
        scope="project",
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


def ask_agents() -> list[str]:
    descriptions = {
        "claude": "Claude Code skills",
        "opencode": "OpenCode commands",
        "copilot": "GitHub Copilot prompt files",
        "codex": "Codex prompts and AGENTS guidance",
    }
    if supports_interactive_menu():
        return ask_agents_with_menu(descriptions)

    print_section("Agents / 目标 Agent")
    for index, agent in enumerate(SUPPORTED_AGENTS, start=1):
        print(f"  {style(str(index) + '.', BOLD, CYAN)} {agent:<8} {style(descriptions[agent], DIM)}")
    while True:
        value = input("Choose one number or name (default: copilot): ").strip().lower()
        if not value:
            return ["copilot"]
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
            agents = parse_agents(",".join(mapped))
            if len(agents) != 1:
                raise SystemExit("Please choose exactly one agent in interactive mode.")
            return agents
        except SystemExit as exc:
            print(exc)


def ask_prefix() -> str:
    default = "bflow"
    print_section("Command prefix / 命令前缀")
    value = input("Command prefix / 命令前缀 (default: bflow): ").strip()
    return value or default


def ask_confirmation(config: InitConfig) -> bool:
    print_section("Initialization summary / 初始化摘要")
    print_kv("Project root", str(config.project_root))
    print_kv("Agents", ", ".join(config.agents))
    print_kv("Commands", format_commands(config.prefix))
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
    print_section("bflow initialization complete / 初始化完成")
    print_kv("Project root", str(config.project_root))
    print_kv("Prefix", f"/{config.prefix}-*")
    print_kv("Agents", ", ".join(config.agents))
    print_kv("Created", style(str(len(report.created)), BOLD, GREEN))
    print_kv("Updated", style(str(len(report.updated)), BOLD, YELLOW))
    print_path_group("Shared workflow files / 共享工作流文件", shared_paths, config.project_root)
    print_path_group("Project adapter files / 项目级适配文件", project_paths, config.project_root)
    print_path_group("Global adapter files / 全局适配文件", global_paths, config.project_root)
    if report.warnings:
        print_section("Warnings / 警告")
        for warning in report.warnings:
            print(f"  {style('•', YELLOW)} {warning}")
    print_section("Prerequisites / 前置依赖")
    print("  1. Install `chrome-devtools-mcp` in each target agent before using replay or diagnose workflows.")
    print("     在使用 replay 或 diagnose 工作流之前，请先在对应的 Agent 中安装 `chrome-devtools-mcp`。")
    print("     https://github.com/ChromeDevTools/chrome-devtools-mcp")
    print("  2. Install or connect `agent-browser` in each target agent before using explore workflows.")
    print("     在使用 explore 工作流之前，请先在对应的 Agent 中安装或接入 `agent-browser`。")
    print("     https://github.com/vercel-labs/agent-browser")
    print_section("Next steps / 下一步")
    print("  1. Restart your agent UI if slash commands are loaded only on startup.")
    print("     如果你的 Agent 只在启动时加载命令，请先重启。")
    print(f"  2. Try /{config.prefix}-new with a natural-language browser test request.")
    print(f"     先试一下 /{config.prefix}-new，并输入一段自然语言测试需求。")
    print(f"  3. After the draft case is created, run /{config.prefix}-explore to confirm stable steps.")
    print(f"     case 草稿生成后，再执行 /{config.prefix}-explore 来确认稳定步骤。")


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
