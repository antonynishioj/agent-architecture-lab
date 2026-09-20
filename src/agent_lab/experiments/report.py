from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from agent_lab.evaluation.experiment_result import (
    EvaluatedExperimentResult,
)
from agent_lab.experiments.experiment import ExperimentResult


class ExperimentReport(BaseModel):
    run_id: str
    experiment: ExperimentResult
    evaluation: EvaluatedExperimentResult

    def save(
        self,
        directory: str = "data/results/cases",
    ) -> Path:

        output_directory = Path(directory)

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%dT%H%M%SZ"
        )

        filename = (
            f"{self.run_id}_"
            f"{self.experiment.case_id}_"
            f"{timestamp}.json"
        )

        output_file = (
            output_directory / filename
        )

        output_file.write_text(
            self.model_dump_json(
                indent=2
            ),
            encoding="utf-8",
        )

        return output_file