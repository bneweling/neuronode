"""
AI Services Monitor

Produktionsreifes Monitoring System für AI Services.
Überwacht Performance, Kosten, Latenz und Qualität in Echtzeit.
"""

import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import asyncio
from contextlib import asynccontextmanager, contextmanager

# Lokale Imports
from ..config.settings import Settings
from .metrics import MetricsCollector

logger = logging.getLogger(__name__)


@dataclass
class APICall:
    """Represents a single API call"""
    service_name: str
    timestamp: datetime
    duration_ms: float
    tokens_used: int
    cost_cents: float
    success: bool
    error_message: Optional[str] = None
    cache_hit: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ServiceStats:
    """Aggregated statistics for a service"""
    service_name: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    total_duration_ms: float
    total_tokens: int
    total_cost_cents: float
    avg_duration_ms: float
    cache_hit_rate: float
    error_rate: float
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class SystemHealth:
    """Overall system health metrics"""
    timestamp: datetime
    active_services: int
    total_calls_last_hour: int
    avg_response_time_ms: float
    error_rate_last_hour: float
    estimated_hourly_cost_cents: float
    cache_efficiency: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }


class AIServicesMonitor:
    """
    Real-time monitoring for AI Services
    """
    
    def __init__(self, settings: Settings, monitoring_dir: Path):
        self.settings = settings
        self.monitoring_dir = monitoring_dir
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage for recent data (last 24 hours)
        self.api_calls: deque = deque(maxlen=10000)  # Keep last 10k calls
        self.service_stats: Dict[str, ServiceStats] = {}
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        # Cost mapping (cents per 1k tokens)
        self.cost_per_1k_tokens = {
            'gemini-1.5-flash-latest': 0.075,  # $0.075 per 1K input tokens
            'gemini-1.5-pro-latest': 1.25,    # $1.25 per 1K input tokens
            'gemini-1.0-pro': 0.5             # $0.50 per 1K input tokens
        }
        
        # Metrics collector
        self.metrics = MetricsCollector()
        
        logger.info(f"AIServicesMonitor initialisiert - Monitoring Dir: {monitoring_dir}")
    
    def estimate_cost(self, model_name: str, tokens_used: int) -> float:
        """Estimate cost in cents for API call"""
        cost_per_1k = self.cost_per_1k_tokens.get(model_name, 0.5)  # Default fallback
        return (tokens_used / 1000.0) * cost_per_1k
    
    def record_api_call(self, service_name: str, model_name: str, 
                       duration_ms: float, tokens_used: int, 
                       success: bool, cache_hit: bool = False,
                       error_message: Optional[str] = None) -> None:
        """Record an API call for monitoring"""
        
        with self._lock:
            # Calculate cost
            cost_cents = self.estimate_cost(model_name, tokens_used)
            
            # Create API call record
            api_call = APICall(
                service_name=service_name,
                timestamp=datetime.now(),
                duration_ms=duration_ms,
                tokens_used=tokens_used,
                cost_cents=cost_cents,
                success=success,
                cache_hit=cache_hit,
                error_message=error_message
            )
            
            # Add to recent calls
            self.api_calls.append(api_call)
            
            # Update service statistics
            self._update_service_stats(api_call)
            
            # Update metrics
            self.metrics.record_api_call(
                service_name, duration_ms, tokens_used, 
                cost_cents, success, cache_hit
            )
    
    def _update_service_stats(self, api_call: APICall) -> None:
        """Update aggregated service statistics"""
        service_name = api_call.service_name
        
        if service_name not in self.service_stats:
            self.service_stats[service_name] = ServiceStats(
                service_name=service_name,
                total_calls=0,
                successful_calls=0,
                failed_calls=0,
                total_duration_ms=0.0,
                total_tokens=0,
                total_cost_cents=0.0,
                avg_duration_ms=0.0,
                cache_hit_rate=0.0,
                error_rate=0.0,
                last_updated=datetime.now()
            )
        
        stats = self.service_stats[service_name]
        
        # Update counters
        stats.total_calls += 1
        stats.total_duration_ms += api_call.duration_ms
        stats.total_tokens += api_call.tokens_used
        stats.total_cost_cents += api_call.cost_cents
        
        if api_call.success:
            stats.successful_calls += 1
        else:
            stats.failed_calls += 1
        
        # Recalculate derived metrics
        stats.avg_duration_ms = stats.total_duration_ms / stats.total_calls
        stats.error_rate = stats.failed_calls / stats.total_calls
        
        # Calculate cache hit rate (from recent calls only)
        recent_calls = [call for call in self.api_calls 
                       if call.service_name == service_name]
        cache_hits = sum(1 for call in recent_calls if call.cache_hit)
        stats.cache_hit_rate = cache_hits / len(recent_calls) if recent_calls else 0.0
        
        stats.last_updated = datetime.now()
    
    @contextmanager
    def track_api_call(self, service_name: str, model_name: str):
        """Context manager to automatically track API calls"""
        start_time = time.time()
        tokens_used = 0
        success = False
        error_message = None
        cache_hit = False
        
        try:
            yield {
                'set_tokens': lambda t: setattr(self, '_temp_tokens', t),
                'set_cache_hit': lambda c: setattr(self, '_temp_cache_hit', c)
            }
            success = True
            tokens_used = getattr(self, '_temp_tokens', 0)
            cache_hit = getattr(self, '_temp_cache_hit', False)
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"API Call Fehler in {service_name}: {e}")
            raise
        
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_api_call(
                service_name, model_name, duration_ms, 
                tokens_used, success, cache_hit, error_message
            )
            
            # Cleanup temp attributes
            if hasattr(self, '_temp_tokens'):
                delattr(self, '_temp_tokens')
            if hasattr(self, '_temp_cache_hit'):
                delattr(self, '_temp_cache_hit')
    
    def get_service_stats(self, service_name: Optional[str] = None) -> Dict[str, ServiceStats]:
        """Get service statistics"""
        with self._lock:
            if service_name:
                return {service_name: self.service_stats.get(service_name)}
            return self.service_stats.copy()
    
    def get_system_health(self) -> SystemHealth:
        """Get current system health metrics"""
        with self._lock:
            now = datetime.now()
            one_hour_ago = now - timedelta(hours=1)
            
            # Filter recent calls (last hour)
            recent_calls = [call for call in self.api_calls 
                           if call.timestamp >= one_hour_ago]
            
            # Calculate metrics
            total_calls_last_hour = len(recent_calls)
            successful_calls = sum(1 for call in recent_calls if call.success)
            failed_calls = total_calls_last_hour - successful_calls
            
            avg_response_time = (
                sum(call.duration_ms for call in recent_calls) / total_calls_last_hour
                if total_calls_last_hour > 0 else 0.0
            )
            
            error_rate = failed_calls / total_calls_last_hour if total_calls_last_hour > 0 else 0.0
            
            # Estimate hourly cost
            cost_last_hour = sum(call.cost_cents for call in recent_calls)
            estimated_hourly_cost = cost_last_hour  # Already for the last hour
            
            # Cache efficiency
            cache_hits = sum(1 for call in recent_calls if call.cache_hit)
            cache_efficiency = cache_hits / total_calls_last_hour if total_calls_last_hour > 0 else 0.0
            
            return SystemHealth(
                timestamp=now,
                active_services=len(self.service_stats),
                total_calls_last_hour=total_calls_last_hour,
                avg_response_time_ms=avg_response_time,
                error_rate_last_hour=error_rate,
                estimated_hourly_cost_cents=estimated_hourly_cost,
                cache_efficiency=cache_efficiency
            )
    
    def get_recent_calls(self, limit: int = 100, service_name: Optional[str] = None) -> List[APICall]:
        """Get recent API calls"""
        with self._lock:
            calls = list(self.api_calls)
            
            if service_name:
                calls = [call for call in calls if call.service_name == service_name]
            
            # Return most recent first
            return sorted(calls, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_cost_breakdown(self, hours: int = 24) -> Dict[str, float]:
        """Get cost breakdown by service for the last N hours"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_calls = [call for call in self.api_calls 
                           if call.timestamp >= cutoff_time]
            
            cost_by_service = defaultdict(float)
            for call in recent_calls:
                cost_by_service[call.service_name] += call.cost_cents
            
            return dict(cost_by_service)
    
    def save_monitoring_report(self) -> Path:
        """Save comprehensive monitoring report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.monitoring_dir / f"monitoring_report_{timestamp}.json"
        
        with self._lock:
            # Gather all data
            report = {
                "timestamp": datetime.now().isoformat(),
                "system_health": self.get_system_health().to_dict(),
                "service_stats": {
                    name: stats.to_dict() 
                    for name, stats in self.service_stats.items()
                },
                "recent_calls": [
                    call.to_dict() for call in self.get_recent_calls(500)
                ],
                "cost_breakdown_24h": self.get_cost_breakdown(24),
                "cost_breakdown_1h": self.get_cost_breakdown(1)
            }
        
        # Save to file
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Monitoring Report gespeichert: {report_path}")
        return report_path
    
    def cleanup_old_data(self, days_to_keep: int = 7) -> None:
        """Clean up old monitoring data"""
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        with self._lock:
            # Remove old API calls (deque automatically limits size, but let's be explicit)
            self.api_calls = deque(
                [call for call in self.api_calls if call.timestamp >= cutoff_time],
                maxlen=self.api_calls.maxlen
            )
        
        # Clean up old report files
        if self.monitoring_dir.exists():
            for report_file in self.monitoring_dir.glob("monitoring_report_*.json"):
                try:
                    # Extract timestamp from filename
                    timestamp_str = report_file.stem.split('_')[-2] + '_' + report_file.stem.split('_')[-1]
                    file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if file_time < cutoff_time:
                        report_file.unlink()
                        logger.debug(f"Alte Monitoring-Datei gelöscht: {report_file}")
                        
                except (ValueError, IndexError):
                    # Skip files that don't match expected format
                    continue
        
        logger.info(f"Monitoring Daten bereinigt (behalten: {days_to_keep} Tage)")
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_calls = [call for call in self.api_calls 
                       if call.timestamp >= cutoff_time]
        
        if not recent_calls:
            return {
                "period_hours": hours,
                "total_calls": 0,
                "avg_response_time_ms": 0,
                "error_rate": 0,
                "total_cost_cents": 0,
                "cache_hit_rate": 0
            }
        
        successful_calls = [call for call in recent_calls if call.success]
        
        return {
            "period_hours": hours,
            "total_calls": len(recent_calls),
            "successful_calls": len(successful_calls),
            "failed_calls": len(recent_calls) - len(successful_calls),
            "avg_response_time_ms": sum(call.duration_ms for call in recent_calls) / len(recent_calls),
            "error_rate": (len(recent_calls) - len(successful_calls)) / len(recent_calls),
            "total_cost_cents": sum(call.cost_cents for call in recent_calls),
            "cache_hit_rate": sum(1 for call in recent_calls if call.cache_hit) / len(recent_calls),
            "total_tokens": sum(call.tokens_used for call in recent_calls)
        }


# Singleton instance for global access
_monitor_instance: Optional[AIServicesMonitor] = None


def get_monitor() -> Optional[AIServicesMonitor]:
    """Get the global monitor instance"""
    return _monitor_instance


def initialize_monitor(settings: Settings, monitoring_dir: Path) -> AIServicesMonitor:
    """Initialize the global monitor instance"""
    global _monitor_instance
    _monitor_instance = AIServicesMonitor(settings, monitoring_dir)
    return _monitor_instance


def track_api_call(service_name: str, model_name: str):
    """Convenience function to track API calls"""
    monitor = get_monitor()
    if monitor:
        return monitor.track_api_call(service_name, model_name)
    else:
        # Fallback context manager that does nothing
        from contextlib import nullcontext
        return nullcontext({'set_tokens': lambda t: None, 'set_cache_hit': lambda c: None}) 