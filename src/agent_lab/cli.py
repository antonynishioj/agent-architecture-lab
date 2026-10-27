"""
Command-line entry point: `uv run agent-lab <command>`.

    serve                 start the API server (the UI talks to it)
    benchmark             run the fixed benchmark from the terminal
    resume <run>          continue a paused or failed run
    list                  list runs
    report <run>          recompute summary.json from raw files and verify it
    replay <run>          re-execute a run offline from its LLM cache and verify it
    findings <run>        recompute the qualitative findings quoted in the blog
    blog [--run <run>]    build the illustrated Word blog post
"""

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

from agent_lab.analysis.report import build_summary, write_reports
from agent_lab.experiments.factory import Lab
from agent_lab.experiments.store import RunStore
from agent_lab.settings import PROJECT_ROOT, load_settings


def _resolve_run(lab: Lab, value: str) -> Path:
    path = Path(value)

    if path.is_dir():
        return path.resolve()

    found = lab.store.run_dir(value)

    if found is None:
        sys.exit(f"Run not found: {value}")

    return found


def _print_progress(event: dict) -> None:
    progress = event.get("progress")
    prefix = f"[{progress:3d}%] " if progress is not None else "       "

    if event.get("message"):
        print(prefix + event["message"], flush=True)


def _compare(expected: dict, actual: dict) -> list[str]:
    differences = []

    def walk(left, right, key: str) -> None:
        if isinstance(left, dict) and isinstance(right, dict):
            for name in sorted(set(left) | set(right)):
                walk(left.get(name), right.get(name), f"{key}.{name}")
        elif isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
            for index, (a, b) in enumerate(zip(left, right)):
                walk(a, b, f"{key}[{index}]")
        elif left != right:
            differences.append(f"{key}: published={left!r} recomputed={right!r}")

    walk(expected, actual, "summary")

    return differences


def cmd_serve(args) -> None:
    import uvicorn

    uvicorn.run(
        "agent_lab.api.app:app",
        host=args.host,
        port=args.port,
        reload=False,
    )


def cmd_benchmark(lab: Lab, args) -> None:
    cases = lab.loader.load_all()

    if args.cases:
        wanted = set(args.cases.split(","))
        cases = [case for case in cases if case.case_id in wanted]

    if args.difficulty:
        wanted = set(args.difficulty.split(","))
        cases = [case for case in cases if case.difficulty in wanted]

    manifest = lab.create_run(
        run_type="benchmark",
        cases=cases,
        trials=args.trials,
        architectures=args.architectures.split(",") if args.architectures else None,
        label=args.label,
    )

    print(f"Run {manifest.run_id} -> results/runs/{manifest.directory}")

    manifest = lab.engine().run(manifest.run_id, progress=_print_progress)
    print(f"\nStatus: {manifest.status}")
    print(f"Report: results/runs/{manifest.directory}/REPORT.md")


def cmd_resume(lab: Lab, args) -> None:
    path = _resolve_run(lab, args.run)
    manifest = RunStore.load_from_dir(path)
    manifest = lab.engine().run(manifest.run_id, progress=_print_progress)
    print(f"\nStatus: {manifest.status}")


def cmd_list(lab: Lab, _args) -> None:
    for manifest in lab.store.list():
        print(
            f"{manifest.run_id}  {manifest.status:<22} "
            f"{manifest.completed_items:>3}/{len(manifest.items):<3} "
            f"{manifest.directory}"
        )


def cmd_report(lab: Lab, args) -> None:
    path = _resolve_run(lab, args.run)
    published_file = path / "summary.json"

    if args.write or not published_file.exists():
        write_reports(path)
        print(f"Wrote summary.json, summary.csv and REPORT.md in {path}")
        return

    published = json.loads(published_file.read_text(encoding="utf-8"))
    recomputed = json.loads(json.dumps(build_summary(path)))
    differences = _compare(published, recomputed)

    if differences:
        print("MISMATCH between summary.json and the raw case files:")
        for line in differences[:50]:
            print("  " + line)
        sys.exit(1)

    print(f"VERIFIED: summary.json matches the raw case files in {path.name}.")
    print(f"Winner: {recomputed['winner']['winner']}. {recomputed['winner']['explanation']}")


