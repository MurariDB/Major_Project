"""
Performance monitoring utility for the Voice RAG Assistant
"""
import time
import psutil
import threading
import statistics
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class SystemMetrics:
    cpu_percent: float
    memory_percent: float
    memory_usage_mb: float
    active_threads: int
    response_time_ms: float
    gpu_available: bool = False
    gpu_memory_mb: float = 0.0

class PerformanceMonitor:
    """Monitors system performance and response times"""
    
    def __init__(self):
        self.is_monitoring = False
        self.monitor_thread = None
        self.stop_event = threading.Event()
        self.metrics_history: List[SystemMetrics] = []
        self.response_times: List[float] = []
        self.current_metrics: Optional[SystemMetrics] = None
        self._lock = threading.Lock()
        
    def start_monitoring(self, interval: float = 2.0):
        """Start the monitoring thread"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        print("[INFO] Performance monitoring started")

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.is_monitoring = False
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        print("[INFO] Performance monitoring stopped")

    def _monitor_loop(self, interval: float):
        """Internal loop to collect metrics"""
        while not self.stop_event.is_set():
            try:
                self._collect_metrics()
                time.sleep(interval)
            except Exception as e:
                print(f"[ERROR] Monitor loop failed: {e}")
                break

    def _collect_metrics(self):
        """Collect current system metrics"""
        try:
            # CPU & Memory
            cpu_pct = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            
            # GPU (if available)
            gpu_avail = False
            gpu_mem = 0.0
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_avail = True
                    gpu_mem = torch.cuda.memory_allocated() / 1024 / 1024
            except ImportError:
                pass

            avg_resp = statistics.mean(self.response_times[-10:]) if self.response_times else 0.0

            metrics = SystemMetrics(
                cpu_percent=cpu_pct,
                memory_percent=mem.percent,
                memory_usage_mb=mem.used / 1024 / 1024,
                active_threads=threading.active_count(),
                response_time_ms=avg_resp,
                gpu_available=gpu_avail,
                gpu_memory_mb=gpu_mem
            )

            with self._lock:
                self.current_metrics = metrics
                self.metrics_history.append(metrics)
                # Keep history manageable
                if len(self.metrics_history) > 3600:  # ~1 hour at 1s interval
                    self.metrics_history.pop(0)

        except Exception as e:
            # Fail silently to avoid crashing main app
            pass

    def record_response_time(self, start_time: float):
        """Record the time taken for a request"""
        duration_ms = (time.time() - start_time) * 1000
        with self._lock:
            self.response_times.append(duration_ms)
            if len(self.response_times) > 100:
                self.response_times.pop(0)

    def is_system_overloaded(self) -> bool:
        """Check if system resources are critically high"""
        if not self.current_metrics:
            return False
        return (self.current_metrics.cpu_percent > 90 or 
                self.current_metrics.memory_percent > 90)

    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get the latest metrics safely"""
        with self._lock:
            return self.current_metrics

    def get_recommendations(self) -> List[str]:
        """Get performance recommendations based on current state"""
        recs = []
        if not self.current_metrics:
            return recs
            
        if self.current_metrics.memory_percent > 85:
            recs.append("High memory usage detected. Consider restarting if sluggish.")
        if self.current_metrics.cpu_percent > 85:
            recs.append("High CPU load. Audio processing may stutter.")
            
        return recs

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get statistical summary of metrics"""
        if not self.metrics_history:
            return {}
            
        with self._lock:
            cpus = [m.cpu_percent for m in self.metrics_history]
            mems = [m.memory_usage_mb for m in self.metrics_history]
            
            return {
                "avg_cpu_percent": statistics.mean(cpus),
                "max_cpu_percent": max(cpus),
                "avg_memory_mb": statistics.mean(mems),
                "avg_response_time_ms": self.current_metrics.response_time_ms if self.current_metrics else 0,
                "samples_count": len(self.metrics_history)
            }

# Global instance
performance_monitor = PerformanceMonitor()