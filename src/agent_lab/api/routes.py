from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket

from agent_lab.api.results import ResultStore
from agent_lab.api.schemas import (
    BenchmarkListItem,
    BenchmarkListResponse,
    CustomExperimentRequest,
    ExperimentStartResponse,
    ExperimentStatusResponse,
)
from agent_lab.api.state import JobManager
from agent_lab.experiments.benchmark import BenchmarkLoader
from agent_lab.experiments.case import ExperimentCase
from agent_lab.experiments.service import ExperimentService


class APIContext:
    def __init__(
        self,
        service: ExperimentService,
        benchmark_loader: BenchmarkLoader,
        result_store: ResultStore,
    ):
        self.service = service
        self.benchmark_loader = benchmark_loader
        self.result_store = result_store
        self.jobs = JobManager()


def _registry_progress(run) -> int:
    if run.total_cases == 0:
        return 0

    finished = (
        run.completed_cases
        + run.failed_cases
    )

    return int(
        finished
        / run.total_cases
        * 100
    )

def _update_job_from_event(
    context: APIContext,
    run_id: str,
    event: dict,
) -> None:
    stage = event.get("stage")

    progress = event.get("progress")

    if stage == "case_started":
        context.jobs.update(
            run_id,
            progress=(
                progress
                if progress is not None
                else 0
            ),
            message=(
                f"Running case: "
                f"{event.get('case_id')}"
            ),
            current_case=event.get("case_id"),
            current_architecture=None,
        )

    elif stage == "research_started":
        context.jobs.update(
            run_id,
            progress=(
                progress
                if progress is not None
                else 0
            ),
            message="Researching the question...",
        )

    elif stage == "research_loaded":
        context.jobs.update(
            run_id,
            progress=(
                progress
                if progress is not None
                else 0
            ),
            message="Frozen benchmark research loaded.",
        )

    elif stage == "research_completed":
        context.jobs.update(
            run_id,
            progress=(
                progress
                if progress is not None
                else 0
            ),
            message=(
                f"Research completed with "
                f"{event.get('source_count', 0)} sources."
            ),
        )

    elif stage == "architecture_started":
        architecture = event.get(
            "architecture"
        )

        context.jobs.update(
            run_id,
            progress=(
                progress
                if progress is not None
                else 0
            ),
            message=(
                f"Running "
                f"{architecture} architecture..."
            ),
            current_architecture=architecture,
        )

    elif stage == "architecture_completed":
        architecture = event.get(
            "architecture"
        )

        context.jobs.update(
            run_id,
            progress=(
                progress
                if progress is not None
                else 0
            ),
            message=(
                f"{architecture} architecture completed."
            ),
            current_architecture=architecture,
        )

    elif stage == "evaluation_started":
        context.jobs.update(
            run_id,
            progress=(
                progress
                if progress is not None
                else 0
            ),
            message=(
                f"Evaluating "
                f"{event.get('architecture', 'architecture')}..."
            ),
        )

    elif stage == "evaluation_completed":
        context.jobs.update(
            run_id,
            progress=(
                progress
                if progress is not None
                else 0
            ),
            message=(
                f"Evaluation completed for "
                f"{event.get('architecture', 'architecture')}."
            ),
        )

    elif stage == "case_completed":
        context.jobs.update(
            run_id,
            progress=(
                progress
                if progress is not None
                else 0
            ),
            message="Case completed.",
            current_architecture=None,
        )

    elif stage == "case_failed":
        context.jobs.update(
            run_id,
            progress=(
                progress
                if progress is not None
                else 0
            ),
            message=(
                f"Case failed: "
                f"{event.get('error')}"
            ),
            error=event.get("error"),
            current_architecture=None,
        )


def _progress_callback(
    context: APIContext,
    run_id: str,
):
    def callback(event: dict) -> None:
        _update_job_from_event(
            context=context,
            run_id=run_id,
            event=event,
        )

    return callback


def _run_custom(
    context: APIContext,
    run_id: str,
    case: ExperimentCase,
) -> None:
    try:
        context.service.run_custom(
            case=case,
            run_id=run_id,
            progress_callback=_progress_callback(
                context,
                run_id,
            ),
        )

        context.jobs.update(
            run_id,
            status="completed",
            progress=100,
            message="Custom experiment completed.",
            current_case=None,
            current_architecture=None,
        )

    except Exception as exc:
        context.jobs.update(
            run_id,
            status="failed",
            message="Custom experiment failed.",
            error=str(exc),
            current_case=None,
            current_architecture=None,
        )


def _run_benchmark(
    context: APIContext,
    run_id: str,
    cases: list[ExperimentCase],
) -> None:
    try:
        context.service.run_benchmark(
            cases=cases,
            run_id=run_id,
            progress_callback=_progress_callback(
                context,
                run_id,
            ),
        )

        run = context.service.registry.load(run_id)

        if run is None:
            raise RuntimeError(
                f"Run disappeared from registry: {run_id}"
            )

        if run.status == "completed_with_errors":
            context.jobs.update(
                run_id,
                status="completed_with_errors",
                progress=100,
                message=(
                    f"Benchmark completed with "
                    f"{run.failed_cases} failed case(s)."
                ),
                current_case=None,
                current_architecture=None,
            )
        else:
            context.jobs.update(
                run_id,
                status="completed",
                progress=100,
                message="Benchmark completed.",
                current_case=None,
                current_architecture=None,
            )

    except Exception as exc:
        context.jobs.update(
            run_id,
            status="failed",
            message="Benchmark failed.",
            error=str(exc),
            current_case=None,
            current_architecture=None,
        )


