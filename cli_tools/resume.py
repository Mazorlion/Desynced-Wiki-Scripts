from dataclasses import asdict, dataclass
import json
from pathlib import Path

from typing import Any, TypeAlias

from util.logger import get_logger

logger = get_logger()


@dataclass
class Resumable:
    id: str
    obj: Any  # Any way to use type safety later?


ResumableId: TypeAlias = str


@dataclass
class ResumeData:
    last_processed: str = ""  # can be whatever
    total_processed: int = 0  # minimal consistency check


class ResumeHelper:
    _resume_data: ResumeData
    _resume_file_path: Path

    def __init__(self, resume_file_path: Path, resume: bool):
        self._resume_file_path = resume_file_path
        self._resume_data = self._init_resume_data(resume)

    def init_resume_index(self, to_process: list[Resumable]) -> int:
        """
        Looks in the list at the saved totalProcessed index and checks if the text there matches our last_processed.
        If so, we can return the index, else, warn and reset resume at 0.

        Returns at which index to start
        """

        if self._resume_data.total_processed > 0:
            last_processed_index = self._resume_data.total_processed - 1
            if self._resume_data.total_processed == len(to_process):
                logger.info("Resume found last run finished execution. Starting over.")
            elif last_processed_index >= len(to_process):
                logger.warning(
                    "Resume mismatch: last_processed_index is bigger than our dataset. Reseting resume to 0."
                )
            elif (
                to_process[last_processed_index].id == self._resume_data.last_processed
            ):
                logger.info(
                    f"Resuming at index {last_processed_index} ({self._resume_data.last_processed})"
                )
                self._resume_data = ResumeData(
                    to_process[last_processed_index].id,
                    self._resume_data.total_processed,
                )
                return last_processed_index + 1  # start on the next one
            else:
                logger.warning(
                    f"Resume mismatch: expected '{self._resume_data.last_processed}' at index {last_processed_index}, "
                    f"but found '{to_process[last_processed_index]}'. Resetting resume to 0."
                )
                # Reset resume if mismatch or out of bounds
        else:
            logger.info("No valid resume index found, starting from 0.")

        self._resume_data = ResumeData()
        self._write_resume_file(self._resume_data)
        return 0

    def update_progress(self, finished: str):
        """Update resume file with last file and increase totalProcessed by 1, then write it immediately."""
        self._resume_data.last_processed = finished
        self._resume_data.total_processed += 1
        self._write_resume_file(self._resume_data)

    def _write_resume_file(self, resume: ResumeData):
        """Write resume data to file. Raise on error."""
        try:
            with open(self._resume_file_path, "w", encoding="utf-8") as f:
                json.dump(asdict(resume), f, indent=2)
            # logger.debug(f"Resume file updated: {self._resume_file_path}")
        except Exception as e:
            logger.error(f"Failed to write resume file: {e}")
            raise

    def _init_resume_data(self, resume: bool) -> ResumeData:
        if self._resume_file_path.exists() and resume:
            try:
                with open(self._resume_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return ResumeData(**data)
                logger.debug(f"Loaded resume file: {self._resume_file_path}")
            except FileNotFoundError as e:
                logger.warning(f"Resume file not found, starting fresh: {e}")
                return ResumeData()
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in resume file, starting fresh: {e}")
                return ResumeData()
            except TypeError as e:
                logger.warning(f"Invalid data in resume file, starting fresh: {e}")
                return ResumeData()
        else:
            if not resume:
                logger.debug(
                    f"Resuming not requested, resume file ({self._resume_file_path}) will be overwritten"
                )
            return ResumeData()
