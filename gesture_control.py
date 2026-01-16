import cv2
import mediapipe as mp
import math
import time
import pyautogui

# ----------------------------
# Setup MediaPipe hand tracking
# ----------------------------
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Improved detection settings
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.8,
    min_tracking_confidence=0.5
)


# ---------------------------------------------------------
# Utility function: distance between two landmark points
# ---------------------------------------------------------
def distance(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


# ---------------------------------------------------------
# Gesture classification based on finger positions
# ---------------------------------------------------------
def classify_gesture(landmarks, handedness=None):
    # Key landmarks
    wrist = landmarks[0]
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]  # Thumb interphalangeal joint
    thumb_mcp = landmarks[2]  # Thumb MCP joint
    
    index_tip = landmarks[8]
    index_pip = landmarks[6]
    index_mcp = landmarks[5]
    
    middle_tip = landmarks[12]
    middle_pip = landmarks[10]
    middle_mcp = landmarks[9]
    
    ring_tip = landmarks[16]
    ring_pip = landmarks[14]
    ring_mcp = landmarks[13]
    
    pinky_tip = landmarks[20]
    pinky_pip = landmarks[18]
    pinky_mcp = landmarks[17]
    
    # Calculate hand size for relative measurements
    # Use distance from wrist to middle MCP as reference
    hand_size = distance(wrist, middle_mcp)
    
    # Calculate finger states first (needed for pinch check and return value)
    fingers_extended = []
    
    # Thumb detection: differentiate between horizontal fist and vertical thumbs up
    # First, calculate hand orientation (needed for thumb detection)
    key_y_positions_temp = [
        wrist.y, thumb_mcp.y, index_mcp.y, middle_mcp.y, ring_mcp.y, pinky_mcp.y
    ]
    key_x_positions_temp = [
        wrist.x, thumb_mcp.x, index_mcp.x, middle_mcp.x, ring_mcp.x, pinky_mcp.x
    ]
    vertical_spread_temp = max(key_y_positions_temp) - min(key_y_positions_temp)
    horizontal_spread_temp = max(key_x_positions_temp) - min(key_x_positions_temp)
    is_horizontal_temp = horizontal_spread_temp > vertical_spread_temp * 1.15
    
    thumb_extended = False
    
    # For vertical hand (thumbs up scenario): thumb must be clearly extended upward
    if not is_horizontal_temp:
        # Vertical hand: thumb is extended if it's significantly above thumb MCP
        if thumb_tip.y < thumb_mcp.y - 0.05:
            thumb_extended = True
        # Also check if thumb tip is above the top of the hand
        hand_top_temp = min(key_y_positions_temp)
        if thumb_tip.y < hand_top_temp - 0.02:
            thumb_extended = True
    
    # For horizontal hand: be more strict - thumb should be clearly extended sideways
    # This prevents detecting thumb in a horizontal fist
    else:
        # Horizontal hand: only detect thumb if it's clearly extended beyond IP joint
        thumb_extension_dist = distance(thumb_tip, thumb_mcp)
        thumb_base_dist = distance(thumb_ip, thumb_mcp)
        if thumb_extension_dist > thumb_base_dist * 1.5:  # Stricter threshold
            # Also check horizontal extension
            if handedness:
                hand_label = handedness.classification[0].label
                if hand_label == "Left":
                    if thumb_tip.x > thumb_ip.x + 0.05:  # Stricter threshold
                        thumb_extended = True
                else:
                    if thumb_tip.x < thumb_ip.x - 0.05:  # Stricter threshold
                        thumb_extended = True
            else:
                # If no handedness, check if thumb is clearly extended horizontally
                thumb_horizontal_dist = abs(thumb_tip.x - thumb_ip.x)
                if thumb_horizontal_dist > 0.05:
                    thumb_extended = True
    
    fingers_extended.append(1 if thumb_extended else 0)
    
    # Check other fingers
    finger_data = [
        (index_tip, index_pip, index_mcp),
        (middle_tip, middle_pip, middle_mcp),
        (ring_tip, ring_pip, ring_mcp),
        (pinky_tip, pinky_pip, pinky_mcp)
    ]
    
    for tip, pip, mcp in finger_data:
        # Finger is extended if tip is above PIP joint
        # Use a small threshold to account for hand angle and improve robustness
        tip_to_pip_dist = pip.y - tip.y
        is_extended = tip_to_pip_dist > 0.01  # Tip must be clearly above PIP
        fingers_extended.append(1 if is_extended else 0)
    
    # PINCH detection (check after calculating finger states)
    # Check if thumb and index are close together
    pinch_dist = distance(thumb_tip, index_tip)
    # Make threshold relative to hand size (more robust)
    if pinch_dist < hand_size * 0.12:  # Adjusted threshold - was 0.15, now more sensitive
        # Additional check: make sure other fingers are not extended
        if fingers_extended[2] == 0 and fingers_extended[3] == 0 and fingers_extended[4] == 0:
            # Thumb and index can be extended or not for pinch, but other fingers must be down
            return "pinch", fingers_extended
    
    # Calculate fingers_count from already computed fingers_extended
    fingers_count = sum(fingers_extended)
    
    # Calculate hand orientation to differentiate fist (horizontal) from thumbs up (vertical)
    # Use wrist to middle finger MCP as reference for hand direction
    wrist_to_middle = math.sqrt((middle_mcp.x - wrist.x)**2 + (middle_mcp.y - wrist.y)**2)
    
    # Calculate vertical spread of hand (difference between highest and lowest key points)
    # Key points: wrist, thumb_mcp, index_mcp, middle_mcp, ring_mcp, pinky_mcp
    key_y_positions = [
        wrist.y, thumb_mcp.y, index_mcp.y, middle_mcp.y, ring_mcp.y, pinky_mcp.y
    ]
    vertical_spread = max(key_y_positions) - min(key_y_positions)
    
    # Calculate horizontal spread
    key_x_positions = [
        wrist.x, thumb_mcp.x, index_mcp.x, middle_mcp.x, ring_mcp.x, pinky_mcp.x
    ]
    horizontal_spread = max(key_x_positions) - min(key_x_positions)
    
    # Hand is more horizontal if horizontal_spread > vertical_spread
    # Hand is more vertical if vertical_spread > horizontal_spread
    is_horizontal = horizontal_spread > vertical_spread * 1.2  # Horizontal if 20% wider than tall
    
    # Calculate thumb extension angle/direction for thumbs up
    # For thumbs up, thumb should be clearly above the hand
    thumb_vertical_position = thumb_tip.y
    hand_top = min(key_y_positions)  # Top of hand (lowest y value)
    hand_bottom = max(key_y_positions)  # Bottom of hand (highest y value)
    
    # Thumb is "up" if it's above the top of the hand or significantly above the thumb MCP
    thumb_is_up = thumb_tip.y < hand_top + 0.05 or thumb_tip.y < thumb_mcp.y - 0.06
    
    # Classify gestures based on pattern and orientation
    # 1. THUMBS UP (only thumb extended, hand vertical, thumb pointing up)
    if fingers_extended == [1, 0, 0, 0, 0]:
        # Additional checks: thumb should be extended upward, hand should be more vertical
        if thumb_is_up and not is_horizontal:
            return "thumbs_up", fingers_extended
        # If thumb is extended but hand is horizontal, might be a loose fist
        # Fall through to fist detection
    
    # 2. FIST (no fingers extended OR hand is horizontal with minimal finger extension)
    if fingers_count == 0:
        # Classic fist: no fingers extended
        return "fist", fingers_extended
    elif fingers_count <= 1 and is_horizontal:
        # Horizontal hand with at most one finger slightly extended = fist
        # This handles cases where thumb might be slightly visible in a horizontal fist
        return "fist", fingers_extended
    
    # 3. OPEN HAND (all 5 fingers extended)
    if fingers_count == 5:
        return "open", fingers_extended
    
    # Else unknown gesture
    return "unknown", fingers_extended