def create_router(
    context: APIContext,
) -> APIRouter:

    router = APIRouter(
        prefix="/api",
    )

    @router.get("/health")
    def health():
        return {
            "status": "healthy",
        }

    @router.get(
        "/benchmarks",
        response_model=BenchmarkListResponse,
    )
    def list_benchmarks():
        cases = context.benchmark_loader.load_all()

        return BenchmarkListResponse(
            count=len(cases),
            cases=[
                BenchmarkListItem(
                    case_id=case.case_id,
                    category=case.category,
                    difficulty=case.difficulty,
                    question=case.question,
                )
                for case in cases
            ],
        )

    @router.get("/benchmarks/{case_id}")
    def get_benchmark(case_id: str):
        try:
            case = context.benchmark_loader.load_case(
                case_id
            )
        except KeyError:
            raise HTTPException(
                status_code=404,
                detail=f"Benchmark case not found: {case_id}",
            )

        return case.model_dump()

    @router.post(
        "/experiments/custom",
        response_model=ExperimentStartResponse,
    )
    def start_custom_experiment(
        request: CustomExperimentRequest,
        background_tasks: BackgroundTasks,
    ):
        run, case = context.service.create_custom_run(
            question=request.question,
            reference_answer=request.reference_answer,
            category=request.category,
            difficulty=request.difficulty,
        )

        context.jobs.create(
            run_id=run.run_id,
            case_id=case.case_id,
        )

        background_tasks.add_task(
            _run_custom,
            context,
            run.run_id,
            case,
        )

        return ExperimentStartResponse(
            run_id=run.run_id,
            status="queued",
            message="Custom experiment started.",
        )

    @router.post(
        "/experiments/benchmark",
        response_model=ExperimentStartResponse,
    )
    def start_benchmark(
        background_tasks: BackgroundTasks,
    ):
        cases = context.benchmark_loader.load_all()

        if not cases:
            raise HTTPException(
                status_code=400,
                detail="No benchmark cases are configured.",
            )

        run = context.service.create_benchmark_run(
            cases=cases,
        )

        context.jobs.create(
            run_id=run.run_id,
        )

        background_tasks.add_task(
            _run_benchmark,
            context,
            run.run_id,
            cases,
        )

        return ExperimentStartResponse(
            run_id=run.run_id,
            status="queued",
            message=(
                f"Benchmark started with "
                f"{len(cases)} cases."
            ),
        )

    @router.get(
        "/experiments/{run_id}/status",
        response_model=ExperimentStatusResponse,
    )
    def get_experiment_status(
        run_id: str,
    ):
        job = context.jobs.get(run_id)

        if job is not None:
            return ExperimentStatusResponse(
                run_id=job.run_id,
                status=job.status,
                progress=job.progress,
                message=job.message,
                case_id=job.case_id,
                current_case=job.current_case,
                current_architecture=job.current_architecture,
                error=job.error,
            )

        run = context.service.registry.load(run_id)

        if run is None:
            raise HTTPException(
                status_code=404,
                detail=f"Run not found: {run_id}",
            )

        return ExperimentStatusResponse(
            run_id=run.run_id,
            status=run.status,
            progress=(
                _registry_progress(run)
                if run.total_cases
                else 0
            ),
            message=(
                f"{run.completed_cases}/"
                f"{run.total_cases} cases completed."
            ),
            error=None,
        )

    @router.get("/experiments/{run_id}")
    def get_experiment_results(
        run_id: str,
    ):
        result = context.result_store.find(
            run_id
        )

        if result is not None:
            return result

        run = context.service.registry.load(
            run_id
        )

        if run is None:
            raise HTTPException(
                status_code=404,
                detail=f"Run not found: {run_id}",
            )

        return {
            "run_id": run_id,
            "status": run.status,
            "total_cases": run.total_cases,
            "completed_cases": run.completed_cases,
            "failed_cases": run.failed_cases,
            "cases": [
                case.model_dump()
                for case in run.cases
            ],
        }

    @router.websocket(
        "/ws/experiments/{run_id}"
    )
    async def experiment_websocket(
        websocket: WebSocket,
        run_id: str,
    ):
        await websocket.accept()

        try:
            while True:
                job = context.jobs.get(run_id)

                if job is None:
                    run = context.service.registry.load(
                        run_id
                    )

                    if run is None:
                        await websocket.send_json(
                            {
                                "status": "not_found",
                                "run_id": run_id,
                            }
                        )
                        break

                    payload = {
                        "run_id": run.run_id,
                        "status": run.status,
                        "progress": (
                            int(
                                (
                                    run.completed_cases
                                    + run.failed_cases
                                )
                                / run.total_cases
                                * 100
                            )
                            if run.total_cases
                            else 0
                        ),
                        "message": (
                            f"{run.completed_cases}/"
                            f"{run.total_cases} cases completed."
                        ),
                    }
                else:
                    payload = {
                        "run_id": job.run_id,
                        "status": job.status,
                        "progress": job.progress,
                        "message": job.message,
                        "case_id": job.case_id,
                        "current_case": job.current_case,
                        "current_architecture": (
                            job.current_architecture
                        ),
                        "error": job.error,
                    }

                await websocket.send_json(payload)

                if payload["status"] in {
                    "completed",
                    "completed_with_errors",
                    "failed",
                    "not_found",
                }:
                    break

                import asyncio

                await asyncio.sleep(0.5)

        finally:
            await websocket.close()

    return router