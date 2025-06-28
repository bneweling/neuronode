"""
Simple Metrics Collector

Lightweight metrics collection without external dependencies.
"""

from functools import wraps
import time
from typing import Dict, Any
from collections import defaultdict, deque


class SimpleCounter:
    """Simple counter implementation"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.value = 0
    
    def inc(self, amount: int = 1):
        self.value += amount


class SimpleHistogram:
    """Simple histogram implementation"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.observations = deque(maxlen=1000)  # Keep last 1000 observations
    
    def observe(self, value: float):
        self.observations.append(value)
    
    def get_stats(self) -> Dict[str, float]:
        if not self.observations:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0}
        
        observations = list(self.observations)
        return {
            "count": len(observations),
            "sum": sum(observations),
            "avg": sum(observations) / len(observations),
            "min": min(observations),
            "max": max(observations)
        }


class SimpleGauge:
    """Simple gauge implementation"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.value = 0
    
    def set(self, value: float):
        self.value = value
    
    def inc(self, amount: float = 1):
        self.value += amount
    
    def dec(self, amount: float = 1):
        self.value -= amount


class MetricsCollector:
    """Simple metrics collector"""
    
    def __init__(self):
        # Initialize metrics
        self.api_call_counter = SimpleCounter('api_calls_total', 'Total API calls')
        self.api_duration = SimpleHistogram('api_call_duration_ms', 'API call duration in milliseconds')
        self.api_tokens = SimpleHistogram('api_tokens_used', 'Tokens used per API call')
        self.api_cost = SimpleHistogram('api_cost_cents', 'Cost per API call in cents')
        self.cache_hit_counter = SimpleCounter('cache_hits_total', 'Cache hits')
        self.cache_miss_counter = SimpleCounter('cache_misses_total', 'Cache misses')
        self.error_counter = SimpleCounter('errors_total', 'Total errors')
    
    def record_api_call(self, service_name: str, duration_ms: float, 
                       tokens_used: int, cost_cents: float, 
                       success: bool, cache_hit: bool):
        """Record an API call"""
        self.api_call_counter.inc()
        self.api_duration.observe(duration_ms)
        self.api_tokens.observe(tokens_used)
        self.api_cost.observe(cost_cents)
        
        if cache_hit:
            self.cache_hit_counter.inc()
        else:
            self.cache_miss_counter.inc()
        
        if not success:
            self.error_counter.inc()
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics as dictionary"""
        return {
            "api_calls": self.api_call_counter.value,
            "api_duration_stats": self.api_duration.get_stats(),
            "api_tokens_stats": self.api_tokens.get_stats(),
            "api_cost_stats": self.api_cost.get_stats(),
            "cache_hits": self.cache_hit_counter.value,
            "cache_misses": self.cache_miss_counter.value,
            "errors": self.error_counter.value,
            "cache_hit_rate": (
                self.cache_hit_counter.value / 
                (self.cache_hit_counter.value + self.cache_miss_counter.value)
                if (self.cache_hit_counter.value + self.cache_miss_counter.value) > 0 else 0
            )
        }


# Legacy compatibility
query_counter = SimpleCounter('ki_queries_total', 'Total number of queries processed')
query_duration = SimpleHistogram('ki_query_duration_seconds', 'Query processing duration')
document_counter = SimpleCounter('ki_documents_processed_total', 'Total documents processed')
active_connections = SimpleGauge('ki_websocket_connections', 'Active WebSocket connections')
cache_hits = SimpleCounter('ki_cache_hits_total', 'Cache hit count')
cache_misses = SimpleCounter('ki_cache_misses_total', 'Cache miss count')


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
    """Get metrics in simple format"""
    return {
        "queries_total": query_counter.value,
        "query_duration_stats": query_duration.get_stats(),
        "documents_processed": document_counter.value,
        "active_connections": active_connections.value,
        "cache_hits": cache_hits.value,
        "cache_misses": cache_misses.value
    }