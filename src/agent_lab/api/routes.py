import asyncio
import json
from threading import Thread

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse

from agent_lab.analysis.report import build_summary, summary_csv
from agent_lab.api.schemas import (
    BenchmarkRunRequest,
    CustomExperimentRequest,
    ExperimentStartResponse,
)
from agent_lab.api.state import JobManager
from agent_lab.architectures.definitions import ARCHITECTURES
from agent_lab.architectures.roles import ROLE_SPECS
from agent_lab.experiments.case import ExperimentCase
from agent_lab.experiments.engine import calls_per_item
from agent_lab.experiments.factory import Lab
from agent_lab.research.result import ResearchBundle, SearchResult


TERMINAL_STATUSES = {"completed", "completed_with_errors", "failed", "paused"}


class APIContext:
    def __init__(self, lab: Lab):
        self.lab = lab
        self.jobs = JobManager()


def _execute(context: APIContext, run_id: str) -> None:
    """Runs in a background thread; the manifest records the outcome."""

    try:
        manifest = context.lab.engine().run(
            run_id,
            progress=lambda event: context.jobs.record_event(run_id, event),
        )

        context.jobs.update(
            run_id,
            status=manifest.status,
            progress=100,
            message=(
                "Run completed."
                if manifest.status == "completed"
                else f"Run completed with {manifest.failed_items} failed unit(s)."
            ),
        )
    except Exception as exc:
        manifest = context.lab.store.load(run_id)
        status = manifest.status if manifest and manifest.status == "paused" else "failed"

        if manifest and status == "failed":
            manifest.status = "failed"
            manifest.error = str(exc)
            context.lab.store.save(manifest)

        context.jobs.update(
            run_id,
            status=status,
            message=(
                "Paused: quota reached. Resume later from Run history."
                if status == "paused"
                else "Run failed."
            ),
            error=str(exc),
        )


def _ensure_can_start(context: APIContext) -> None:
    active = context.jobs.active()

    if active is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Run {active.run_id} is still in progress. Only one run "
                f"executes at a time so runs do not compete for quota."
            ),
        )

    if not context.lab.settings.gemini_api_key:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY is not set in the .env file.",
        )


def _start(context: APIContext, run_id: str) -> None:
    """Call _ensure_can_start first, before creating any run on disk."""

    context.jobs.create(run_id)
    Thread(target=_execute, args=(context, run_id), daemon=True).start()


def _job_payload(context: APIContext, run_id: str) -> dict | None:
    job = context.jobs.get(run_id)

    if job is not None:
        return job.to_dict()

    manifest = context.lab.store.load(run_id)

    if manifest is None:
        return None

    finished = manifest.completed_items + manifest.failed_items

    return {
        "run_id": run_id,
        "status": manifest.status,
        "progress": int(finished / max(1, len(manifest.items)) * 100),
        "message": f"{finished}/{len(manifest.items)} case-trials finished.",
        "current_case": None,
        "current_trial": None,
        "current_architecture": None,
        "error": manifest.error,
        "events": [],
    }


