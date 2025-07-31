from dataclasses import asdict, dataclass
import json
from pathlib import Path

import logging
from typing import Any, TypeAlias

logger = logging.getLogger()


@dataclass
class Resumable:
    id: str
    obj: Any  # Any way to use type safety later?


ResumableId: TypeAlias = str


@dataclass
class ResumeData:
    lastProcessed: str = ""  # can be whatever
    totalProcessed: int = 0  # minimal consistency check


class ResumeHelper:
    _resume_data: ResumeData
    _resume_file_path: Path

    def __init__(self, resume_file_path: Path, restart: bool):
        self._resume_file_path = resume_file_path
        self._resume_data = self._init_resume_data(restart)

    def init_resume_index(self, to_process: list[Resumable]) -> int:
        """
        Looks in the list at the saved totalProcessed index and checks if the text there matches our lastProcessed.
        If so, we can return the index, else, warn and reset resume at 0.

        Returns at which index to start
        """

        if self._resume_data.totalProcessed > 0:
            lastProcessedIndex = self._resume_data.totalProcessed - 1
            if self._resume_data.totalProcessed == len(to_process):
                logger.info(f"Resume found last run finished execution. Starting over.")
            elif lastProcessedIndex >= len(to_process):
                logger.warning(
                    f"Resume mismatch: lastProcessedIndex is bigger than our dataset. Resetting resume to 0."
                )
            elif to_process[lastProcessedIndex].id == self._resume_data.lastProcessed:
                logger.info(
                    f"Resuming at index {lastProcessedIndex} ({self._resume_data.lastProcessed})"
                )
                self._resume_data = ResumeData(
                    to_process[lastProcessedIndex].id, self._resume_data.totalProcessed
                )
                return lastProcessedIndex + 1  # start on the next one
            else:
                logger.warning(
                    f"Resume mismatch: expected '{self._resume_data.lastProcessed}' at index {lastProcessedIndex}, "
                    f"but found '{to_process[lastProcessedIndex]}'. Resetting resume to 0."
                )
                # Reset resume if mismatch or out of bounds
        else:
            logger.info("No valid resume index found, starting from 0.")

        self._resume_data = ResumeData()
        self._write_resume_file(self._resume_data)
        return 0

    def update_progress(self, finished: str):
        """Update resume file with last file and increase totalProcessed by 1, then write it immediately."""
        self._resume_data.lastProcessed = finished
        self._resume_data.totalProcessed += 1
        self._write_resume_file(self._resume_data)

    def _write_resume_file(self, resume: ResumeData):
        """Write resume data to file. Raise on error."""
        try:
            with open(self._resume_file_path, "w", encoding="utf-8") as f:
                json.dump(asdict(resume), f, indent=2)
            logger.debug(f"Resume file updated: {self._resume_file_path}")
        except Exception as e:
            logger.error(f"Failed to write resume file: {e}")
            raise

    def _init_resume_data(self, restart: bool) -> ResumeData:
        if self._resume_file_path.exists() and not restart:
            try:
                with open(self._resume_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return ResumeData(**data)
                logger.info(f"Loaded resume file: {self._resume_file_path}")
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
            if self._resume_file_path.exists():
                if restart:
                    logger.info(
                        f"Restart requested, ignoring and overwriting existing resume file: {self._resume_file_path}"
                    )
            return ResumeData()
