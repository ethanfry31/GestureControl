"""
Gesture Detection Module for Iron Man Gesture Control System
Detects fist, open palm, and swipe gestures
"""

from collections import deque
from typing import Optional, List
import utils


def is_fist(lm) -> bool:
    """
    Detect if hand is in a fist gesture.
    
    Fist detection: All fingertips (8, 12, 16, 20) should be below their 
    corresponding PIP joints (6, 10, 14, 18).
    
    Args:
        lm: MediaPipe landmarks list
    
    Returns:
        True if fist is detected, False otherwise
    """
    if not lm or len(lm) < 21:
        return False
    
    # Finger tip indices and their corresponding PIP joint indices
    # [index_tip, middle_tip, ring_tip, pinky_tip]
    tip_indices = [8, 12, 16, 20]
    pip_indices = [6, 10, 14, 18]
    
    # Check each finger: tip should be below PIP joint (higher y value)
    for tip_idx, pip_idx in zip(tip_indices, pip_indices):
        if tip_idx >= len(lm) or pip_idx >= len(lm):
            continue
        
        tip = lm[tip_idx]
        pip = lm[pip_idx]
        
        # If tip is above PIP (lower y value), finger is extended = not a fist
        if tip.y < pip.y:
            return False
    
    # All fingers are down (tips below PIPs) = fist
    return True


def is_open_palm(lm) -> bool:
    """
    Detect if hand is in an open palm gesture.
    
    Open palm: Opposite of fist - all fingertips should be above their PIP joints.
    
    Args:
        lm: MediaPipe landmarks list
    
    Returns:
        True if open palm is detected, False otherwise
    """
    if not lm or len(lm) < 21:
        return False
    
    # Finger tip indices and their corresponding PIP joint indices
    tip_indices = [8, 12, 16, 20]
    pip_indices = [6, 10, 14, 18]
    
    # Check each finger: tip should be above PIP joint (lower y value)
    fingers_extended = 0
    for tip_idx, pip_idx in zip(tip_indices, pip_indices):
        if tip_idx >= len(lm) or pip_idx >= len(lm):
            continue
        
        tip = lm[tip_idx]
        pip = lm[pip_idx]
        
        # If tip is above PIP (lower y value), finger is extended
        if tip.y < pip.y:
            fingers_extended += 1
    
    # Open palm: at least 3 out of 4 fingers extended (allows for slight variations)
    return fingers_extended >= 3


def detect_swipe(history_buffer) -> Optional[str]:
    """
    Detect swipe gesture - improved for better responsiveness and fewer false negatives.
    
    Improvements:
    - Shorter detection window (3-5 frames) for faster response
    - Lower displacement threshold (0.06 instead of 0.10)
    - Accepts very fast movements (no upper speed limit)
    - More lenient direction consistency (50% instead of 60%)
    - Prioritizes distance and direction over strict speed requirements
    
    Args:
        history_buffer: SlidingBuffer or deque containing x-coordinate history
    
    Returns:
        "swipe_left", "swipe_right", or None if no swipe detected
    """
    # Handle both SlidingBuffer and deque
    if hasattr(history_buffer, 'buffer'):
        buffer_list = list(history_buffer.buffer)
    elif hasattr(history_buffer, 'get'):
        buffer_list = history_buffer.get()
    else:
        buffer_list = list(history_buffer)
    
    # Need at least 3 frames for very fast swipes
    if not buffer_list or len(buffer_list) < 3:
        return None
    
    # Use shorter detection window (3-5 frames) for faster response
    # This catches quick swipes that might be missed with longer windows
    window_size = min(5, len(buffer_list))
    start_idx = len(buffer_list) - window_size
    window_buffer = buffer_list[start_idx:]
    
    if len(window_buffer) < 3:
        return None
    
    first_x = window_buffer[0]
    last_x = window_buffer[-1]
    num_frames = len(window_buffer)
    
    # Calculate total displacement
    dx = last_x - first_x
    
    # Calculate average velocity per frame
    avg_velocity = abs(dx) / num_frames if num_frames > 0 else 0
    
    # Calculate peak velocity (max single-frame movement)
    # No upper limit - accept very fast movements
    max_frame_velocity = 0.0
    for i in range(1, len(window_buffer)):
        frame_velocity = abs(window_buffer[i] - window_buffer[i-1])
        max_frame_velocity = max(max_frame_velocity, frame_velocity)
    
    # Check for consistent direction (very lenient - 50% consistency)
    right_movements = 0
    left_movements = 0
    neutral_movements = 0
    
    for i in range(1, len(window_buffer)):
        frame_dx = window_buffer[i] - window_buffer[i-1]
        if frame_dx > 0.008:  # Moving right (lowered threshold)
            right_movements += 1
        elif frame_dx < -0.008:  # Moving left (lowered threshold)
            left_movements += 1
        else:
            neutral_movements += 1
    
    # Very lenient consistency requirement (50% instead of 60%)
    # This allows for some jitter while still detecting direction
    consistency_threshold = max(2, int(num_frames * 0.5))
    
    # IMPROVED swipe detection criteria:
    # 1. LOWER displacement threshold (0.06 instead of 0.10)
    #    This allows shorter, faster movements to count as swipes
    min_displacement = 0.06
    
    # 2. LOWER minimum average velocity (0.010 instead of 0.015)
    #    Accepts slower but deliberate movements
    min_avg_velocity = 0.010
    
    # 3. LOWER peak velocity threshold (0.015 instead of 0.02)
    #    Catches shorter fast movements
    min_peak_velocity = 0.015
    
    # 4. NO UPPER SPEED LIMIT - accept very fast gestures
    #    As long as direction and distance are roughly correct
    
    # Check for right swipe
    # Priority: displacement > direction consistency > speed
    if dx > min_displacement:
        # Check if direction is roughly correct (at least 50% right movements)
        if right_movements >= consistency_threshold:
            # Accept if either average OR peak velocity is sufficient
            # This catches both slow deliberate swipes and fast quick swipes
            if avg_velocity >= min_avg_velocity or max_frame_velocity >= min_peak_velocity:
                return "swipe_right"
        # Even if consistency is borderline, accept if displacement and speed are good
        elif right_movements >= max(1, consistency_threshold - 1) and avg_velocity >= min_avg_velocity * 1.5:
            return "swipe_right"
    
    # Check for left swipe
    # Same logic as right swipe
    elif dx < -min_displacement:
        if left_movements >= consistency_threshold:
            if avg_velocity >= min_avg_velocity or max_frame_velocity >= min_peak_velocity:
                return "swipe_left"
        elif left_movements >= max(1, consistency_threshold - 1) and avg_velocity >= min_avg_velocity * 1.5:
            return "swipe_left"
    
    return None


