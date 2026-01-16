"""
Iron Man Gesture Control System - Version 3 (Object-Centric)
Main script implementing object-centric 3D manipulation system

Features:
- Object-centric 3D space manipulation
- Grab/release objects instead of cursor control
- Swipe gestures as high-level commands
- Radial/contextual menus
- Intent-based gesture processing
- Visual feedback and overlays
- Cursor mode fallback for testing
"""

import cv2
import mediapipe as mp
import time
from collections import deque
from typing import Optional

# Import modular components
import gestures
import cursor
import actions
import utils

# Import new object-centric components
import object
import intents
import visual_feedback
import object_controller
import menu_system

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
# Configuration
# ----------------------------
USE_OBJECT_MODE = True  # Toggle between object mode and cursor mode
CURSOR_MODE_FALLBACK = True  # Allow falling back to cursor mode

# ----------------------------
# Initialize tracking variables
# ----------------------------
# History buffer for swipe detection
swipe_buffer = utils.SlidingBuffer(maxlen=20)

# State tracking
is_dragging = False
last_swipe_time = 0
swipe_cooldown = 0.5
last_click_time = 0
click_cooldown = 0.3

# Previous gesture state
prev_fist = False
prev_open_palm = False
prev_index_pointing = False
reference_set = False

# Object-centric system
object_controller_instance: Optional[object_controller.ObjectController] = None
intent_processor = intents.IntentProcessor()
visual_feedback_instance: Optional[visual_feedback.VisualFeedback] = None

# Hand position buffer for smoothing
hand_position_buffer = utils.SlidingBuffer(maxlen=5)

# ----------------------------
# Main loop
# ----------------------------
cap = cv2.VideoCapture(0)

print("Iron Man Gesture Control System v3.0 (Object-Centric)")
print("=" * 60)
print("Mode: OBJECT-CENTRIC (Controls REAL Windows!)" if USE_OBJECT_MODE else "Mode: CURSOR (Legacy)")
print("Controls:")
if USE_OBJECT_MODE:
    print("  - Fist: Grab nearest REAL WINDOW (moves actual windows!)")
    print("  - Open palm: Release window / Hover over windows")
    print("  - Hand movement while grabbing: Drag window to new position")
    print("  - Swipe left/right: Switch virtual desktops")
    print("  - Swipe up/down: Scroll content")
    print("  - Index pointing: Click")
    print("  - Open palm near window: Open contextual menu")
    print("")
    print("You'll see window outlines on the camera view!")
    print("Orange = Hovered, Yellow = Grabbed, Gray = Other windows")
else:
    print("  - Swipe left/right: Switch desktops")
    print("  - Index finger up: Left click")
    print("  - Fist: Grab/drag windows")
    print("  - Open palm: Release windows")
    print("  - Index MCP: Control cursor position")
print("")
print("Press 'q' to quit, 'm' to toggle mode")

