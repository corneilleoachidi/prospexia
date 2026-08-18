"""Exécution du pipeline dans un thread Qt, avec signaux vers l'interface."""
from __future__ import annotations

import asyncio

from PySide6.QtCore import QThread, Signal

from prospexia.config import Settings
from prospexia.core.models import SearchRequest
from prospexia.core.pipeline import Pipeline, PipelineCancelled


class PipelineWorker(QThread):
    progress = Signal(object)     # ProgressEvent
    prospect = Signal(object)     # Prospect
    finished_ok = Signal(list)    # list[Prospect]
    cancelled = Signal()
    failed = Signal(str)

    def __init__(self, settings: Settings, request: SearchRequest, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.request = request
        self._pipeline: Pipeline | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._pipeline = Pipeline(self.settings,
                                  on_progress=lambda e: self.progress.emit(e),
                                  on_prospect=lambda p: self.prospect.emit(p))
        try:
            results = self._loop.run_until_complete(self._pipeline.run(self.request))
            self.finished_ok.emit(results)
        except PipelineCancelled:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"{type(exc).__name__}: {exc}")
        finally:
            self._loop.close()

    def cancel(self) -> None:
        if self._pipeline and self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._pipeline.cancel)
