"""
Iron Man Gesture Control System - Version 2
Main script implementing swipe gestures, grab/drag, and cursor control

Features:
- Swipe left/right for desktop switching
- Fist gesture to grab/drag windows
- Open palm to release/drop windows
- Smooth cursor movement with EMA
- Modular architecture
"""

import cv2
import mediapipe as mp
import time
from collections import deque

# Import our modular components
import gestures
import cursor
import actions
import utils

# ----------------------------
# Setup MediaPipe hand tracking
# ----------------------------
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.8,
    min_tracking_confidence=0.5
)

# ----------------------------
# Initialize tracking variables
# ----------------------------
# No longer need swipe buffer - using pointing gestures instead
# Keeping for potential future use or debugging
swipe_buffer = utils.SlidingBuffer(maxlen=20)

# State tracking
is_dragging = False
last_swipe_time = 0
swipe_cooldown = 0.5  # seconds - prevents repeated swipes
last_click_time = 0
click_cooldown = 0.3  # seconds - prevents repeated clicks

# Previous gesture state (for detecting transitions)
prev_fist = False
prev_open_palm = False
prev_index_pointing = False
prev_pointing_down = False

# Reference point tracking for relative mapping
reference_set = False

# ----------------------------
# Main loop
# ----------------------------
cap = cv2.VideoCapture(0)

print("Iron Man Gesture Control System v2.0")
print("=" * 60)
print("Controls:")
print("  - Point DOWN with index finger: Left click")
print("  - Point LEFT with index finger: Switch to left desktop")
print("  - Point RIGHT with index finger: Switch to right desktop")
print("  - Fist: Grab/drag windows")
print("  - Open palm: Release/drop windows / Move cursor")
print("  - Index MCP: Control cursor position (relative mapping)")
print("")
print("Click Gesture:")
print("  - Point your index finger DOWNWARD (tip below wrist)")
print("  - This won't conflict with left/right pointing (those require pointing up)")
print("")
print("Pointing Tips:")
print("  - Point DOWN: Index finger pointing down (for clicking)")
print("  - Point LEFT: Index finger pointing up, tip to the LEFT of your wrist")
print("  - Point RIGHT: Index finger pointing up, tip to the RIGHT of your wrist")
print("  - Left/Right pointing only works when pointing UP, not down")
print("  - This avoids conflicts!")
print("")
print("Press 'q' to quit")

