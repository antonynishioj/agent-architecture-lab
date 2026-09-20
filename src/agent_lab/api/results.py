import json
from pathlib import Path


class ResultStore:
    def __init__(
        self,
        directory: str = "data/results/cases",
    ):
        self.directory = Path(directory)

    def find(
        self,
        run_id: str,
    ) -> dict | None:

        if not self.directory.exists():
            return None

        for path in self.directory.glob("*.json"):
            try:
                data = json.loads(
                    path.read_text(
                        encoding="utf-8"
                    )
                )
            except (
                json.JSONDecodeError,
                OSError,
            ):
                continue

            if data.get("run_id") == run_id:
                return data

        return None