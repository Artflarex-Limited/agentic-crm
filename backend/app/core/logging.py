"""
Shared logging and distributed tracing utilities.
Standardizes logging format across all microservices.
"""
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

from app.core.config import get_settings

settings = get_settings()

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
span_id_var: ContextVar[str] = ContextVar("span_id", default="")
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def generate_trace_id() -> str:
    return uuid.uuid4().hex[:16]


def generate_span_id() -> str:
    return uuid.uuid4().hex[:8]


def generate_correlation_id() -> str:
    return f"run-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"


class StructuredFormatter(logging.Formatter):
    """JSON structured logging formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        if hasattr(record, "span_id"):
            log_data["span_id"] = record.span_id
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "levelname",
                "levelno", "pathname", "process", "processName", "thread",
                "threadName", "exc_info", "exc_text", "stack_info",
                "trace_id", "span_id", "correlation_id",
            ):
                if not key.startswith("_"):
                    log_data[key] = value

        import json
        return json.dumps(log_data)


def setup_logging(
    name: str = "agentic_crm",
    level: int = logging.INFO,
    json_format: bool = False,
) -> logging.Logger:
    """Configure application logging."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if json_format:
        handler.setFormatter(StructuredFormatter())
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger


def setup_tracing(service_name: str = "agentic-crm") -> trace.Tracer:
    """Configure OpenTelemetry distributed tracing."""
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
    })

    provider = TracerProvider(resource=resource)

    if settings.otel_exporter_endpoint:
        try:
            exporter = OTLPSpanExporter(
                endpoint=settings.otel_exporter_endpoint,
                insecure=True,
            )
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)
        except Exception:
            pass

    trace.set_tracer_provider(provider)
    return trace.get_tracer(__name__)


class TracingContext:
    """Context manager for distributed tracing."""

    def __init__(
        self,
        tracer: trace.Tracer,
        operation_name: str,
        attributes: dict[str, Any] | None = None,
    ):
        self.tracer = tracer
        self.operation_name = operation_name
        self.attributes = attributes or {}
        self.span = None

    def __enter__(self):
        self.span = self.tracer.start_span(self.operation_name)
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)

        trace_id = trace.get_current_span().get_span_context().trace_id[:16]
        span_id = trace.get_current_span().get_span_context().span_id[:8]

        trace_id_var.set(trace_id)
        span_id_var.set(span_id)

        return self

    def __exit__(self, *args):
        if args[0] is not None:
            self.span.set_status(Status(StatusCode.ERROR, str(args[0])))
        self.span.end()
        trace_id_var.set("")
        span_id_var.set("")

    def set_attribute(self, key: str, value: Any):
        if self.span:
            self.span.set_attribute(key, value)

    def add_event(self, name: str, attributes: dict[str, Any] | None = None):
        if self.span:
            self.span.add_event(name, attributes=attributes)


def traced(
    operation_name: str | None = None,
    attributes: dict[str, Any] | None = None,
):
    """Decorator for automatic tracing of functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            name = operation_name or f"{func.__module__}.{func.__name__}"
            with TracingContext(tracer, name, attributes) as ctx:
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    ctx.span.set_status(Status(StatusCode.ERROR, str(e)))
                    ctx.span.record_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            name = operation_name or f"{func.__module__}.{func.__name__}"
            with TracingContext(tracer, name, attributes) as ctx:
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    ctx.span.set_status(Status(StatusCode.ERROR, str(e)))
                    ctx.span.record_exception(e)
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def get_trace_id() -> str:
    return trace_id_var.get("")


def get_span_id() -> str:
    return span_id_var.get("")


def get_correlation_id() -> str:
    return correlation_id_var.get("")


def set_correlation_id(corr_id: str):
    correlation_id_var.set(corr_id)


class LogContext:
    """Add context fields to log records."""

    def __init__(self, **kwargs):
        self.context = kwargs

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def set(self, **kwargs):
        self.context.update(kwargs)

    def clear(self):
        self.context.clear()


def log_with_context(logger: logging.Logger, level: int, message: str, **kwargs):
    """Log with additional context fields."""
    extra = {"context": kwargs}
    logger.log(level, message, extra=extra)


logger = setup_logging()