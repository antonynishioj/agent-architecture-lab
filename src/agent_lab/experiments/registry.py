import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from pydantic import BaseModel, Field


class CaseRunState(BaseModel):
    case_id: str
    status: str = "pending"
    error: str | None = None
    result_file: str | None = None


class ExperimentRun(BaseModel):
    run_id: str
    run_type: str
    status: str = "queued"

    created_at: str
    started_at: str | None = None
    completed_at: str | None = None

    total_cases: int = 0
    completed_cases: int = 0
    failed_cases: int = 0

    cases: list[CaseRunState] = Field(
        default_factory=list
    )


class RunRegistry:
    def __init__(
        self,
        directory: str = "data/results/runs",
    ):
        self.directory = Path(directory)
        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._lock = Lock()

    def _path(
        self,
        run_id: str,
    ) -> Path:

        return self.directory / f"{run_id}.json"

    def create(
        self,
        run_id: str,
        run_type: str,
        case_ids: list[str],
    ) -> ExperimentRun:

        now = datetime.now(
            timezone.utc
        ).isoformat()

        run = ExperimentRun(
            run_id=run_id,
            run_type=run_type,
            status="queued",
            created_at=now,
            total_cases=len(case_ids),
            cases=[
                CaseRunState(
                    case_id=case_id
                )
                for case_id in case_ids
            ],
        )

        self.save(run)

        return run

    def load(
        self,
        run_id: str,
    ) -> ExperimentRun:

        path = self._path(run_id)

        if not path.exists():
            raise FileNotFoundError(
                f"Run not found: {run_id}"
            )

        return ExperimentRun.model_validate_json(
            path.read_text(
                encoding="utf-8"
            )
        )

    def save(
        self,
        run: ExperimentRun,
    ) -> None:

        with self._lock:

            self._path(
                run.run_id
            ).write_text(
                run.model_dump_json(
                    indent=2
                ),
                encoding="utf-8",
            )

    def update_status(
        self,
        run_id: str,
        status: str,
    ) -> ExperimentRun:

        run = self.load(run_id)

        run.status = status

        now = datetime.now(
            timezone.utc
        ).isoformat()

        if status == "running":
            run.started_at = now

        elif status in {
            "completed",
            "failed",
        }:
            run.completed_at = now

        self.save(run)

        return run

    def update_case(
        self,
        run_id: str,
        case_id: str,
        status: str,
        *,
        error: str | None = None,
        result_file: str | None = None,
    ) -> ExperimentRun:

        run = self.load(run_id)

        for case in run.cases:

            if case.case_id != case_id:
                continue

            previous_status = case.status

            case.status = status
            case.error = error
            case.result_file = result_file

            if (
                status == "completed"
                and previous_status != "completed"
            ):
                run.completed_cases += 1

            if (
                status == "failed"
                and previous_status != "failed"
            ):
                run.failed_cases += 1

            break

        self.save(run)

        return run

    def pending_cases(
        self,
        run_id: str,
    ) -> list[CaseRunState]:

        run = self.load(run_id)

        return [
            case
            for case in run.cases
            if case.status != "completed"
        ]