while True:
    success, frame = cap.read()
    if not success:
        break

    # Flip frame horizontally for mirror effect
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # Initialize object controller and visual feedback on first frame
    if object_controller_instance is None and USE_OBJECT_MODE:
        object_controller_instance = object_controller.ObjectController(w, h)
        visual_feedback_instance = visual_feedback.VisualFeedback(w, h)

    # Convert frame to RGB for MediaPipe
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        hand_landmarks = result.multi_hand_landmarks[0]
        landmarks = hand_landmarks.landmark

        # Get hand position (using index MCP as reference)
        index_mcp = utils.get_index_mcp(landmarks)
        wrist = utils.get_wrist(landmarks)
        
        if index_mcp and wrist:
            # Normalized coordinates
            norm_x = index_mcp.x
            norm_y = index_mcp.y
            
            # Estimate depth (can be improved with hand size or other methods)
            hand_size = utils.distance(wrist, index_mcp)
            norm_z = 0.3 + (1.0 - hand_size * 2) * 0.2  # Rough depth estimate
            
            # Buffer hand position for smoothing
            hand_position_buffer.append((norm_x, norm_y, norm_z))
            
            # Get smoothed position
            if hand_position_buffer.size() > 0:
                positions = hand_position_buffer.get()
                avg_x = sum(p[0] for p in positions) / len(positions)
                avg_y = sum(p[1] for p in positions) / len(positions)
                avg_z = sum(p[2] for p in positions) / len(positions)
            else:
                avg_x, avg_y, avg_z = norm_x, norm_y, norm_z

        # Get wrist x for swipe detection
        if wrist:
            swipe_buffer.append(wrist.x)

        # ----------------------------
        # Gesture Detection
        # ----------------------------
        current_fist = gestures.is_fist(landmarks)
        current_open_palm = gestures.is_open_palm(landmarks)
        current_index_pointing = gestures.is_index_pointing(landmarks)

        # Detect swipe
        swipe_direction = None
        if not current_fist and swipe_buffer.size() >= 8:
            swipe_direction = gestures.detect_swipe(swipe_buffer)

        # ----------------------------
        # Object-Centric Mode
        # ----------------------------
        if USE_OBJECT_MODE and object_controller_instance:
            # Create gesture data for intent processing
            gesture_data = {
                'fist': current_fist,
                'open_palm': current_open_palm,
                'index_pointing': current_index_pointing,
                'swipe_direction': swipe_direction,
                'position': (avg_x, avg_y, avg_z),
                'velocity': (0.0, 0.0, 0.0)  # Can be calculated from buffer
            }
            
            # Process gesture into intent
            intent = intent_processor.process_gesture(gesture_data)
            intent_processor.update_last_intent(intent)
            
            # Process intent with object controller
            object_controller_instance.process_intent(intent)
            
            # Handle swipe commands
            if swipe_direction and (time.time() - last_swipe_time) > swipe_cooldown:
                actions.execute_swipe_command(swipe_direction)
                last_swipe_time = time.time()
                swipe_buffer.clear()
            
            # Draw real windows and visual feedback
            if visual_feedback_instance:
                # Get all real windows
                windows = object_controller_instance.get_windows()
                grabbed_window = object_controller_instance.get_grabbed_window()
                hovered_window = object_controller_instance.get_window_at_position(avg_x, avg_y)
                
                # Draw all windows
                screen_w = object_controller_instance.window_manager.screen_width
                screen_h = object_controller_instance.window_manager.screen_height
                for window in windows[:10]:  # Limit to 10 windows for performance
                    is_grabbed = (grabbed_window and window.hwnd == grabbed_window.hwnd)
                    is_hovered = (hovered_window and window.hwnd == hovered_window.hwnd and not is_grabbed)
                    visual_feedback_instance.draw_window_outline(
                        frame, window, is_grabbed, is_hovered, screen_w, screen_h
                    )
                
                # Draw active menu if open
                active_menu = object_controller_instance.get_active_menu()
                if active_menu and active_menu.is_open and active_menu.position:
                    menu_x = int(active_menu.position[0] * w)
                    menu_y = int(active_menu.position[1] * h)
                    visual_feedback_instance.draw_radial_menu(
                        frame, menu_x, menu_y,
                        active_menu.get_option_labels(),
                        active_menu.selected_index
                    )
                
                # Draw intent feedback
                intent_text = intents.intent_to_action(intent)
                visual_feedback_instance.draw_intent_feedback(
                    frame, intent_text, (20, 30)
                )
                
                # Show grabbed window info
                if grabbed_window:
                    status_y = 90
                    cv2.putText(
                        frame, f"Grabbed: {grabbed_window.title[:40]}", (10, status_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2
                    )
        
        # ----------------------------
        # Cursor Mode (Legacy/Fallback)
        # ----------------------------
        else:
            # Original cursor-based control
            if index_mcp:
                if not reference_set:
                    cursor.set_reference_point(norm_x, norm_y)
                    reference_set = True
                cursor.move_cursor(norm_x, norm_y, alpha=0.35)

            # Handle gestures
            if current_index_pointing and not prev_index_pointing and not current_fist:
                if (time.time() - last_click_time) > click_cooldown:
                    cursor.left_click()
                    last_click_time = time.time()

            if current_fist and not prev_fist:
                cursor.start_drag()
                is_dragging = True

            if current_open_palm and prev_fist and is_dragging:
                cursor.stop_drag()
                is_dragging = False

            if current_fist:
                is_dragging = True
                if not cursor.is_dragging():
                    cursor.start_drag()

            if swipe_direction and (time.time() - last_swipe_time) > swipe_cooldown:
                if swipe_direction == "swipe_left":
                    actions.switch_desktop_left()
                elif swipe_direction == "swipe_right":
                    actions.switch_desktop_right()
                last_swipe_time = time.time()
                swipe_buffer.clear()

        # ----------------------------
        # Draw hand landmarks
        # ----------------------------
        mp_drawing.draw_landmarks(
            frame,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
        )

        # ----------------------------
        # Status Display
        # ----------------------------
        status_y = 60 if USE_OBJECT_MODE else 30
        cv2.putText(
            frame, f"Mode: {'OBJECT' if USE_OBJECT_MODE else 'CURSOR'}", (10, status_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2
        )
        status_y += 30
        cv2.putText(
            frame, f"Fist: {current_fist}", (10, status_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if current_fist else (0, 0, 255), 1
        )
        status_y += 25
        cv2.putText(
            frame, f"Open: {current_open_palm}", (10, status_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if current_open_palm else (0, 0, 255), 1
        )
        if swipe_direction:
            status_y += 25
            cv2.putText(
                frame, f"Swipe: {swipe_direction}", (10, status_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2
            )

        # Update previous states
        prev_fist = current_fist
        prev_open_palm = current_open_palm
        prev_index_pointing = current_index_pointing

    else:
        # No hand detected
        if is_dragging:
            cursor.stop_drag()
            is_dragging = False
        cursor.reset_smoothing()
        swipe_buffer.clear()
        hand_position_buffer.clear()
        prev_fist = False
        prev_open_palm = False
        prev_index_pointing = False
        reference_set = False
        
        if object_controller_instance:
            object_controller_instance.grabbed_window = None
            object_controller_instance.grab_offset = None
            object_controller_instance.menu_manager.close_menu()

        cv2.putText(
            frame, "No hand detected", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2
        )

    # Show video
    cv2.imshow("Iron Man Gesture Control v3.0 - Press 'q' to quit, 'm' to toggle mode", frame)

    # Handle key presses
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('m'):
        # Toggle between object mode and cursor mode
        USE_OBJECT_MODE = not USE_OBJECT_MODE
        if USE_OBJECT_MODE:
            object_controller_instance = object_controller.ObjectController(w, h)
            visual_feedback_instance = visual_feedback.VisualFeedback(w, h)
        else:
            object_controller_instance = None
            visual_feedback_instance = None
        print(f"Switched to {'OBJECT' if USE_OBJECT_MODE else 'CURSOR'} mode")

# Cleanup
if is_dragging:
    cursor.stop_drag()
cap.release()
cv2.destroyAllWindows()
print("Gesture control system stopped.")