while True:
    success, frame = cap.read()
    if not success:
        break

    # Flip frame horizontally for mirror effect (more intuitive)
    frame = cv2.flip(frame, 1)

    # Convert frame to RGB for MediaPipe
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    h, w, _ = frame.shape

    if result.multi_hand_landmarks:
        hand_landmarks = result.multi_hand_landmarks[0]
        landmarks = hand_landmarks.landmark

        # ----------------------------
        # Gesture Detection
        # ----------------------------
        # Check pointing down FIRST (before fist) to avoid conflicts
        current_pointing_down = gestures.is_pointing_down(landmarks)
        
        # Only check for fist if NOT pointing down (pointing down takes priority)
        current_fist = False
        if not current_pointing_down:
            current_fist = gestures.is_fist(landmarks)
        
        current_open_palm = gestures.is_open_palm(landmarks)
        current_index_pointing = gestures.is_index_pointing(landmarks)
        
        # Detect pointing left/right (replaces swipe motion)
        # Only detect if not in fist and index finger is extended upward
        # Pointing left/right only works when pointing up, not when pointing down
        pointing_direction = None
        if not current_fist and current_index_pointing and not current_pointing_down:
            if gestures.is_pointing_left(landmarks):
                pointing_direction = "point_left"
            elif gestures.is_pointing_right(landmarks):
                pointing_direction = "point_right"

        # ----------------------------
        # Handle Pointing Left/Right Gestures (replaces swipe motion)
        # ----------------------------
        # Only trigger on transition (when you start pointing, not while holding)
        pointing_left = pointing_direction == "point_left"
        pointing_right = pointing_direction == "point_right"
        prev_pointing_left = hasattr(gestures, '_prev_pointing_left') and gestures._prev_pointing_left
        prev_pointing_right = hasattr(gestures, '_prev_pointing_right') and gestures._prev_pointing_right
        
        if pointing_left and not prev_pointing_left and (time.time() - last_swipe_time) > swipe_cooldown:
            actions.switch_desktop_left()
            last_swipe_time = time.time()
            print("Point LEFT detected! Switching to left desktop")
        
        if pointing_right and not prev_pointing_right and (time.time() - last_swipe_time) > swipe_cooldown:
            actions.switch_desktop_right()
            last_swipe_time = time.time()
            print("Point RIGHT detected! Switching to right desktop")
        
        # Store previous state for transition detection
        gestures._prev_pointing_left = pointing_left
        gestures._prev_pointing_right = pointing_right

        # ----------------------------
        # Handle Pointing Down → Left Click
        # ----------------------------
        # Pointing down detected: perform left click (with cooldown)
        # Pointing down is distinct from fist and won't conflict with left/right pointing
        prev_pointing_down = hasattr(gestures, '_prev_pointing_down') and gestures._prev_pointing_down
        
        # Click when pointing down (doesn't conflict with left/right since those require pointing up)
        # Pointing down already takes priority over fist, so no need to check for fist here
        if current_pointing_down and not prev_pointing_down:
            # Only click if enough time has passed since last click
            if (time.time() - last_click_time) > click_cooldown:
                cursor.left_click()
                last_click_time = time.time()
                print("Click (Point Down)")
        
        gestures._prev_pointing_down = current_pointing_down

        # ----------------------------
        # Handle Grab/Drag (Rule 3: Continuous dragging)
        # ----------------------------
        # Fist detected: begin drag if not already dragging
        # Note: Fist takes priority over index pointing
        if current_fist and not prev_fist:
            cursor.start_drag()
            is_dragging = True
            print("Grab: Drag started")

        # Open palm detected: release drag if previously dragging
        if current_open_palm and prev_fist and is_dragging:
            cursor.stop_drag()
            is_dragging = False
            print("Release: Drag stopped")

        # If still in fist, maintain drag state
        if current_fist:
            is_dragging = True
            if not cursor.is_dragging():
                cursor.start_drag()

        # ----------------------------
        # Cursor Movement (Rule 3: Continuous movement while dragging)
        # ----------------------------
        # Use index MCP (landmark 9) for cursor control
        index_mcp = utils.get_index_mcp(landmarks)
        if index_mcp:
            # Normalized coordinates (0-1)
            norm_x = index_mcp.x
            norm_y = index_mcp.y
            
            # Set reference point on first detection (for relative mapping)
            if not reference_set:
                cursor.set_reference_point(norm_x, norm_y)
                reference_set = True
            
            # Move cursor with relative mapping and enhanced smoothing
            cursor.move_cursor(norm_x, norm_y, alpha=0.35)

        # ----------------------------
        # Visual Feedback
        # ----------------------------
        # Draw hand landmarks
        mp_drawing.draw_landmarks(
            frame,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
        )

        # Display status information
        status_y = 30
        cv2.putText(
            frame, f"Fist: {current_fist}", (10, status_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if current_fist else (0, 0, 255), 2
        )
        status_y += 30
        cv2.putText(
            frame, f"Open: {current_open_palm}", (10, status_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if current_open_palm else (0, 0, 255), 2
        )
        status_y += 30
        cv2.putText(
            frame, f"Pointing: {current_index_pointing}", (10, status_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if current_index_pointing else (0, 0, 255), 2
        )
        status_y += 30
        cv2.putText(
            frame, f"Point Down: {current_pointing_down}", (10, status_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if current_pointing_down else (0, 0, 255), 2
        )
        status_y += 30
        cv2.putText(
            frame, f"Dragging: {is_dragging}", (10, status_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if is_dragging else (0, 0, 255), 2
        )
        status_y += 30
        # Show pointing direction
        if pointing_left:
            cv2.putText(
                frame, "Pointing: LEFT", (10, status_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 3
            )
        elif pointing_right:
            cv2.putText(
                frame, "Pointing: RIGHT", (10, status_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 3
            )
        
        # Show pointing debug info
        if current_index_pointing:
            wrist = utils.get_wrist(landmarks)
            index_tip = landmarks[8]
            if wrist:
                x_offset = index_tip.x - wrist.x
                status_y += 30
                if abs(x_offset) > 0.05:
                    color = (0, 255, 0)  # Green - pointing detected
                    direction = "RIGHT" if x_offset > 0 else "LEFT"
                    cv2.putText(
                        frame, f"Point Offset: {x_offset:.3f} ({direction})", (10, status_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
                    )
                else:
                    color = (150, 150, 150)  # Gray - not pointing left/right
                    cv2.putText(
                        frame, f"Point Offset: {x_offset:.3f} (CENTER)", (10, status_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1
                    )

        # Update previous states
        prev_fist = current_fist
        prev_open_palm = current_open_palm
        prev_index_pointing = current_index_pointing

    else:
        # No hand detected - reset dragging state
        if is_dragging:
            cursor.stop_drag()
            is_dragging = False
        cursor.reset_smoothing()
        swipe_buffer.clear()
        prev_fist = False
        prev_open_palm = False
        prev_index_pointing = False
        prev_pointing_down = False
        reference_set = False  # Reset reference point flag when hand is lost
        # Reset pointing state
        if hasattr(gestures, '_prev_pointing_left'):
            gestures._prev_pointing_left = False
        if hasattr(gestures, '_prev_pointing_right'):
            gestures._prev_pointing_right = False
        if hasattr(gestures, '_prev_pointing_down'):
            gestures._prev_pointing_down = False

        cv2.putText(
            frame, "No hand detected", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2
        )

    # Show video
    cv2.imshow("Iron Man Gesture Control v2.0 - Press 'q' to quit", frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
if is_dragging:
    cursor.stop_drag()
cap.release()
cv2.destroyAllWindows()
print("Gesture control system stopped.")

