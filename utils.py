"""
Utilities Module for Iron Man Gesture Control System
Provides sliding buffer, EMA smoothing, and landmark extraction helpers
"""

from collections import deque
from typing import List, Optional


class SlidingBuffer:
    """
    A sliding window buffer that maintains a fixed-size history.
    Automatically removes oldest items when max size is reached.
    """
    
    def __init__(self, maxlen: int = 10):
        """
        Initialize sliding buffer.
        
        Args:
            maxlen: Maximum number of items to store
        """
        self.buffer = deque(maxlen=maxlen)
        self.maxlen = maxlen
    
    def append(self, value: float):
        """Add a new value to the buffer."""
        self.buffer.append(value)
    
    def get(self) -> List[float]:
        """Get all values in the buffer as a list."""
        return list(self.buffer)
    
    def get_first(self) -> Optional[float]:
        """Get the first (oldest) value in the buffer."""
        if len(self.buffer) > 0:
            return self.buffer[0]
        return None
    
    def get_last(self) -> Optional[float]:
        """Get the last (newest) value in the buffer."""
        if len(self.buffer) > 0:
            return self.buffer[-1]
        return None
    
    def clear(self):
        """Clear all values from the buffer."""
        self.buffer.clear()
    
    def is_full(self) -> bool:
        """Check if buffer has reached max capacity."""
        return len(self.buffer) >= self.maxlen
    
    def size(self) -> int:
        """Get current size of the buffer."""
        return len(self.buffer)


def smooth(value: float, old_value: float, alpha: float = 0.2) -> float:
    """
    Exponential Moving Average (EMA) smoothing function.
    
    Formula: smooth_val = alpha * new + (1 - alpha) * old
    
    Args:
        value: New value to smooth
        old_value: Previous smoothed value
        alpha: Smoothing factor (0.0 to 1.0). Lower = more smoothing.
                Default 0.2 for moderate smoothing.
    
    Returns:
        Smoothed value
    """
    return alpha * value + (1 - alpha) * old_value


def get_landmark(landmarks, index: int):
    """
    Safely extract a landmark point by index.
    
    Args:
        landmarks: MediaPipe landmarks list
        index: Landmark index (0-20)
    
    Returns:
        Landmark point or None if index is invalid
    """
    if landmarks and 0 <= index < len(landmarks):
        return landmarks[index]
    return None


def get_wrist(landmarks):
    """Get wrist landmark (index 0)."""
    return get_landmark(landmarks, 0)


def get_index_mcp(landmarks):
    """Get index finger MCP joint (index 5)."""
    return get_landmark(landmarks, 5)


def get_middle_mcp(landmarks):
    """Get middle finger MCP joint (index 9)."""
    return get_landmark(landmarks, 9)


def distance(a, b) -> float:
    """
    Calculate Euclidean distance between two landmark points.
    
    Args:
        a: First landmark point
        b: Second landmark point
    
    Returns:
        Distance as float
    """
    if a is None or b is None:
        return 0.0
    import math
    return math.hypot(a.x - b.x, a.y - b.y)

