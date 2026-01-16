"""
Object Controller for Iron Man Gesture Control
Manages object manipulation and 3D space interactions
Now controls REAL Windows windows instead of virtual objects
"""

from typing import Optional, Tuple
from object import ObjectManager, VirtualObject
from intents import GestureIntent, IntentType
from menu_system import MenuManager, MenuType
import window_manager
import utils


class ObjectController:
    """
    Main controller for object-centric gesture interactions.
    """
    
    def __init__(self, frame_width: int, frame_height: int):
        """
        Initialize object controller.
        
        Args:
            frame_width: Video frame width
            frame_height: Video frame height
        """
        self.object_manager = ObjectManager()
        self.menu_manager = MenuManager()
        self.window_manager = window_manager.WindowManager()
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # Hand position tracking (normalized 0-1)
        self.hand_x: float = 0.5
        self.hand_y: float = 0.5
        self.hand_z: float = 0.3  # Depth estimate
        
        # Track grabbed window
        self.grabbed_window: Optional[window_manager.WindowInfo] = None
        self.grab_offset: Optional[Tuple[float, float]] = None
    
    def update_hand_position(self, x: float, y: float, z: Optional[float] = None):
        """
        Update hand position in 3D space.
        
        Args:
            x, y: Normalized position (0-1)
            z: Optional depth (0-1), estimated if not provided
        """
        self.hand_x = max(0.0, min(1.0, x))
        self.hand_y = max(0.0, min(1.0, y))
        if z is not None:
            self.hand_z = max(0.0, min(1.0, z))
        else:
            # Estimate depth based on hand size or other factors
            # For now, use a default
            self.hand_z = 0.3
    
    def process_intent(self, intent: GestureIntent):
        """
        Process a gesture intent and update object states.
        
        Args:
            intent: GestureIntent to process
        """
        if intent.position:
            self.update_hand_position(*intent.position)
        
        # Handle different intent types
        if intent.intent_type == IntentType.GRAB_OBJECT:
            self._handle_grab()
        
        elif intent.intent_type == IntentType.RELEASE_OBJECT:
            self._handle_release()
        
        elif intent.intent_type == IntentType.HOVER_OBJECT:
            self._handle_hover()
        
        elif intent.intent_type == IntentType.OPEN_MENU:
            self._handle_open_menu()
        
        elif intent.intent_type == IntentType.CLOSE_MENU:
            self._handle_close_menu()
        
        elif intent.intent_type == IntentType.DRAG:
            self._handle_drag()
        
        elif intent.intent_type in [IntentType.SWIPE_LEFT, IntentType.SWIPE_RIGHT,
                                    IntentType.SWIPE_UP, IntentType.SWIPE_DOWN]:
            self._handle_swipe(intent.intent_type)
    
    def _handle_grab(self):
        """Handle grab intent - grab REAL window."""
        # Find nearest real window
        nearest_window = self.window_manager.find_nearest_window(
            self.hand_x, self.hand_y, max_distance=0.25
        )
        
        if nearest_window:
            self.grabbed_window = nearest_window
            # Calculate offset from window center
            window_x, window_y = nearest_window.get_normalized_position(
                self.window_manager.screen_width, 
                self.window_manager.screen_height
            )
            self.grab_offset = (
                self.hand_x - window_x,
                self.hand_y - window_y
            )
            # Bring window to front
            self.window_manager.bring_window_to_front(nearest_window)
            print(f"Grabbed window: {nearest_window.title}")
    
    def _handle_release(self):
        """Handle release intent - release REAL window."""
        if self.grabbed_window:
            print(f"Released window: {self.grabbed_window.title}")
            self.grabbed_window = None
            self.grab_offset = None
    
    def _handle_hover(self):
        """Handle hover intent - highlight window under hand."""
        # Find window at hand position
        window = self.window_manager.find_window_at_position(self.hand_x, self.hand_y)
        # Visual feedback will be handled in main loop
        pass
    
    def _handle_drag(self):
        """Handle drag intent - move REAL window."""
        if self.grabbed_window and self.grab_offset:
            # Calculate target position (accounting for grab offset)
            target_x = self.hand_x - self.grab_offset[0]
            target_y = self.hand_y - self.grab_offset[1]
            
            # Move the real window
            self.window_manager.move_window(self.grabbed_window, target_x, target_y)
    
    def _handle_open_menu(self):
        """Handle open menu intent - show menu for window."""
        # Find window at hand position
        window = self.window_manager.find_window_at_position(self.hand_x, self.hand_y)
        
        if window:
            # Create menu with window-specific actions
            from menu_system import MenuOption
            options = [
                MenuOption("Close", lambda w=window: self.window_manager.close_window(w)),
                MenuOption("Minimize", lambda w=window: self.window_manager.minimize_window(w)),
                MenuOption("Maximize", lambda w=window: self.window_manager.maximize_window(w)),
                MenuOption("Bring to Front", lambda w=window: self.window_manager.bring_window_to_front(w))
            ]
            menu = self.menu_manager.create_menu(MenuType.OBJECT_MENU, options)
            self.menu_manager.open_menu(menu, self.hand_x, self.hand_y)
    
    def _handle_close_menu(self):
        """Handle close menu intent."""
        self.menu_manager.close_menu()
    
    def _handle_swipe(self, swipe_type: IntentType):
        """Handle swipe intents (high-level commands)."""
        # Swipes are handled by actions module
        # This is just a placeholder for object-specific swipe handling
        pass
    
    def get_windows(self):
        """Get all real windows."""
        return self.window_manager.get_all_windows()
    
    def get_grabbed_window(self):
        """Get currently grabbed window."""
        return self.grabbed_window
    
    def get_active_menu(self):
        """Get the active menu if any."""
        return self.menu_manager.active_menu
    
    def get_window_at_position(self, x: float, y: float):
        """Get window at normalized position."""
        return self.window_manager.find_window_at_position(x, y)

