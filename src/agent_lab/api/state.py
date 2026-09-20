from dataclasses import dataclass
from threading import Lock


@dataclass
class JobState:
    run_id: str
    status: str
    progress: int = 0
    message: str = ""
    case_id: str | None = None
    current_case: str | None = None
    current_architecture: str | None = None
    error: str | None = None


class JobManager:
    def __init__(self):
        self._jobs: dict[str, JobState] = {}
        self._lock = Lock()

    def create(
        self,
        run_id: str,
        case_id: str | None = None,
    ) -> JobState:

        job = JobState(
            run_id=run_id,
            status="queued",
            progress=0,
            message="Experiment queued.",
            case_id=case_id,
        )

        with self._lock:
            self._jobs[run_id] = job

        return job

    def update(
        self,
        run_id: str,
        *,
        status: str | None = None,
        progress: int | None = None,
        message: str | None = None,
        current_case: str | None = None,
        current_architecture: str | None = None,
        error: str | None = None,
    ) -> JobState:

        with self._lock:
            job = self._jobs[run_id]

            if status is not None:
                job.status = status

            if progress is not None:
                job.progress = max(0, min(100, progress))

            if message is not None:
                job.message = message

            if current_case is not None:
                job.current_case = current_case

            if current_architecture is not None:
                job.current_architecture = current_architecture

            if error is not None:
                job.error = error

            return job

    def get(self, run_id: str) -> JobState | None:
        with self._lock:
            return self._jobs.get(run_id)