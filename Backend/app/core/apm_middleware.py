import time
import uuid
import threading
from typing import List, Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
import psutil

class APMCollector:
    """In-memory thread-safe APM metrics collector and tracer."""
    def __init__(self, max_traces: int = 2000):
        self.max_traces = max_traces
        self.traces: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def record_trace(
        self,
        trace_id: str,
        method: str,
        path: str,
        start_time: float,
        end_time: float,
        duration_ms: float,
        status_code: int,
        exception: Optional[str] = None
    ):
        trace_entry = {
            "trace_id": trace_id,
            "method": method,
            "path": path,
            "start_time": start_time,
            "end_time": end_time,
            "duration_ms": round(duration_ms, 2),
            "status_code": status_code,
            "exception": exception,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))
        }

        with self._lock:
            self.traces.append(trace_entry)
            if len(self.traces) > self.max_traces:
                self.traces.pop(0)

            if status_code >= 400 or exception:
                error_entry = {
                    "trace_id": trace_id,
                    "method": method,
                    "endpoint": path,
                    "status_code": status_code,
                    "error_type": "HTTPError" if status_code >= 400 else "Exception",
                    "message": exception or f"HTTP {status_code} response",
                    "severity": "HIGH" if status_code >= 500 or exception else "MEDIUM",
                    "timestamp": trace_entry["timestamp"]
                }
                self.errors.append(error_entry)
                if len(self.errors) > 500:
                    self.errors.pop(0)

    def get_summary(self) -> Dict[str, Any]:
        """Calculates server-side aggregated metrics."""
        with self._lock:
            total = len(self.traces)
            if total == 0:
                return {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "avg_latency_ms": 0.0,
                    "recent_errors": [],
                    "recent_traces": []
                }
            successes = sum(1 for t in self.traces if t["status_code"] < 400 and not t["exception"])
            failures = total - successes
            durations = [t["duration_ms"] for t in self.traces]
            avg_lat = sum(durations) / len(durations) if durations else 0.0

            return {
                "total_requests": total,
                "successful_requests": successes,
                "failed_requests": failures,
                "success_rate_pct": round((successes / total) * 100.0, 2),
                "error_rate_pct": round((failures / total) * 100.0, 2),
                "avg_latency_ms": round(avg_lat, 2),
                "recent_errors": list(self.errors[-20:]),
                "recent_traces": list(self.traces[-50:])
            }

# Global singleton collector
apm_collector = APMCollector()


class APMMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware for request tracing, latency tracking, and error capturing."""
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        trace_id = request.headers.get("X-Trace-ID") or f"tr-{uuid.uuid4().hex[:12]}"
        request.state.trace_id = trace_id

        start_time = time.time()
        status_code = 500
        exception_msg = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Response-Time-ms"] = f"{duration_ms:.2f}"

            apm_collector.record_trace(
                trace_id=trace_id,
                method=request.method,
                path=request.url.path,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                status_code=status_code,
                exception=None
            )
            return response
        except Exception as exc:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            exception_msg = f"{type(exc).__name__}: {str(exc)}"
            
            apm_collector.record_trace(
                trace_id=trace_id,
                method=request.method,
                path=request.url.path,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                status_code=500,
                exception=exception_msg
            )
            raise exc
