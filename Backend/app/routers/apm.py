import time
import os
import psutil
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db, engine
from app.core.apm_middleware import apm_collector

router = APIRouter(prefix="/apm", tags=["Application Performance Monitoring"])

@router.get("/metrics")
def get_apm_metrics():
    """Retrieve real-time APM telemetry metrics, traces, and system resource status."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    cpu_pct = process.cpu_percent(interval=None)

    summary = apm_collector.get_summary()
    summary["system"] = {
        "cpu_usage_pct": round(cpu_pct, 2),
        "memory_rss_mb": round(mem_info.rss / (1024 * 1024), 2),
        "memory_vsz_mb": round(mem_info.vms / (1024 * 1024), 2),
        "open_fds": len(process.open_files()) if hasattr(process, "open_files") else None,
        "threads": process.num_threads() if hasattr(process, "num_threads") else None,
    }
    return summary

@router.get("/db-health")
def check_db_health(db: Session = Depends(get_db)):
    """Safe, non-destructive database health, ping, and connection pool check."""
    start_time = time.time()
    try:
        res = db.execute(text("SELECT 1")).scalar()
        latency_ms = (time.time() - start_time) * 1000
        
        db_type = engine.name
        return {
            "status": "HEALTHY",
            "db_type": db_type,
            "ping_result": res,
            "latency_ms": round(latency_ms, 2),
            "connection_status": "CONNECTED"
        }
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return {
            "status": "UNHEALTHY",
            "db_type": engine.name,
            "error": str(e),
            "latency_ms": round(latency_ms, 2),
            "connection_status": "FAILED"
        }
