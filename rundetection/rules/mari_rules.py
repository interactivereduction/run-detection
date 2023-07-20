"""
Mari Rules
"""
import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import List, Any

from rundetection.ingest import JobRequest, get_run_title
from rundetection.rules.rule import Rule

logger = logging.getLogger(__name__)


class MariStitchRule(Rule[bool]):
    """
    The MariStitchRule is the rule that applies
    """

    def __init__(self, value: bool) -> None:

        super().__init__(value)
        self._spec_values = self._load_mari_spec()

    @staticmethod
    def _get_previous_run_path(run_number: int, run_path: Path) -> Path:
        return Path(run_path.parent, f"MAR{run_number - 1}.nxs")

    def _get_runs_to_stitch(self, run_path: Path, run_number: int, run_title: str) -> List[int]:
        run_numbers = []
        while run_path.exists():
            if get_run_title(run_path) != run_title:
                break
            run_numbers.append(run_number)
            run_number -= 1
            run_path = self._get_previous_run_path(run_number, run_path)
        return run_numbers

    @staticmethod
    def _load_mari_spec() -> Any:
        """
        Load the entire mari specification into a dictionary
        :return: Mari spec as dict
        """
        try:
            with open(
                "rundetection/specifications/mari_specification.json",
                "r",
                encoding="utf-8",
            ) as spec_file:
                return json.load(spec_file)
        except FileNotFoundError:
            logger.warning("Mari Specification could not be reloaded")
            raise RuntimeError("Mari specification is no longer available")

    def verify(self, job_request: JobRequest) -> None:
        if not self._value:  # if the stitch rule is set to false, skip
            return

        run_numbers = self._get_runs_to_stitch(
            job_request.filepath, job_request.run_number, job_request.experiment_title
        )
        if len(run_numbers) > 1:
            additional_request = deepcopy(job_request)
            additional_request.additional_values["runno"] = run_numbers
            additional_request.additional_values["sum_runs"] = True
            # We must reapply the common mari rules manually here, if we apply the whole spec automatically it will
            # produce an infinite loop
            additional_request.additional_values["mask_file_link"] = self._spec_values["marimaskfile"]
            additional_request.additional_values["wbvan"] = self._spec_values["mariwbvan"]
            job_request.additional_requests.append(additional_request)


class MariMaskFileRule(Rule[str]):
    """
    Adds the permalink of the maskfile to the additional outputs
    """

    def verify(self, job_request: JobRequest) -> None:
        job_request.additional_values["mask_file_link"] = self._value


class MariWBVANRule(Rule[int]):
    """
    Inserts the cycles wbvan number into the script. This value is manually calculated by the MARI instrument scientist
    once per cycle.
    """

    def verify(self, job_request: JobRequest) -> None:
        job_request.additional_values["wbvan"] = self._value
