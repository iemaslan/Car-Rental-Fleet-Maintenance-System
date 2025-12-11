"""
Clock interfaces and implementations for time-dependent operations.
This allows for deterministic testing by injecting different clock implementations.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional


class Clock(ABC):
    """Abstract base class for clock implementations."""
    
    @abstractmethod
    def now(self) -> datetime:
        """Returns the current datetime."""
        pass
    
    def now_iso(self) -> str:
        """Returns the current time in ISO 8601 format."""
        return self.now().isoformat()


class SystemClock(Clock):
    """Clock implementation that uses the system time."""
    
    def now(self) -> datetime:
        """Returns the current system time."""
        return datetime.now()


class FixedClock(Clock):
    """Clock implementation that returns a fixed time for testing."""
    
    def __init__(self, fixed_time: Optional[datetime] = None):
        """
        Initialize with a fixed time.
        
        Args:
            fixed_time: The datetime to return. If None, uses the current time.
        """
        self._fixed_time = fixed_time or datetime.now()
    
    def now(self) -> datetime:
        """Returns the fixed time."""
        return self._fixed_time
    
    def set_time(self, new_time: datetime) -> None:
        """Update the fixed time."""
        self._fixed_time = new_time
    
    def advance(self, **kwargs) -> None:
        """
        Advance the clock by the specified time delta.
        
        Args:
            **kwargs: Arguments to pass to timedelta (days, hours, minutes, etc.)
        """
        self._fixed_time += timedelta(**kwargs)
