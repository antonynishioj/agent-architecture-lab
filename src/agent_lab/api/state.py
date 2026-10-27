import time
from dataclasses import asdict, dataclass, field
from threading import Lock


@dataclass
class JobState:
    run_id: str
    status: str
    progress: int = 0
    message: str = ""
    current_case: str | None = None
    current_trial: int | None = None
    current_architecture: str | None = None
    error: str | None = None
    events: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


ACTIVE_STATUSES = {"queued", "running"}


class JobManager:
    """
    In-memory progress for runs executing in this server process.

    The durable state lives in the run's manifest.json. This only
    holds the live progress feed shown in the UI.
    """

    MAX_EVENTS = 40

    def __init__(self):
        self._jobs: dict[str, JobState] = {}
        self._lock = Lock()

    def create(self, run_id: str) -> JobState:
        job = JobState(
            run_id=run_id,
            status="queued",
            message="Experiment queued.",
        )

        with self._lock:
            self._jobs[run_id] = job

        return job

    def active(self) -> JobState | None:
        with self._lock:
            for job in self._jobs.values():
                if job.status in ACTIVE_STATUSES:
                    return job

        return None

    def update(self, run_id: str, **changes) -> None:
        with self._lock:
            job = self._jobs[run_id]

            for key, value in changes.items():
                setattr(job, key, value)

    def record_event(self, run_id: str, event: dict) -> None:
        with self._lock:
            job = self._jobs.get(run_id)

            if job is None:
                return

            job.status = "running"

            if event.get("progress") is not None:
                job.progress = max(job.progress, int(event["progress"]))

            if event.get("message"):
                job.message = event["message"]

            if "case_id" in event:
                job.current_case = event["case_id"]

            if "trial" in event:
                job.current_trial = event["trial"]

            if "architecture" in event:
                job.current_architecture = event["architecture"]

            if event.get("message"):
                job.events.append(
                    {
                        "time": time.strftime("%H:%M:%S"),
                        "stage": event.get("stage"),
                        "message": event["message"],
                    }
                )
                job.events = job.events[-self.MAX_EVENTS:]

    def get(self, run_id: str) -> JobState | None:
        with self._lock:
            job = self._jobs.get(run_id)

            if job is None:
                return None

            return JobState(**{**job.to_dict(), "events": list(job.events)})