# -----------------------------------------------------------------------
# MAIN LOOP: read webcam → detect hand → classify → perform system action
# -----------------------------------------------------------------------
cap = cv2.VideoCapture(0)

# Cooldown so actions don’t repeat too fast
last_action_time = 0
cooldown = 1.0  # seconds

while True:
    success, frame = cap.read()
    if not success:
        break

    # Flip frame horizontally for mirror effect (more intuitive)
    frame = cv2.flip(frame, 1)

    # Convert frame to RGB for mediapipe
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    # Get frame dimensions for drawing
    h, w, _ = frame.shape

    if result.multi_hand_landmarks:
        hand_landmarks = result.multi_hand_landmarks[0]
        landmarks = hand_landmarks.landmark
        
        # Get handedness information
        handedness = None
        if result.multi_handedness:
            handedness = result.multi_handedness[0]

        # Classify gesture with handedness info
        gesture, fingers_extended = classify_gesture(landmarks, handedness)

        # Display gesture on screen with background for visibility
        text = f"Gesture: {gesture.upper()}"
        (text_width, text_height), baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, 1, 3
        )
        
        # Draw background rectangle
        cv2.rectangle(
            frame,
            (10, 10),
            (text_width + 20, text_height + 40),
            (0, 0, 0),
            -1
        )
        
        # Draw gesture text
        cv2.putText(
            frame, text, (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3
        )
        
        # Display handedness if available
        if handedness:
            hand_label = handedness.classification[0].label
            hand_score = handedness.classification[0].score
            hand_text = f"{hand_label} ({hand_score:.2f})"
            cv2.putText(
                frame, hand_text, (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
            )
        
        # Calculate and display hand orientation (for debugging)
        wrist_pos = landmarks[0]
        key_y_pos = [
            wrist_pos.y, landmarks[2].y, landmarks[5].y, landmarks[9].y,
            landmarks[13].y, landmarks[17].y
        ]
        key_x_pos = [
            wrist_pos.x, landmarks[2].x, landmarks[5].x, landmarks[9].x,
            landmarks[13].x, landmarks[17].x
        ]
        vert_spread = max(key_y_pos) - min(key_y_pos)
        horiz_spread = max(key_x_pos) - min(key_x_pos)
        is_horiz = horiz_spread > vert_spread * 1.2
        orientation_text = "Horizontal" if is_horiz else "Vertical"
        cv2.putText(
            frame, f"Orientation: {orientation_text}", (20, 245),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2
        )
        
        # Debug: Show finger states (helpful for troubleshooting)
        finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
        y_offset = 120
        for i, (name, extended) in enumerate(zip(finger_names, fingers_extended)):
            status = "UP" if extended else "DOWN"
            color = (0, 255, 0) if extended else (0, 0, 255)
            cv2.putText(
                frame, f"{name}: {status}", (20, y_offset + i * 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
            )

        # Draw the hand landmarks
        mp_drawing.draw_landmarks(
            frame,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
        )

        # Trigger actions with cooldown
        if time.time() - last_action_time > cooldown:
            if gesture == "thumbs_up":
                pyautogui.press("volumeup")
                last_action_time = time.time()
                print("Volume Up")

            elif gesture == "fist":
                pyautogui.press("volumedown")
                last_action_time = time.time()
                print("Volume Down")

            elif gesture == "open":
                pyautogui.press("playpause")
                last_action_time = time.time()
                print("Play/Pause")

            elif gesture == "pinch":
                pyautogui.screenshot("gesture_screenshot.png")
                last_action_time = time.time()
                print("Screenshot taken")

    else:
        # No hand detected
        cv2.putText(
            frame, "No hand detected", (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2
        )

    # Show video
    cv2.imshow("Gesture Control - Press 'q' to quit", frame)

    # Press q to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
