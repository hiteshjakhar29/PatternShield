"""
PatternShield — Task Queue Abstraction

Thin wrapper that runs tasks synchronously now but is structured so that
swapping in Celery or RQ later only requires replacing the `submit` function
body — no changes to callers.

Design rationale (for interviews):
  Batch analysis on large pages can take 2–5 seconds when LLM is enabled.
  The current architecture runs this synchronously in the Flask request cycle.
  To scale to production, we would:
    1. Push each batch job to a Redis queue via Celery
    2. Return a job_id immediately (202 Accepted)
    3. Poll GET /jobs/<job_id> or use WebSocket push for result delivery
  This module provides the interface contract so no route code changes
  are needed when that migration happens.

Usage (current — sync):
    result = submit(my_func, arg1, arg2, kw=val)

Usage (future — async with Celery):
    job_id = submit(my_func, arg1, arg2, kw=val)
    # caller polls /jobs/<job_id>
"""
import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


def submit(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """
    Submit a task for execution.

    Currently synchronous. Future: returns a job ID when Celery is wired in.
    """
    t0 = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = round((time.time() - t0) * 1000, 1)
        logger.debug(f"task {func.__name__} completed in {elapsed}ms")
        return result
    except Exception as e:
        logger.error(f"task {func.__name__} failed: {e}", exc_info=True)
        raise


# ── Future Celery integration stub ────────────────────────────────────────────
# Uncomment and configure when ready to migrate to async workers:
#
# from celery import Celery
# _celery = Celery("patternshield", broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"))
#
# def submit_async(func, *args, **kwargs):
#     """Submit a task to Celery and return a job ID."""
#     task = _celery.send_task(func.__name__, args=args, kwargs=kwargs)
#     return task.id
#
# def get_result(job_id: str):
#     """Poll Celery for task result."""
#     from celery.result import AsyncResult
#     res = AsyncResult(job_id, app=_celery)
#     return {"status": res.status, "result": res.result if res.ready() else None}
