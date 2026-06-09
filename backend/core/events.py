"""
Event emitter for SSE streaming.
Backend code calls emit(event_type, payload) anywhere in the workflow.
Frontend consumes via /api/chat/stream.
"""
import asyncio
import time
import json
import uuid
from typing import Optional, Dict, Any, AsyncIterator
from dataclasses import dataclass, field, asdict


@dataclass
class SwarmEvent:
    """A single event in the swarm's stream."""
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    agent_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_sse(self) -> str:
        """Format as Server-Sent Event."""
        data = json.dumps({
            "type": self.event_type,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            **self.payload,
        })
        return f"event: {self.event_type}\ndata: {data}\n\n"


class EventBus:
    """
    Per-stream event bus. Each chat request creates one bus.
    Workflow code emits events; the SSE endpoint reads from the queue.
    """
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self._closed = False
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.get_event_loop()

    def emit(self, event_type: str, payload: Optional[Dict] = None, agent_id: Optional[str] = None):
        """Emit an event. Thread-safe wrapper."""
        if self._closed:
            return
        event = SwarmEvent(
            event_type=event_type,
            payload=payload or {},
            agent_id=agent_id,
        )
        
        def _put():
            try:
                self.queue.put_nowait(event)
            except asyncio.QueueFull:
                pass  # drop event if queue overflows

        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(_put)
        else:
            _put()

    async def stream(self) -> AsyncIterator[str]:
        """Async generator yielding SSE-formatted events."""
        event_seq = 0
        while not self._closed:
            try:
                event = await asyncio.wait_for(self.queue.get(), timeout=30.0)
                event_seq += 1
                
                sse_data = event.to_sse()
                
                payload_keys = list(event.payload.keys())
                ans_len = len(event.payload.get("answer", "")) if event.payload.get("answer") else None
                dec_len = len(event.payload.get("decision", "")) if event.payload.get("decision") else None
                workflow_name = event.payload.get("workflow", "")
                
                logger.info(
                    f"[DIAGNOSTIC EVENT YIELD] seq={event_seq} | type={event.event_type} | "
                    f"workflow={workflow_name} | keys={payload_keys} | "
                    f"answer_len={ans_len} | decision_len={dec_len} | "
                    f"serialized_len={len(sse_data)}"
                )
                
                yield sse_data
                if event.event_type in ("error", "stream.end"):
                    break
            except asyncio.TimeoutError:
                # Heartbeat to keep connection alive
                yield ": keepalive\n\n"

    def close(self):
        self._closed = True


# Global registry of active streams (one per request_id)
_active_buses: Dict[str, EventBus] = {}


def create_bus(request_id: str) -> EventBus:
    """Create a new event bus for a request."""
    bus = EventBus()
    _active_buses[request_id] = bus
    return bus


def get_bus(request_id: str) -> Optional[EventBus]:
    """Get an existing bus by request_id."""
    return _active_buses.get(request_id)


def remove_bus(request_id: str):
    """Clean up after stream completes."""
    if request_id in _active_buses:
        _active_buses[request_id].close()
        del _active_buses[request_id]
