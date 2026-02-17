"""
Monitoring Service
Collects and stores logs from edge servers for GenAI analysis
"""
import logging
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CDN Monitoring Service",
    description="Collects logs and metrics from edge servers",
    version="1.0.0"
)

# In-memory log storage (in production, use database)
logs_storage = []
MAX_LOGS = 10000

# Models
class EdgeLog(BaseModel):
    """Log entry from edge server"""
    request_id: Optional[str] = None
    timestamp: str
    client_ip: str
    request_path: str
    request_method: str
    cache_status: str
    edge_server: str
    ttl: int
    response_time_ms: Optional[float] = None
    status_code: int
    bytes_sent: Optional[int] = None

class MetricData(BaseModel):
    """Metric data from edge server"""
    edge_server: str
    metric_type: str
    value: float
    timestamp: str
    metadata: Optional[Dict] = None

# Endpoints

@app.get("/")
async def root():
    return {
        "service": "CDN Monitoring Service",
        "status": "running",
        "total_logs": len(logs_storage)
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/logs/ingest")
async def ingest_log(log: EdgeLog):
    """
    Ingest a log entry from an edge server
    This endpoint is called by edge servers after each request
    """
    # Generate request ID if not provided
    if not log.request_id:
        log.request_id = str(uuid.uuid4())
    
    # Add to storage
    log_dict = log.model_dump()
    logs_storage.append(log_dict)
    
    # Keep storage bounded
    if len(logs_storage) > MAX_LOGS:
        logs_storage.pop(0)
    
    logger.info(
        f"📝 Log ingested: {log.edge_server} | {log.request_path} | {log.cache_status}"
    )
    
    return {
        "status": "success",
        "request_id": log.request_id
    }

@app.post("/api/logs/batch")
async def ingest_logs_batch(logs: List[EdgeLog]):
    """
    Ingest multiple log entries at once (for efficiency)
    """
    ingested = 0
    
    for log in logs:
        if not log.request_id:
            log.request_id = str(uuid.uuid4())
        
        log_dict = log.model_dump()
        logs_storage.append(log_dict)
        ingested += 1
    
    # Keep storage bounded
    while len(logs_storage) > MAX_LOGS:
        logs_storage.pop(0)
    
    logger.info(f"📝 Batch ingested: {ingested} logs")
    
    return {
        "status": "success",
        "ingested": ingested
    }

@app.get("/api/logs")
async def get_logs(
    limit: int = 100,
    edge_server: Optional[str] = None,
    cache_status: Optional[str] = None
):
    """
    Retrieve logs (used by GenAI engine for analysis)
    """
    filtered_logs = logs_storage
    
    # Apply filters
    if edge_server:
        filtered_logs = [log for log in filtered_logs if log.get('edge_server') == edge_server]
    
    if cache_status:
        filtered_logs = [log for log in filtered_logs if log.get('cache_status') == cache_status]
    
    # Get most recent logs
    recent_logs = filtered_logs[-limit:] if len(filtered_logs) > limit else filtered_logs
    
    return {
        "total_logs": len(logs_storage),
        "filtered_logs": len(filtered_logs),
        "returned_logs": len(recent_logs),
        "logs": recent_logs
    }

@app.get("/api/logs/{request_id}")
async def get_log_by_id(request_id: str):
    """Get a specific log by request ID"""
    for log in reversed(logs_storage):
        if log.get('request_id') == request_id:
            return log
    
    return {"error": "Log not found"}, 404

@app.post("/api/metrics/ingest")
async def ingest_metric(metric: MetricData):
    """
    Ingest metric data from edge servers
    (cache hit rate, response time, etc.)
    """
    logger.info(
        f"📊 Metric: {metric.edge_server} | {metric.metric_type} = {metric.value}"
    )
    
    return {"status": "success"}

@app.get("/api/stats")
async def get_stats():
    """Get aggregated statistics"""
    if not logs_storage:
        return {
            "total_requests": 0,
            "cache_hit_rate": 0,
            "edge_servers": []
        }
    
    total_requests = len(logs_storage)
    cache_hits = sum(1 for log in logs_storage if log.get('cache_status') == 'HIT')
    cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
    
    # Edge server stats
    edge_stats = {}
    for log in logs_storage:
        edge = log.get('edge_server', 'unknown')
        if edge not in edge_stats:
            edge_stats[edge] = {'requests': 0, 'cache_hits': 0}
        
        edge_stats[edge]['requests'] += 1
        if log.get('cache_status') == 'HIT':
            edge_stats[edge]['cache_hits'] += 1
    
    return {
        "total_requests": total_requests,
        "cache_hits": cache_hits,
        "cache_misses": total_requests - cache_hits,
        "cache_hit_rate": f"{cache_hit_rate:.2f}%",
        "edge_servers": edge_stats
    }

@app.delete("/api/logs/clear")
async def clear_logs():
    """Clear all logs (for testing)"""
    logs_storage.clear()
    logger.info("🗑️ All logs cleared")
    return {"status": "success", "message": "All logs cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

