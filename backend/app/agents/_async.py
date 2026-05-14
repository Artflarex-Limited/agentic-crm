"""
Async utilities for Celery tasks that need to run async code in sync worker context.
"""
import asyncio
from functools import wraps


def run_async(coro):
    """
    Execute an async coroutine from a synchronous Celery task.
    Reuses running loop if available, otherwise creates new event loop.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def async_task(task_name: str = None, bind: bool = False, max_retries: int = 3):
    """
    Decorator factory for Celery tasks that wrap async operations.

    Usage:
        @async_task("agents.example.task_name")
        async def my_task(arg1, arg2):
            # async code here
            pass

        # Or with bind:
        @async_task(bind=True)
        def bound_task(self, arg1):
            pass
    """
    def decorator(func):
        from app.celery_app import celery_app

        @celery_app.task(name=task_name, bind=bind, max_retries=max_retries)
        @wraps(func)
        def wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                return run_async(func(*args, **kwargs))
            return func(*args, **kwargs)

        if task_name:
            wrapper.name = task_name

        return wrapper
    return decorator
