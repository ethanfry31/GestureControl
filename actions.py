"""
Actions Module for Iron Man Gesture Control System
Handles desktop switching and future Iron Man UI features
"""

import pyautogui


def switch_desktop_left():
    """
    Switch to the desktop on the left.
    
    Uses Windows 10/11 virtual desktop shortcut: Win + Ctrl + Left Arrow
    """
    try:
        pyautogui.hotkey("win", "ctrl", "left")
        print("Switched to left desktop")
    except Exception as e:
        print(f"Error switching desktop left: {e}")


def switch_desktop_right():
    """
    Switch to the desktop on the right.
    
    Uses Windows 10/11 virtual desktop shortcut: Win + Ctrl + Right Arrow
    """
    try:
        pyautogui.hotkey("win", "ctrl", "right")
        print("Switched to right desktop")
    except Exception as e:
        print(f"Error switching desktop right: {e}")


def switch_app_left():
    """Switch to the previous app (Alt+Tab backward)."""
    try:
        pyautogui.hotkey("alt", "shift", "tab")
        print("Switched to previous app")
    except Exception as e:
        print(f"Error switching app left: {e}")


def switch_app_right():
    """Switch to the next app (Alt+Tab forward)."""
    try:
        pyautogui.hotkey("alt", "tab")
        print("Switched to next app")
    except Exception as e:
        print(f"Error switching app right: {e}")


def scroll_up():
    """Scroll content up."""
    try:
        pyautogui.scroll(3)  # Scroll up
        print("Scrolled up")
    except Exception as e:
        print(f"Error scrolling up: {e}")


def scroll_down():
    """Scroll content down."""
    try:
        pyautogui.scroll(-3)  # Scroll down
        print("Scrolled down")
    except Exception as e:
        print(f"Error scrolling down: {e}")


def execute_swipe_command(swipe_direction: str):
    """
    Execute high-level command based on swipe direction.
    
    Args:
        swipe_direction: "swipe_left", "swipe_right", "swipe_up", "swipe_down"
    """
    command_map = {
        "swipe_left": switch_desktop_left,
        "swipe_right": switch_desktop_right,
        "swipe_up": scroll_up,
        "swipe_down": scroll_down
    }
    
    command = command_map.get(swipe_direction)
    if command:
        command()


def holographic_ui_overlay():
    """
    Placeholder for future Iron Man holographic UI overlay feature.
    
    This function is a stub for future implementation of:
    - 3D holographic interface rendering
    - Gesture-based UI navigation
    - Augmented reality overlay
    """
    pass  # Leave empty for now


def take_screenshot(filename: str = "gesture_screenshot.png"):
    """
    Take a screenshot and save it.
    
    Args:
        filename: Name of the file to save screenshot to
    """
    try:
        pyautogui.screenshot(filename)
        print(f"Screenshot saved to {filename}")
    except Exception as e:
        print(f"Error taking screenshot: {e}")

