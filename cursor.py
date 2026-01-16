"""
Cursor Control Module for Iron Man Gesture Control System
Handles cursor movement, dragging, and smoothing
"""

import pyautogui
from typing import Tuple, Optional

# Screen dimensions (will be initialized on first use)
_screen_width: Optional[int] = None
_screen_height: Optional[int] = None

# Enhanced smoothing state (double exponential smoothing for Iron Man feel)
_smooth_x: Optional[float] = None
_smooth_y: Optional[float] = None
_velocity_x: Optional[float] = None  # Velocity tracking for smooth acceleration
_velocity_y: Optional[float] = None

# Drag state
_is_dragging: bool = False

# Relative mapping state
_reference_x: Optional[float] = None
_reference_y: Optional[float] = None
_use_relative_mapping: bool = True  # Enable relative mapping by default
_sensitivity: float = 1.0  # Sensitivity multiplier for relative movement

# Iron Man smoothing parameters
_smoothing_alpha: float = 0.6  # Position smoothing (higher = more responsive)
_smoothing_beta: float = 0.4   # Velocity smoothing (higher = more momentum)
_min_velocity: float = 0.001   # Minimum velocity threshold
_max_velocity: float = 0.05     # Maximum velocity cap for stability


def _get_screen_size() -> Tuple[int, int]:
    """Get screen dimensions, caching the result."""
    global _screen_width, _screen_height
    if _screen_width is None or _screen_height is None:
        _screen_width, _screen_height = pyautogui.size()
    return _screen_width, _screen_height


def set_reference_point(x: float, y: float):
    """
    Set the reference point for relative mapping.
    
    This should be called when hand tracking starts or when you want to reset
    the relative mapping origin.
    
    Args:
        x: Normalized x coordinate (0.0 to 1.0) of reference point
        y: Normalized y coordinate (0.0 to 1.0) of reference point
    """
    global _reference_x, _reference_y
    _reference_x = x
    _reference_y = y


def set_relative_mapping(enabled: bool, sensitivity: float = 2.0):
    """
    Enable or disable relative mapping mode.
    
    Args:
        enabled: True for relative mapping, False for absolute mapping
        sensitivity: Multiplier for relative movement (higher = more sensitive)
    """
    global _use_relative_mapping, _sensitivity
    _use_relative_mapping = enabled
    _sensitivity = sensitivity


