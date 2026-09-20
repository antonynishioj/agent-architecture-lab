import json
from pathlib import Path

from agent_lab.research.result import ResearchBundle


class ResearchCache:

    def __init__(self, directory: str = "data/research"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, bundle: ResearchBundle, case_id: str) -> Path:
        path = self.directory / f"{case_id}.json"

        path.write_text(
            bundle.model_dump_json(indent=2),
            encoding="utf-8",
        )

        return path

    def load(self, case_id: str) -> ResearchBundle:
        path = self.directory / f"{case_id}.json"

        if not path.exists():
            raise FileNotFoundError(
                f"No cached research found for case: {case_id}"
            )

        return ResearchBundle.model_validate_json(
            path.read_text(encoding="utf-8")
        )