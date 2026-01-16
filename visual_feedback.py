"""
Visual Feedback System for Iron Man Gesture Control
Provides visual overlays, object highlighting, and AR-style feedback
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from object import VirtualObject, ObjectState
import window_manager


class VisualFeedback:
    """
    Handles visual feedback for the object-centric system.
    """
    
    def __init__(self, frame_width: int, frame_height: int):
        """
        Initialize visual feedback system.
        
        Args:
            frame_width: Width of the video frame
            frame_height: Height of the video frame
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # Color scheme (Orange, White, Black - Iron Man theme)
        self.colors = {
            'idle': (100, 100, 100),      # Gray
            'hovered': (0, 165, 255),     # Orange (BGR)
            'grabbed': (0, 255, 255),     # Yellow/Cyan
            'selected': (255, 255, 255),  # White
            'glow': (0, 165, 255),        # Orange glow
            'menu': (255, 255, 255),      # White menu
            'menu_bg': (0, 0, 0)          # Black background
        }
    
    def draw_object(self, frame: np.ndarray, obj: VirtualObject):
        """
        Draw a virtual object on the frame.
        
        Args:
            frame: OpenCV frame to draw on
            obj: VirtualObject to draw
        """
        # Convert normalized position to pixel coordinates
        x_pixel = int(obj.x * self.frame_width)
        y_pixel = int(obj.y * self.frame_height)
        size_pixel = int(obj.size * min(self.frame_width, self.frame_height))
        
        # Get color based on state
        if obj.state == ObjectState.GRABBED:
            color = self.colors['grabbed']
            thickness = 4
        elif obj.state == ObjectState.HOVERED:
            color = self.colors['hovered']
            thickness = 3
        elif obj.state == ObjectState.SELECTED:
            color = self.colors['selected']
            thickness = 2
        else:
            color = self.colors['idle']
            thickness = 1
        
        # Draw object as a rectangle (representing a window/panel)
        half_size = size_pixel // 2
        top_left = (x_pixel - half_size, y_pixel - half_size)
        bottom_right = (x_pixel + half_size, y_pixel + half_size)
        
        # Draw filled rectangle with border
        cv2.rectangle(frame, top_left, bottom_right, color, -1)  # Filled
        cv2.rectangle(frame, top_left, bottom_right, (255, 255, 255), thickness)  # Border
        
        # Add glow effect for hovered/grabbed objects
        if obj.hover_glow:
            self._draw_glow(frame, x_pixel, y_pixel, size_pixel, color)
        
        # Draw object label
        label = f"{obj.name} ({obj.type})"
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        label_x = x_pixel - label_size[0] // 2
        label_y = y_pixel - half_size - 10
        
        # Draw label background
        cv2.rectangle(
            frame,
            (label_x - 5, label_y - label_size[1] - 5),
            (label_x + label_size[0] + 5, label_y + 5),
            self.colors['menu_bg'],
            -1
        )
        
        # Draw label text
        cv2.putText(
            frame, label,
            (label_x, label_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            self.colors['menu'], 1
        )
    
    def _draw_glow(self, frame: np.ndarray, x: int, y: int, size: int, color: Tuple[int, int, int]):
        """
        Draw a glow effect around an object.
        
        Args:
            frame: OpenCV frame
            x, y: Center position
            size: Object size
            color: Glow color
        """
        # Draw multiple circles with decreasing opacity for glow effect
        for i in range(3, 0, -1):
            radius = size // 2 + i * 5
            alpha = 0.3 / i
            overlay = frame.copy()
            cv2.circle(overlay, (x, y), radius, color, -1)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    def draw_radial_menu(self, frame: np.ndarray, center_x: int, center_y: int, 
                        options: List[str], selected_index: Optional[int] = None):
        """
        Draw a radial/contextual menu around a point.
        
        Args:
            frame: OpenCV frame
            center_x, center_y: Center position of menu
            options: List of menu option strings
            selected_index: Index of currently selected option
        """
        if not options:
            return
        
        menu_radius = 80
        option_radius = 30
        num_options = len(options)
        
        # Draw menu background circle
        cv2.circle(frame, (center_x, center_y), menu_radius + 20, 
                  self.colors['menu_bg'], -1)
        cv2.circle(frame, (center_x, center_y), menu_radius + 20, 
                  self.colors['menu'], 2)
        
        # Calculate angle between options
        angle_step = 2 * np.pi / num_options
        
        for i, option in enumerate(options):
            # Calculate position for this option
            angle = i * angle_step - np.pi / 2  # Start from top
            option_x = int(center_x + menu_radius * np.cos(angle))
            option_y = int(center_y + menu_radius * np.sin(angle))
            
            # Draw option circle
            if i == selected_index:
                color = self.colors['hovered']
                thickness = 3
            else:
                color = self.colors['menu']
                thickness = 1
            
            cv2.circle(frame, (option_x, option_y), option_radius, color, thickness)
            cv2.circle(frame, (option_x, option_y), option_radius, 
                      self.colors['menu_bg'], -1)
            
            # Draw option label (first letter or number)
            label = option[0].upper() if option else str(i + 1)
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            label_x = option_x - label_size[0] // 2
            label_y = option_y + label_size[1] // 2
            
            cv2.putText(
                frame, label,
                (label_x, label_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                color, 2
            )
    
    def draw_intent_feedback(self, frame: np.ndarray, intent_text: str, 
                            position: Tuple[int, int]):
        """
        Draw visual feedback for current intent.
        
        Args:
            frame: OpenCV frame
            intent_text: Text describing the intent
            position: Position to draw feedback
        """
        # Draw background
        text_size, _ = cv2.getTextSize(intent_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        bg_x = position[0] - 10
        bg_y = position[1] - text_size[1] - 10
        bg_w = text_size[0] + 20
        bg_h = text_size[1] + 20
        
        cv2.rectangle(
            frame,
            (bg_x, bg_y),
            (bg_x + bg_w, bg_y + bg_h),
            self.colors['menu_bg'],
            -1
        )
        
        # Draw text
        cv2.putText(
            frame, intent_text,
            (position[0], position[1]),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7,
            self.colors['hovered'], 2
        )
    
    def draw_hand_trail(self, frame: np.ndarray, positions: List[Tuple[int, int]]):
        """
        Draw a trail showing hand movement (for debugging/visualization).
        
        Args:
            frame: OpenCV frame
            positions: List of (x, y) positions in pixels
        """
        if len(positions) < 2:
            return
        
        # Draw trail with fading opacity
        for i in range(1, len(positions)):
            alpha = i / len(positions)
            color = tuple(int(c * alpha) for c in self.colors['hovered'])
            cv2.line(frame, positions[i-1], positions[i], color, 2)
    
    def draw_window_outline(self, frame: np.ndarray, window: window_manager.WindowInfo, 
                           is_grabbed: bool = False, is_hovered: bool = False,
                           screen_width: Optional[int] = None, screen_height: Optional[int] = None):
        """
        Draw outline of a real window on the frame.
        
        Args:
            frame: OpenCV frame
            window: WindowInfo to draw
            is_grabbed: Whether window is currently grabbed
            is_hovered: Whether window is hovered
            screen_width: Screen width in pixels (optional, uses pyautogui if not provided)
            screen_height: Screen height in pixels (optional, uses pyautogui if not provided)
        """
        import pyautogui
        if screen_width is None or screen_height is None:
            screen_width, screen_height = pyautogui.size()
        
        # Convert window position to frame coordinates
        # Note: This is approximate since frame and screen may have different sizes
        scale_x = self.frame_width / screen_width
        scale_y = self.frame_height / screen_height
        
        left = int(window.left * scale_x)
        top = int(window.top * scale_y)
        right = int(window.right * scale_x)
        bottom = int(window.bottom * scale_y)
        
        # Choose color based on state
        if is_grabbed:
            color = self.colors['grabbed']
            thickness = 4
        elif is_hovered:
            color = self.colors['hovered']
            thickness = 3
        else:
            color = self.colors['idle']
            thickness = 1
        
        # Draw rectangle outline
        cv2.rectangle(frame, (left, top), (right, bottom), color, thickness)
        
        # Draw window title
        title = window.title[:30]  # Truncate long titles
        label_size, _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        label_x = left + 5
        label_y = top - 5 if top > 20 else top + 20
        
        # Draw label background
        cv2.rectangle(
            frame,
            (label_x - 2, label_y - label_size[1] - 2),
            (label_x + label_size[0] + 2, label_y + 2),
            self.colors['menu_bg'],
            -1
        )
        
        # Draw label text
        cv2.putText(
            frame, title,
            (label_x, label_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4,
            color, 1
        )