def move_cursor(x: float, y: float, alpha: float = 0.35):
    """
    Move cursor using either relative or absolute mapping with enhanced EMA smoothing.
    
    Relative mapping (default):
    - Tracks hand movement relative to a reference point
    - Moves cursor relative to its current position
    - More intuitive, like a mouse
    
    Absolute mapping:
    - Maps hand position directly to screen coordinates
    - Cursor position matches hand position in camera frame
    
    Args:
        x: Normalized x coordinate (0.0 to 1.0)
        y: Normalized y coordinate (0.0 to 1.0)
        alpha: Smoothing factor for EMA (default 0.35 for better responsiveness)
    """
    global _smooth_x, _smooth_y, _velocity_x, _velocity_y, _reference_x, _reference_y, _use_relative_mapping, _sensitivity, _smoothing_alpha, _smoothing_beta, _max_velocity
    
    # Get screen dimensions
    screen_width, screen_height = _get_screen_size()
    
    if _use_relative_mapping:
        # RELATIVE MAPPING MODE - Iron Man Enhanced Smoothing
        # Initialize reference point if not set (first frame)
        if _reference_x is None or _reference_y is None:
            _reference_x = x
            _reference_y = y
            _smooth_x = 0.0
            _smooth_y = 0.0
            _velocity_x = 0.0
            _velocity_y = 0.0
            return  # Don't move on first frame, just set reference
        
        # Calculate raw delta from reference point
        raw_dx = x - _reference_x
        raw_dy = y - _reference_y
        
        # Apply sensitivity multiplier
        raw_dx *= _sensitivity
        raw_dy *= _sensitivity
        
        # IRON MAN ENHANCED SMOOTHING - Double Exponential Smoothing (Holt's Method)
        # This creates a smooth, responsive feel with natural acceleration/deceleration
        
        # Initialize velocity if needed
        if _velocity_x is None:
            _velocity_x = 0.0
        if _velocity_y is None:
            _velocity_y = 0.0
        
        # Step 1: Update smoothed position (first exponential smoothing)
        if _smooth_x is None:
            _smooth_x = raw_dx
        else:
            # Smooth position with adaptive alpha
            _smooth_x = _smoothing_alpha * raw_dx + (1 - _smoothing_alpha) * _smooth_x
        
        if _smooth_y is None:
            _smooth_y = raw_dy
        else:
            _smooth_y = _smoothing_alpha * raw_dy + (1 - _smoothing_alpha) * _smooth_y
        
        # Step 2: Update velocity (trend/velocity smoothing)
        # Velocity tracks the trend in movement
        prev_smooth_x = _smooth_x - (_smoothing_alpha * raw_dx) / (1 - _smoothing_alpha) if _smoothing_alpha < 1 else _smooth_x
        prev_smooth_y = _smooth_y - (_smoothing_alpha * raw_dy) / (1 - _smoothing_alpha) if _smoothing_alpha < 1 else _smooth_y
        
        # Calculate velocity as change in smoothed position
        velocity_update_x = _smooth_x - prev_smooth_x if _smooth_x is not None and prev_smooth_x is not None else raw_dx
        velocity_update_y = _smooth_y - prev_smooth_y if _smooth_y is not None and prev_smooth_y is not None else raw_dy
        
        # Smooth velocity with beta
        _velocity_x = _smoothing_beta * velocity_update_x + (1 - _smoothing_beta) * _velocity_x
        _velocity_y = _smoothing_beta * velocity_update_y + (1 - _smoothing_beta) * _velocity_y
        
        # Clamp velocity to prevent overshooting
        _velocity_x = max(-_max_velocity, min(_max_velocity, _velocity_x))
        _velocity_y = max(-_max_velocity, min(_max_velocity, _velocity_y))
        
        # Step 3: Apply velocity to final smoothed position (add momentum)
        final_smooth_x = _smooth_x + _velocity_x
        final_smooth_y = _smooth_y + _velocity_y
        
        # Use final smoothed values
        _smooth_x = final_smooth_x
        _smooth_y = final_smooth_y
        
        # Get current cursor position
        current_x, current_y = pyautogui.position()
        
        # Convert smoothed normalized delta to pixels
        dx_pixels = _smooth_x * screen_width
        dy_pixels = _smooth_y * screen_height
        
        # Adaptive dead zone - larger threshold for very small movements
        movement_magnitude = (dx_pixels**2 + dy_pixels**2)**0.5
        dead_zone_threshold = 1.5 if movement_magnitude < 3 else 0.5
        
        # Only move if movement exceeds dead zone
        if abs(dx_pixels) > dead_zone_threshold or abs(dy_pixels) > dead_zone_threshold:
            # Calculate new position (relative movement)
            # Hand moves right (x increases) → cursor moves right (x increases)
            # Hand moves down (y increases) → cursor moves down (y increases)
            new_x = current_x + int(dx_pixels)
            new_y = current_y + int(dy_pixels)
            
            # Clamp to screen boundaries
            new_x = max(0, min(screen_width - 1, new_x))
            new_y = max(0, min(screen_height - 1, new_y))
            
            # Move cursor (duration=0 for instant, smoothing is handled by algorithm)
            pyautogui.moveTo(new_x, new_y, duration=0.0)
        
        # Update reference point to current position for next frame
        _reference_x = x
        _reference_y = y
    
    else:
        # ABSOLUTE MAPPING MODE (original behavior)
        # First layer of EMA smoothing
        if _smooth_x is None:
            _smooth_x = x
        else:
            # Adaptive smoothing: use higher alpha for larger movements (more responsive)
            # Use lower alpha for smaller movements (more stable)
            dx = abs(x - _smooth_x)
            adaptive_alpha = min(alpha + dx * 0.3, 0.5)  # Range: alpha to 0.5
            _smooth_x = adaptive_alpha * x + (1 - adaptive_alpha) * _smooth_x
        
        if _smooth_y is None:
            _smooth_y = y
        else:
            dy = abs(y - _smooth_y)
            adaptive_alpha = min(alpha + dy * 0.3, 0.5)  # Range: alpha to 0.5
            _smooth_y = adaptive_alpha * y + (1 - adaptive_alpha) * _smooth_y
        
        # Convert normalized coordinates to screen coordinates
        # Note: MediaPipe y-coordinate is inverted (0 is top, 1 is bottom)
        screen_x = int(_smooth_x * screen_width)
        screen_y = int(_smooth_y * screen_height)
        
        # Dead zone: don't move if change is too small (prevents jitter)
        current_x, current_y = pyautogui.position()
        dx_pixels = abs(screen_x - current_x)
        dy_pixels = abs(screen_y - current_y)
        
        # Only move if change is significant (at least 2 pixels)
        if dx_pixels > 2 or dy_pixels > 2:
            pyautogui.moveTo(screen_x, screen_y, duration=0.0)


def start_drag():
    """
    Begin dragging (mouse down).
    
    Calls pyautogui.mouseDown() to start a drag operation.
    """
    global _is_dragging
    if not _is_dragging:
        pyautogui.mouseDown()
        _is_dragging = True


def stop_drag():
    """
    Stop dragging (mouse up).
    
    Calls pyautogui.mouseUp() to end a drag operation.
    """
    global _is_dragging
    if _is_dragging:
        pyautogui.mouseUp()
        _is_dragging = False


def is_dragging() -> bool:
    """Check if currently dragging."""
    return _is_dragging


def left_click():
    """
    Perform a left mouse click at the current cursor position.
    
    Calls pyautogui.click() to simulate a left mouse button click.
    """
    pyautogui.click()


def reset_smoothing():
    """Reset all smoothing state (useful when hand is lost)."""
    global _smooth_x, _smooth_y, _velocity_x, _velocity_y, _reference_x, _reference_y
    _smooth_x = None
    _smooth_y = None
    _velocity_x = None
    _velocity_y = None
    _reference_x = None
    _reference_y = None

