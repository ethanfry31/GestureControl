"""
Window Manager for Iron Man Gesture Control
Interfaces with real Windows windows/applications
"""

import pyautogui
from typing import List, Optional, Tuple
import time

try:
    import win32gui
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("Warning: win32gui not available. Install with: pip install pywin32")
    print("Falling back to pyautogui-only window control.")


class WindowInfo:
    """Represents a real Windows window."""
    
    def __init__(self, hwnd: int, title: str, rect: Tuple[int, int, int, int]):
        """
        Initialize window info.
        
        Args:
            hwnd: Window handle
            title: Window title
            rect: (left, top, right, bottom) window rectangle
        """
        self.hwnd = hwnd
        self.title = title
        self.rect = rect
        self.left, self.top, self.right, self.bottom = rect
        self.width = self.right - self.left
        self.height = self.bottom - self.top
        self.center_x = self.left + self.width // 2
        self.center_y = self.top + self.height // 2
    
    def get_normalized_position(self, screen_width: int, screen_height: int) -> Tuple[float, float]:
        """
        Get window center position in normalized coordinates (0-1).
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        
        Returns:
            (x, y) normalized position
        """
        x = self.center_x / screen_width
        y = self.center_y / screen_height
        return (x, y)
    
    def get_normalized_size(self, screen_width: int, screen_height: int) -> Tuple[float, float]:
        """Get window size in normalized coordinates."""
        w = self.width / screen_width
        h = self.height / screen_height
        return (w, h)


class WindowManager:
    """
    Manages real Windows windows and provides control functions.
    """
    
    def __init__(self):
        """Initialize window manager."""
        self.screen_width, self.screen_height = pyautogui.size()
        self.windows: List[WindowInfo] = []
        self.last_update_time = 0
        self.update_interval = 0.5  # Update window list every 0.5 seconds
    
    def _enum_windows_callback(self, hwnd, windows):
        """Callback for enumerating windows."""
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:  # Only include windows with titles
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    windows.append(WindowInfo(hwnd, title, rect))
                except:
                    pass
    
    def get_all_windows(self) -> List[WindowInfo]:
        """
        Get list of all visible windows.
        
        Returns:
            List of WindowInfo objects
        """
        current_time = time.time()
        # Only update window list periodically to avoid performance issues
        if current_time - self.last_update_time > self.update_interval:
            self.windows = []
            if WIN32_AVAILABLE:
                try:
                    win32gui.EnumWindows(self._enum_windows_callback, self.windows)
                except:
                    pass
            self.last_update_time = current_time
        
        return self.windows.copy()
    
    def find_window_at_position(self, x: float, y: float) -> Optional[WindowInfo]:
        """
        Find window at normalized position (0-1).
        
        Args:
            x, y: Normalized position (0-1)
        
        Returns:
            WindowInfo if found, None otherwise
        """
        screen_x = int(x * self.screen_width)
        screen_y = int(y * self.screen_height)
        
        windows = self.get_all_windows()
        
        # Find window containing this point
        for window in windows:
            if (window.left <= screen_x <= window.right and
                window.top <= screen_y <= window.bottom):
                return window
        
        return None
    
    def find_nearest_window(self, x: float, y: float, max_distance: float = 0.2) -> Optional[WindowInfo]:
        """
        Find nearest window to normalized position.
        
        Args:
            x, y: Normalized position (0-1)
            max_distance: Maximum normalized distance
        
        Returns:
            Nearest WindowInfo or None
        """
        screen_x = int(x * self.screen_width)
        screen_y = int(y * self.screen_height)
        
        windows = self.get_all_windows()
        nearest = None
        min_distance = max_distance * min(self.screen_width, self.screen_height)
        
        for window in windows:
            # Calculate distance to window center
            dx = window.center_x - screen_x
            dy = window.center_y - screen_y
            distance = (dx*dx + dy*dy)**0.5
            
            if distance < min_distance:
                min_distance = distance
                nearest = window
        
        return nearest
    
    def move_window(self, window: WindowInfo, x: float, y: float):
        """
        Move window to normalized position.
        
        Args:
            window: WindowInfo to move
            x, y: Target normalized position (0-1) for window center
        """
        if not WIN32_AVAILABLE:
            # Fallback: use cursor to drag window title bar
            # This is less reliable but works without win32
            screen_x = int(x * self.screen_width)
            screen_y = int(y * self.screen_height)
            
            # Click on window title bar and drag
            title_bar_y = window.top + 30  # Approximate title bar position
            pyautogui.moveTo(window.center_x, title_bar_y)
            pyautogui.mouseDown()
            pyautogui.moveTo(screen_x, screen_y, duration=0.1)
            pyautogui.mouseUp()
            return
        
        try:
            # Calculate new position (center window at x, y)
            screen_x = int(x * self.screen_width)
            screen_y = int(y * self.screen_height)
            
            new_left = screen_x - window.width // 2
            new_top = screen_y - window.height // 2
            
            # Clamp to screen boundaries
            new_left = max(0, min(self.screen_width - window.width, new_left))
            new_top = max(0, min(self.screen_height - window.height, new_top))
            
            # Move window using Win32 API
            win32gui.SetWindowPos(
                window.hwnd,
                win32con.HWND_TOP,
                new_left,
                new_top,
                0, 0,  # Keep size
                win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            )
        except Exception as e:
            print(f"Error moving window: {e}")
    
    def bring_window_to_front(self, window: WindowInfo):
        """
        Bring window to front and activate it.
        
        Args:
            window: WindowInfo to bring to front
        """
        if not WIN32_AVAILABLE:
            # Fallback: click on window
            pyautogui.click(window.center_x, window.center_y)
            return
        
        try:
            win32gui.SetForegroundWindow(window.hwnd)
            win32gui.ShowWindow(window.hwnd, win32con.SW_RESTORE)
            win32gui.BringWindowToTop(window.hwnd)
        except Exception as e:
            print(f"Error bringing window to front: {e}")
    
    def close_window(self, window: WindowInfo):
        """
        Close a window.
        
        Args:
            window: WindowInfo to close
        """
        if not WIN32_AVAILABLE:
            # Fallback: Alt+F4
            pyautogui.click(window.center_x, window.center_y)
            pyautogui.hotkey("alt", "f4")
            return
        
        try:
            win32gui.PostMessage(window.hwnd, win32con.WM_CLOSE, 0, 0)
        except Exception as e:
            print(f"Error closing window: {e}")
    
    def minimize_window(self, window: WindowInfo):
        """Minimize a window."""
        if not WIN32_AVAILABLE:
            pyautogui.click(window.center_x, window.top + 10)
            return
        
        try:
            win32gui.ShowWindow(window.hwnd, win32con.SW_MINIMIZE)
        except Exception as e:
            print(f"Error minimizing window: {e}")
    
    def maximize_window(self, window: WindowInfo):
        """Maximize a window."""
        if not WIN32_AVAILABLE:
            pyautogui.click(window.center_x, window.top + 10)
            return
        
        try:
            win32gui.ShowWindow(window.hwnd, win32con.SW_MAXIMIZE)
        except Exception as e:
            print(f"Error maximizing window: {e}")

