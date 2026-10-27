import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from pydantic import BaseModel, Field

from agent_lab.experiments.case import ExperimentCase
from agent_lab.experiments.result import CaseTrialResult
from agent_lab.settings import PROJECT_ROOT


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def git_commit() -> str | None:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()

        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--", "src", "data/benchmark"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None

    if not commit:
        return None

    return f"{commit}-dirty" if dirty else commit


class RunItem(BaseModel):
    case_id: str
    trial: int
    status: str = "pending"  # pending | completed | failed
    error: str | None = None
    file: str | None = None


class RunManifest(BaseModel):
    """
    Everything needed to understand and reproduce a run.

    Written to results/runs/<dir>/manifest.json and committed to git.
    """

    run_id: str
    directory: str
    run_type: str  # benchmark | custom
    label: str = ""
    status: str = "queued"  # queued | running | paused | completed | completed_with_errors | failed

    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None

    generator_model: str
    judge_model: str
    generator_temperature: float
    judge_temperature: float
    max_output_tokens: int

    trials: int
    architectures: list[str]
    case_ids: list[str]

    benchmark_version: str | None = None
    benchmark_fingerprint: str | None = None
    prompt_fingerprint: str
    git_commit: str | None = None
    app_version: str = "0.2.0"

    items: list[RunItem] = Field(default_factory=list)

    @property
    def completed_items(self) -> int:
        return sum(item.status == "completed" for item in self.items)

    @property
    def failed_items(self) -> int:
        return sum(item.status == "failed" for item in self.items)


class RunStore:
    """
    File-based store for runs. One directory per run:

        results/runs/<UTC timestamp>_<type>_<run_id>/
            manifest.json     configuration and progress
            cases.json        exact questions + evidence used
            cases/*.json      one file per (case, trial) with full traces
            llm_cache.jsonl   every prompt and response
            summary.json      aggregated statistics and the winner
            summary.csv       per-architecture table
            REPORT.md         human-readable report
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def run_dir(self, run_id: str) -> Path | None:
        matches = sorted(self.root.glob(f"*_{run_id}"))

        if not matches:
            return None

        return matches[-1]

    def create(
        self,
        *,
        run_id: str,
        run_type: str,
        label: str,
        cases: list[ExperimentCase],
        trials: int,
        architectures: list[str],
        generator_model: str,
        judge_model: str,
        generator_temperature: float,
        judge_temperature: float,
        max_output_tokens: int,
        prompt_fingerprint: str,
        benchmark_version: str | None = None,
        benchmark_fingerprint: str | None = None,
    ) -> RunManifest:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        directory = f"{timestamp}_{run_type}_{run_id}"

        manifest = RunManifest(
            run_id=run_id,
            directory=directory,
            run_type=run_type,
            label=label,
            created_at=utc_now(),
            generator_model=generator_model,
            judge_model=judge_model,
            generator_temperature=generator_temperature,
            judge_temperature=judge_temperature,
            max_output_tokens=max_output_tokens,
            trials=trials,
            architectures=architectures,
            case_ids=[case.case_id for case in cases],
            benchmark_version=benchmark_version,
            benchmark_fingerprint=benchmark_fingerprint,
            prompt_fingerprint=prompt_fingerprint,
            git_commit=git_commit(),
            items=[
                RunItem(case_id=case.case_id, trial=trial)
                for trial in range(1, trials + 1)
                for case in cases
            ],
        )

        path = self.root / directory
        (path / "cases").mkdir(parents=True, exist_ok=True)

        self.save_cases(path, cases)
        self.save(manifest)

        return manifest

    def load(self, run_id: str) -> RunManifest | None:
        path = self.run_dir(run_id)

        if path is None:
            return None

        return self.load_from_dir(path)

    @staticmethod
    def load_from_dir(path: Path) -> RunManifest | None:
        manifest_file = path / "manifest.json"

        if not manifest_file.exists():
            return None

        return RunManifest.model_validate_json(
            manifest_file.read_text(encoding="utf-8")
        )

    def save(self, manifest: RunManifest) -> None:
        with self._lock:
            path = self.root / manifest.directory
            path.mkdir(parents=True, exist_ok=True)

            (path / "manifest.json").write_text(
                manifest.model_dump_json(indent=2),
                encoding="utf-8",
            )

    @staticmethod
    def save_cases(path: Path, cases: list[ExperimentCase]) -> None:
        (path / "cases.json").write_text(
            json.dumps(
                [case.model_dump() for case in cases],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    @staticmethod
    def load_cases(path: Path) -> list[ExperimentCase]:
        data = json.loads((path / "cases.json").read_text(encoding="utf-8"))

        return [ExperimentCase.model_validate(item) for item in data]

    @staticmethod
    def save_item(path: Path, result: CaseTrialResult) -> str:
        filename = f"{result.case_id}__t{result.trial}.json"

        (path / "cases" / filename).write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8",
        )

        return f"cases/{filename}"

    @staticmethod
    def load_items(path: Path) -> list[CaseTrialResult]:
        folder = path / "cases"

        if not folder.exists():
            return []

        return [
            CaseTrialResult.model_validate_json(
                file.read_text(encoding="utf-8")
            )
            for file in sorted(folder.glob("*.json"))
        ]

    def list(self) -> list[RunManifest]:
        manifests = []

        for path in sorted(self.root.iterdir(), reverse=True):
            if not path.is_dir():
                continue

            try:
                manifest = self.load_from_dir(path)
            except ValueError:
                continue

            if manifest is not None:
                manifests.append(manifest)

        return manifests
