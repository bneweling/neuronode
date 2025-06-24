from prometheus_client import Counter, Histogram, Gauge, generate_latest
from functools import wraps
import time

# Metrics
query_counter = Counter('ki_queries_total', 'Total number of queries processed')
query_duration = Histogram('ki_query_duration_seconds', 'Query processing duration')
document_counter = Counter('ki_documents_processed_total', 'Total documents processed')
active_connections = Gauge('ki_websocket_connections', 'Active WebSocket connections')
cache_hits = Counter('ki_cache_hits_total', 'Cache hit count')
cache_misses = Counter('ki_cache_misses_total', 'Cache miss count')

def track_query_metrics(func):
    """Decorator to track query metrics"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        query_counter.inc()
        
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            query_duration.observe(duration)
    
    return wrapper

def get_metrics():
    """Get Prometheus metrics"""
    return generate_latest()