def cmd_replay(lab: Lab, args) -> None:
    """
    Re-runs every completed unit from llm_cache.jsonl with no network
    access, then checks that the recomputed summary matches.
    """

    source = _resolve_run(lab, args.run)
    manifest = RunStore.load_from_dir(source)

    with tempfile.TemporaryDirectory() as temp:
        store = RunStore(Path(temp))
        target = Path(temp) / manifest.directory
        (target / "cases").mkdir(parents=True)

        for name in ("cases.json", "llm_cache.jsonl"):
            if (source / name).exists():
                shutil.copy(source / name, target / name)

        replay = manifest.model_copy(deep=True)
        replay.items = [item for item in replay.items if item.status == "completed"]

        for item in replay.items:
            item.status = "pending"
            item.file = None

        store.save(replay)

        engine = lab.offline_engine()
        engine.store = store
        engine.run(replay.run_id, offline=True)

        recomputed = json.loads((target / "summary.json").read_text(encoding="utf-8"))

    published = build_summary(source)
    published = json.loads(json.dumps(published))

    # Status and planned-unit counts legitimately differ when the
    # original run had failed units; compare the measurements only.
    for summary in (published, recomputed):
        summary.pop("status", None)
        summary["config"].pop("units_planned", None)

    differences = _compare(published, recomputed)

    if differences:
        print("MISMATCH after offline replay:")
        for line in differences[:50]:
            print("  " + line)
        sys.exit(1)

    print(
        f"VERIFIED: replayed {len(replay.items)} case-trials offline from the "
        f"LLM cache and reproduced every number in the summary."
    )


def cmd_findings(lab: Lab, args) -> None:
    from agent_lab.analysis.findings import all_findings

    path = _resolve_run(lab, args.run)
    print(json.dumps(all_findings(path), indent=2))


def cmd_blog(lab: Lab, args) -> None:
    try:
        from agent_lab.blog.build import build_blog, is_publishable
    except ImportError as exc:
        sys.exit(
            f"Missing blog dependencies ({exc.name}). Run: uv sync --extra blog"
        )

    run_path = _resolve_run(lab, args.run) if args.run else None

    if run_path is None:
        candidates = [
            manifest
            for manifest in lab.store.list()
            if manifest.run_type == "benchmark" and manifest.completed_items
        ]

        if candidates:
            best = max(
                candidates,
                key=lambda manifest: (manifest.completed_items, manifest.created_at),
            )
            run_path = lab.store.root / best.directory

    output = Path(args.output) if args.output else PROJECT_ROOT / "docs" / "blog" / "how-many-agents.docx"
    path = build_blog(run_path, output)
    print(f"Wrote {path}")

    if run_path is not None and is_publishable(build_summary(run_path)):
        print(f"Results from {run_path.name}")
    else:
        print(
            "No run covering all four difficulty tiers yet: the results "
            "sections are marked [pending]."
        )


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent-lab", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    serve = commands.add_parser("serve", help="start the API server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    benchmark = commands.add_parser("benchmark", help="run the fixed benchmark")
    benchmark.add_argument("--trials", type=int, default=3)
    benchmark.add_argument("--cases", help="comma-separated case ids")
    benchmark.add_argument("--difficulty", help="comma-separated: easy,medium,hard,adversarial")
    benchmark.add_argument("--architectures", help="comma-separated, e.g. 1-agent,4-agent")
    benchmark.add_argument("--label", default="")

    resume = commands.add_parser("resume", help="continue a paused run")
    resume.add_argument("run", help="run id or directory")

    commands.add_parser("list", help="list runs")

    report = commands.add_parser("report", help="recompute and verify a run summary")
    report.add_argument("run", help="run id or directory")
    report.add_argument("--write", action="store_true", help="overwrite summary files instead of verifying")

    replay = commands.add_parser("replay", help="re-run offline from the LLM cache and verify")
    replay.add_argument("run", help="run id or directory")

    findings = commands.add_parser("findings", help="recompute the qualitative findings")
    findings.add_argument("run", help="run id or directory")

    blog = commands.add_parser("blog", help="build the Word blog post")
    blog.add_argument("--run", help="run id or directory (default: largest benchmark run)")
    blog.add_argument("--output", help="output .docx path")

    args = parser.parse_args()

    if args.command == "serve":
        cmd_serve(args)
        return

    lab = Lab(load_settings())

    {
        "benchmark": cmd_benchmark,
        "resume": cmd_resume,
        "list": cmd_list,
        "report": cmd_report,
        "replay": cmd_replay,
        "findings": cmd_findings,
        "blog": cmd_blog,
    }[args.command](lab, args)


if __name__ == "__main__":
    main()
