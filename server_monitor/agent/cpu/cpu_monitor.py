# This module is responsible for collecting CPU-related metrics using psutil. It includes logic to retrieve CPU utilization per core, average CPU usage, and system load averages. The functions are designed to be called at a fixed interval by the main agent loop.
# 
import psutil
import time
from typing import Dict, List, TypedDict


class LoadAverage(TypedDict):
    load_1_min: float
    load_5_min: float
    load_15_min: float

class CPUTimesPercent(TypedDict):
    user: float
    system: float
    idle: float
    nice: float # Present on Unix
    iowait: float # Present on Linux
    irq: float # Present on Linux, FreeBSD
    softirq: float # Present on Linux
    steal: float # Present on Linux, when running in a virtualized environment
    guest: float # Present on Linux, Windows
    guest_nice: float # Present on Linux

class CPUMetrics(TypedDict):
    timestamp: float
    cpu_usage_per_core: List[float]
    cpu_usage_average: float
    load_average: LoadAverage
    cpu_times_percent: CPUTimesPercent

def get_cpu_usage_per_core() -> List[float]:
    """
    Returns a list of CPU usage percentages for each logical core.
    Note: The first call after process start or a long idle period may return 0.0 for all cores.
    Relies on being called at intervals by the agent loop for meaningful subsequent readings.
    """
    return psutil.cpu_percent(percpu=True)


def get_cpu_usage_average() -> float:
    """
    Returns the average CPU usage percentage across all cores.
    Note: The first call after process start or a long idle period may return 0.0.
    Relies on being called at intervals by the agent loop for meaningful subsequent readings.
    """
    return psutil.cpu_percent(percpu=False)


def get_load_average() -> LoadAverage:
    """
    Returns system load average over 1, 5, and 15 minutes.
    Only available on Unix-like systems.
    """
    try:
        load1, load5, load15 = psutil.getloadavg()
        return {
            "load_1_min": load1,
            "load_5_min": load5,
            "load_15_min": load15
        }
    except (AttributeError, NotImplementedError):
        return {
            "load_1_min": -1.0,
            "load_5_min": -1.0,
            "load_15_min": -1.0
        }

def get_cpu_times_percent() -> CPUTimesPercent:
    """
    Returns a dictionary of CPU time percentages (user, system, idle, etc.).
    Note: The first call after process start or a long idle period may show skewed initial values.
    Relies on being called at intervals by the agent loop for meaningful subsequent readings.
    """
    times = psutil.cpu_times_percent()
    # psutil.cpu_times_percent() returns a namedtuple. Convert to dict.
    # Ensure all keys from TypedDict are present, defaulting if necessary.
    # This handles cases where some fields might not be present on all OSes.
    return CPUTimesPercent(
        user=getattr(times, 'user', 0.0),
        system=getattr(times, 'system', 0.0),
        idle=getattr(times, 'idle', 0.0),
        nice=getattr(times, 'nice', 0.0),
        iowait=getattr(times, 'iowait', 0.0),
        irq=getattr(times, 'irq', 0.0),
        softirq=getattr(times, 'softirq', 0.0),
        steal=getattr(times, 'steal', 0.0),
        guest=getattr(times, 'guest', 0.0),
        guest_nice=getattr(times, 'guest_nice', 0.0)
    )


def collect_cpu_metrics() -> CPUMetrics:
    """
    Collects all CPU-related metrics and returns them in a dictionary.
    """
    return {
        "timestamp": time.time(),
        "cpu_usage_per_core": get_cpu_usage_per_core(),
        "cpu_usage_average": get_cpu_usage_average(),
        "load_average": get_load_average(),
        "cpu_times_percent": get_cpu_times_percent(),
    }