def is_pointing_left(lm) -> bool:
    """
    Detect if index finger is pointing to the left.
    
    Pointing left:
    - Index finger is extended (tip above PIP)
    - Index finger tip is significantly to the left of the wrist
    - Other fingers should be down (optional, for stricter detection)
    
    Args:
        lm: MediaPipe landmarks
    
    Returns:
        True if pointing left, False otherwise
    """
    # Get key landmarks
    wrist = lm[0]
    index_tip = lm[8]
    index_pip = lm[6]
    
    # Check if index finger is extended
    index_extended = index_tip.y < index_pip.y
    
    if not index_extended:
        return False
    
    # Check if index finger tip is to the left of wrist
    # In normalized coordinates, left is smaller x value
    # Use a threshold to ensure it's a deliberate point, not just slight offset
    x_offset = wrist.x - index_tip.x  # Positive if pointing left
    
    # Threshold: index tip should be at least 0.08 units to the left of wrist
    # Increased threshold to avoid conflicts with center pointing (clicking)
    return x_offset > 0.08


def is_pointing_right(lm) -> bool:
    """
    Detect if index finger is pointing to the right.
    
    Pointing right:
    - Index finger is extended (tip above PIP)
    - Index finger tip is significantly to the right of the wrist
    - Other fingers should be down (optional, for stricter detection)
    
    Args:
        lm: MediaPipe landmarks
    
    Returns:
        True if pointing right, False otherwise
    """
    # Get key landmarks
    wrist = lm[0]
    index_tip = lm[8]
    index_pip = lm[6]
    
    # Check if index finger is extended
    index_extended = index_tip.y < index_pip.y
    
    if not index_extended:
        return False
    
    # Check if index finger tip is to the right of wrist
    # In normalized coordinates, right is larger x value
    x_offset = index_tip.x - wrist.x  # Positive if pointing right
    
    # Threshold: index tip should be at least 0.08 units to the right of wrist
    # Increased threshold to avoid conflicts with center pointing (clicking)
    return x_offset > 0.08


def is_pointing_down(lm) -> bool:
    """
    Detect if index finger is pointing downward (for clicking).
    
    Pointing down:
    - Index finger is extended downward (tip below PIP)
    - Index finger tip is below the wrist
    - Used for clicking - won't conflict with left/right pointing
    
    Args:
        lm: MediaPipe landmarks
    
    Returns:
        True if pointing down is detected, False otherwise
    """
    if not lm or len(lm) < 21:
        return False
    
    # Get key landmarks
    wrist = lm[0]
    index_tip = lm[8]
    index_pip = lm[6]
    
    # Check if index finger is pointing down (tip below PIP)
    index_pointing_down = index_tip.y > index_pip.y
    
    if not index_pointing_down:
        return False
    
    # Check if index finger tip is below the wrist
    # In normalized coordinates, down is larger y value
    y_offset = index_tip.y - wrist.y  # Positive if pointing down
    
    # Threshold: index tip should be at least 0.05 units below wrist
    # This ensures it's a deliberate downward point, not just slightly down
    return y_offset > 0.05


def is_index_pointing(lm) -> bool:
    """
    Detect if only the index finger is extended (pointing gesture).
    
    Index pointing: 
    - Index finger tip (8) should be above index PIP (6)
    - Other fingers (middle, ring, pinky) should be down (tips below PIPs)
    - Thumb can be in any position
    
    Args:
        lm: MediaPipe landmarks list
    
    Returns:
        True if index pointing is detected, False otherwise
    """
    if not lm or len(lm) < 21:
        return False
    
    # Check index finger: tip should be above PIP (extended)
    index_tip = lm[8]
    index_pip = lm[6]
    index_extended = index_tip.y < index_pip.y
    
    if not index_extended:
        return False
    
    # Check other fingers: should be down (not extended)
    # Middle, ring, pinky
    other_fingers = [
        (lm[12], lm[10]),  # middle
        (lm[16], lm[14]),  # ring
        (lm[20], lm[18])   # pinky
    ]
    
    for tip, pip in other_fingers:
        # If any other finger is extended, it's not a pointing gesture
        if tip.y < pip.y:
            return False
    
    # Index extended, others down = pointing gesture
    return True


def cleanup_smooth(value: float, old_value: float, alpha: float = 0.2) -> float:
    """
    Exponential smoothing for gesture values.
    
    This is a wrapper around utils.smooth() for consistency with the API.
    
    Args:
        value: New value to smooth
        old_value: Previous smoothed value
        alpha: Smoothing factor (default 0.2)
    
    Returns:
        Smoothed value
    """
    return utils.smooth(value, old_value, alpha)

