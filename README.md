# Iron Man Gesture Control System

A modular Python-based gesture control system that allows you to control your computer using hand gestures, inspired by Iron Man's interface.

## Project Structure

```
/GestureControl/
    version1.py      # Original gesture control (volume, play/pause, screenshots)
    version2.py      # Iron Man gesture control (swipes, drag/drop, cursor)
    gestures.py      # Gesture detection module
    cursor.py        # Cursor control and dragging
    actions.py       # System actions (desktop switching, etc.)
    utils.py         # Utility functions (buffers, smoothing, helpers)
```

## Installation

### Prerequisites

- Python 3.7 or higher
- Webcam
- Windows 10/11 (for desktop switching features)

### Install Dependencies

```bash
pip install mediapipe pyautogui opencv-python
```

### Required Packages

- **mediapipe**: Hand tracking and landmark detection
- **pyautogui**: Mouse/keyboard control and system actions
- **opencv-python**: Video capture and display

## Usage

### Version 1 (Basic Gesture Control)

Run the original gesture control system:

```bash
python version1.py
```

**Controls:**
- **Thumbs Up**: Volume Up
- **Fist**: Volume Down
- **Open Hand**: Play/Pause
- **Pinch**: Take Screenshot

### Version 2 (Iron Man Gesture Control)

Run the advanced Iron Man gesture control system:

```bash
python version2.py
```

**Controls:**
- **Swipe Left/Right**: Switch between virtual desktops
- **Fist**: Grab/drag windows (mouse down)
- **Open Palm**: Release/drop windows (mouse up)
- **Index MCP Position**: Control cursor movement

## Testing Instructions

### Test Swipe Gestures

1. Start `version2.py`
2. Position your hand in front of the camera
3. **Swipe Right**: Move your hand quickly from left to right
   - Desktop should switch to the right
4. **Swipe Left**: Move your hand quickly from right to left
   - Desktop should switch to the left

**Note**: Swipes only work when your hand is NOT in a fist position.

### Test Grab/Drag

1. Start `version2.py`
2. Open a window that can be dragged (e.g., a file explorer window)
3. **Make a Fist**: Close all fingers
   - Cursor should "click" and hold (mouse down)
   - Status should show "Dragging: True"
4. **Move Your Hand**: While maintaining the fist
   - Window should follow your cursor
   - Cursor moves smoothly based on index finger MCP position
5. **Open Palm**: Extend all fingers
   - Mouse should release (mouse up)
   - Status should show "Dragging: False"
   - Window should drop at current position

### Test Cursor Movement

1. Start `version2.py`
2. Position your hand in front of the camera
3. Move your index finger MCP joint (base of index finger)
4. Cursor should smoothly follow your hand movement
5. Movement uses EMA smoothing for natural feel

## System Behavior Rules

### Rule 1: Fist Overrides Swipe
- When fist is detected, swipe gestures are disabled
- This prevents accidental desktop switching while dragging

### Rule 2: Swipes Trigger Once
- Swipe gestures have a 0.5-second cooldown
- Prevents repeated desktop switching from a single gesture

### Rule 3: Continuous Dragging
- While fist is active, mouse stays held down
- Cursor continues to move smoothly
- When open palm is detected, mouse releases once

## Technical Details

### Gesture Detection

- **Fist**: All fingertips (8, 12, 16, 20) below their PIP joints (6, 10, 14, 18)
- **Open Palm**: At least 3 of 4 fingers extended (tips above PIP joints)
- **Swipe**: Fast horizontal movement detected over 5-10 frames
  - Threshold: dx > 0.20 (right) or dx < -0.20 (left)

### Smoothing

- **EMA (Exponential Moving Average)**: Alpha = 0.2
- Formula: `smooth_val = 0.2 * new + 0.8 * old`
- Applied to cursor movement for natural feel

### Cursor Control

- Uses **index MCP joint** (landmark 9) for position
- Normalized coordinates (0-1) mapped to screen coordinates
- Smooth movement prevents jittery cursor

## Troubleshooting

### Hand Not Detected
- Ensure good lighting
- Keep hand within camera frame
- Check camera permissions

### Gestures Not Working
- Make sure gestures are clear and deliberate
- Check console output for error messages
- Verify all dependencies are installed

### Desktop Switching Not Working
- Requires Windows 10/11
- Virtual desktops must be enabled
- Try creating a new virtual desktop first

### Cursor Not Moving Smoothly
- Adjust alpha value in `cursor.py` (lower = more smoothing)
- Ensure stable hand position
- Check camera frame rate

## Future Features

The `actions.py` module includes a placeholder for:
- **Holographic UI Overlay**: Future 3D interface rendering
- Additional gesture-based UI navigation
- Augmented reality features

## License

This project is provided as-is for educational and personal use.

## Notes

- The system works best with good lighting and a clear view of your hand
- Hand should be positioned 1-2 feet from the camera
- For best results, use a webcam with at least 720p resolution
- Press 'q' to quit the application

