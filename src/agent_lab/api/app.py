from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_lab.api.routes import APIContext, create_router
from agent_lab.experiments.factory import Lab
from agent_lab.settings import load_settings


def create_app() -> FastAPI:
    context = APIContext(Lab(load_settings()))

    app = FastAPI(
        title="AI Agent Architecture Lab",
        description=(
            "Experimental framework for measuring "
            "different AI agent architectures."
        ),
        version="0.2.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(create_router(context))

    return app


app = create_app()
