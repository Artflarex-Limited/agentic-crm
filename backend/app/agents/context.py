"""
Agent Context - Tracing, correlation IDs, and structured logging for AI agents.
"""
import logging
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any

from app.models.models import AgentRole

agent_run_id: ContextVar[str] = ContextVar("agent_run_id", default="")
agent_correlation_id: ContextVar[str] = ContextVar("agent_correlation_id", default="")
agent_role: ContextVar[str] = ContextVar("agent_role", default="")

logger = logging.getLogger(__name__)


def generate_run_id() -> str:
    return str(uuid.uuid4())[:16]


def generate_correlation_id() -> str:
    return f"run-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"


class AgentContext:
    def __init__(
        self,
        run_id: str | None = None,
        correlation_id: str | None = None,
        role: AgentRole | None = None,
    ):
        self.run_id = run_id or generate_run_id()
        self.correlation_id = correlation_id or generate_correlation_id()
        self.role = role
        self._token_run_id = agent_run_id.set(self.run_id)
        self._token_corr = agent_correlation_id.set(self.correlation_id)
        self._token_role = agent_role.set(role.value if role else "")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        agent_run_id.reset(self._token_run_id)
        agent_correlation_id.reset(self._token_corr)
        agent_role.reset(self._token_role)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "role": self.role.value if self.role else None,
        }


def get_current_run_id() -> str:
    return agent_run_id.get("")


def get_current_correlation_id() -> str:
    return agent_correlation_id.get("")


def get_current_role() -> str:
    return agent_role.get("")


class AgentTaskMixin:
    def log_info(self, message: str, **kwargs):
        ctx = {
            "run_id": get_current_run_id(),
            "correlation_id": get_current_correlation_id(),
            "task_name": getattr(self, "name", "unknown"),
        }
        ctx.update(kwargs)
        logger.info(f"[{ctx['run_id']}] {message}", extra=ctx)

    def log_error(self, message: str, **kwargs):
        ctx = {
            "run_id": get_current_run_id(),
            "correlation_id": get_current_correlation_id(),
            "task_name": getattr(self, "name", "unknown"),
        }
        ctx.update(kwargs)
        logger.error(f"[{ctx['run_id']}] {message}", extra=ctx)

    def log_warning(self, message: str, **kwargs):
        ctx = {
            "run_id": get_current_run_id(),
            "correlation_id": get_current_correlation_id(),
            "task_name": getattr(self, "name", "unknown"),
        }
        ctx.update(kwargs)
        logger.warning(f"[{ctx['run_id']}] {message}", extra=ctx)