def create_router(context: APIContext) -> APIRouter:
    router = APIRouter(prefix="/api")
    lab = context.lab

    @router.get("/health")
    def health():
        return {"status": "healthy"}

    @router.get("/config")
    def config():
        settings = lab.settings

        return {
            "generator_model": settings.generator_model,
            "judge_model": settings.judge_model,
            "generator_rpm": settings.generator_rpm,
            "judge_rpm": settings.judge_rpm,
            "generator_rpd": settings.generator_rpd,
            "judge_rpd": settings.judge_rpd,
            "api_key_configured": bool(settings.gemini_api_key),
            "tavily_enabled": settings.tavily_enabled,
            "usage_today": lab.usage.today(),
            "active_run": (
                job.run_id if (job := context.jobs.active()) else None
            ),
            "architectures": [
                {
                    "name": architecture.name,
                    "agent_count": architecture.agent_count,
                    "description": architecture.description,
                    "agents": [
                        [ROLE_SPECS[role].title for role in agent.responsibilities]
                        for agent in architecture.agents
                    ],
                    "calls_per_case": calls_per_item([architecture.name]),
                }
                for architecture in ARCHITECTURES
            ],
        }

    @router.get("/benchmarks")
    def list_benchmarks(difficulty: str | None = None):
        cases = lab.loader.load_all()

        return {
            "version": lab.loader.version(),
            "cases": [
                {
                    "case_id": case.case_id,
                    "category": case.category,
                    "difficulty": case.difficulty,
                    "question": case.question,
                    "design_notes": case.design_notes,
                    "key_points": len(case.key_points),
                    "sources": len(case.research.results) if case.research else 0,
                }
                for case in cases
                if difficulty is None or case.difficulty == difficulty
            ],
        }

    @router.get("/benchmarks/{case_id}")
    def get_benchmark(case_id: str):
        try:
            return lab.loader.load_case(case_id).model_dump()
        except KeyError:
            raise HTTPException(404, f"Benchmark case not found: {case_id}")

    @router.post("/experiments/benchmark", response_model=ExperimentStartResponse)
    def start_benchmark(request: BenchmarkRunRequest):
        _ensure_can_start(context)
        cases = lab.loader.load_all()

        if request.case_ids:
            wanted = set(request.case_ids)
            cases = [case for case in cases if case.case_id in wanted]

        try:
            manifest = lab.create_run(
                run_type="benchmark",
                cases=cases,
                trials=request.trials,
                architectures=request.architectures,
                label=request.label,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc))

        _start(context, manifest.run_id)

        return ExperimentStartResponse(
            run_id=manifest.run_id,
            status="queued",
            message=f"Benchmark started: {len(cases)} cases × {request.trials} trials.",
        )

    @router.post("/experiments/custom", response_model=ExperimentStartResponse)
    def start_custom(request: CustomExperimentRequest):
        _ensure_can_start(context)
        research = None

        if request.sources_mode == "manual":
            if not request.sources:
                raise HTTPException(400, "Paste at least one source.")

            research = ResearchBundle(
                query=request.question,
                results=[
                    SearchResult(**source.model_dump())
                    for source in request.sources
                ],
            )
        elif not lab.settings.tavily_enabled:
            raise HTTPException(
                400,
                "Web search needs TAVILY_API_KEY in .env. Paste sources instead.",
            )

        case = ExperimentCase(
            case_id="custom",
            question=request.question,
            reference_answer=request.reference_answer or None,
            key_points=[point for point in request.key_points if point.strip()],
            must_not_claim=[claim for claim in request.must_not_claim if claim.strip()],
            category=request.category or "Custom",
            difficulty=request.difficulty or "custom",
            source_kind="user" if research else "web",
            research=research,
        )

        try:
            manifest = lab.create_run(
                run_type="custom",
                cases=[case],
                trials=request.trials,
                architectures=request.architectures,
                label=request.label,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc))

        _start(context, manifest.run_id)

        return ExperimentStartResponse(
            run_id=manifest.run_id,
            status="queued",
            message="Custom experiment started.",
        )

    @router.get("/experiments/{run_id}/status")
    def get_status(run_id: str):
        payload = _job_payload(context, run_id)

        if payload is None:
            raise HTTPException(404, f"Run not found: {run_id}")

        return payload

    @router.get("/runs")
    def list_runs():
        return [
            {
                "run_id": manifest.run_id,
                "directory": manifest.directory,
                "run_type": manifest.run_type,
                "label": manifest.label,
                "status": (
                    "running"
                    if (job := context.jobs.get(manifest.run_id))
                    and job.status in {"queued", "running"}
                    else manifest.status
                ),
                "created_at": manifest.created_at,
                "trials": manifest.trials,
                "case_count": len(manifest.case_ids),
                "architectures": manifest.architectures,
                "completed_items": manifest.completed_items,
                "failed_items": manifest.failed_items,
                "total_items": len(manifest.items),
                "generator_model": manifest.generator_model,
                "error": manifest.error,
            }
            for manifest in lab.store.list()
        ]

    def _run_path(run_id: str):
        path = lab.store.run_dir(run_id)

        if path is None:
            raise HTTPException(404, f"Run not found: {run_id}")

        return path

    @router.get("/runs/{run_id}")
    def get_run(run_id: str):
        path = _run_path(run_id)
        manifest = lab.store.load_from_dir(path)

        return {
            "manifest": manifest.model_dump() if manifest else None,
            "cases": [case.model_dump() for case in lab.store.load_cases(path)],
            "items": [item.model_dump() for item in lab.store.load_items(path)],
        }

    @router.get("/runs/{run_id}/summary")
    def get_summary(run_id: str):
        return build_summary(_run_path(run_id))

    @router.get("/runs/{run_id}/export.csv", response_class=PlainTextResponse)
    def export_csv(run_id: str):
        return PlainTextResponse(
            summary_csv(build_summary(_run_path(run_id))),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{run_id}.csv"'},
        )

    @router.post("/runs/{run_id}/resume", response_model=ExperimentStartResponse)
    def resume_run(run_id: str):
        manifest = lab.store.load(run_id)

        if manifest is None:
            raise HTTPException(404, f"Run not found: {run_id}")

        if manifest.status == "completed":
            raise HTTPException(400, "This run is already complete.")

        _ensure_can_start(context)

        _start(context, run_id)

        return ExperimentStartResponse(
            run_id=run_id,
            status="queued",
            message="Run resumed. Cached calls are reused.",
        )

    @router.websocket("/ws/experiments/{run_id}")
    async def experiment_websocket(websocket: WebSocket, run_id: str):
        await websocket.accept()

        try:
            last = None

            while True:
                payload = _job_payload(context, run_id) or {
                    "run_id": run_id,
                    "status": "not_found",
                }

                encoded = json.dumps(payload, sort_keys=True)

                if encoded != last:
                    await websocket.send_json(payload)
                    last = encoded

                if payload["status"] in TERMINAL_STATUSES | {"not_found"}:
                    break

                await asyncio.sleep(0.5)
        except WebSocketDisconnect:
            return

        await websocket.close()

    return router
