"""
Simple synchronous EventBus implementation for Phase 3.5.4
"""
from __future__ import annotations
from typing import Callable, Dict, List
import threading


class EventBus:
    def __init__(self):
        # map event_type -> list of handlers
        self._handlers: Dict[str, List[Callable[[dict], None]]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, handler: Callable[[dict], None]) -> None:
        """Register a handler for an event type."""
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)

    def publish(self, event: dict) -> None:
        """Publish an event (synchronous). Event must be a dict with 'type' key."""
        if not isinstance(event, dict):
            return
        event_type = event.get("type")
        if not event_type:
            return
        # snapshot handlers to avoid race conditions if handlers modify subscriptions
        with self._lock:
            handlers = list(self._handlers.get(event_type, []))
        for h in handlers:
            try:
                h(event)
            except Exception:
                # swallow handler exceptions to keep publisher resilient
                continue
