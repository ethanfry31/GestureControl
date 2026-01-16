"""
Intent System for Iron Man Gesture Control
Abstracts gestures into high-level intents for AI integration
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass


class IntentType(Enum):
    """Types of user intents"""
    GRAB_OBJECT = "grab_object"
    RELEASE_OBJECT = "release_object"
    HOVER_OBJECT = "hover_object"
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"
    OPEN_MENU = "open_menu"
    CLOSE_MENU = "close_menu"
    SELECT_OPTION = "select_option"
    CLICK = "click"
    DRAG = "drag"
    SCROLL = "scroll"
    ZOOM = "zoom"
    ROTATE = "rotate"
    UNKNOWN = "unknown"


@dataclass
class GestureIntent:
    """
    Represents a high-level intent derived from gestures.
    
    This abstraction allows the system to understand user intent
    rather than just raw hand movements, enabling AI integration.
    """
    intent_type: IntentType
    confidence: float = 1.0  # Confidence level (0.0 to 1.0)
    position: Optional[tuple] = None  # (x, y, z) in normalized space
    metadata: Optional[Dict[str, Any]] = None  # Additional context
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}


class IntentProcessor:
    """
    Processes raw gesture data into high-level intents.
    """
    
    def __init__(self):
        """Initialize intent processor."""
        self.last_intent: Optional[GestureIntent] = None
    
    def process_gesture(self, gesture_data: Dict[str, Any]) -> GestureIntent:
        """
        Convert raw gesture data into an intent.
        
        Args:
            gesture_data: Dictionary containing gesture information:
                - 'fist': bool
                - 'open_palm': bool
                - 'index_pointing': bool
                - 'swipe_direction': Optional[str]
                - 'position': tuple (x, y, z)
                - 'velocity': tuple (vx, vy, vz)
        
        Returns:
            GestureIntent representing the user's intent
        """
        # Extract gesture information
        is_fist = gesture_data.get('fist', False)
        is_open_palm = gesture_data.get('open_palm', False)
        is_index_pointing = gesture_data.get('index_pointing', False)
        swipe_direction = gesture_data.get('swipe_direction')
        position = gesture_data.get('position', (0.5, 0.5, 0.3))
        velocity = gesture_data.get('velocity', (0.0, 0.0, 0.0))
        
        # Priority order: grab > swipe > click > hover
        
        # 1. Grab intent (fist)
        if is_fist:
            return GestureIntent(
                intent_type=IntentType.GRAB_OBJECT,
                confidence=0.9,
                position=position,
                metadata={'velocity': velocity}
            )
        
        # 2. Release intent (open palm after grab)
        if is_open_palm and self.last_intent and self.last_intent.intent_type == IntentType.GRAB_OBJECT:
            return GestureIntent(
                intent_type=IntentType.RELEASE_OBJECT,
                confidence=0.9,
                position=position
            )
        
        # 3. Swipe intents (high-level commands)
        if swipe_direction:
            intent_map = {
                'swipe_left': IntentType.SWIPE_LEFT,
                'swipe_right': IntentType.SWIPE_RIGHT,
                'swipe_up': IntentType.SWIPE_UP,
                'swipe_down': IntentType.SWIPE_DOWN
            }
            intent_type = intent_map.get(swipe_direction, IntentType.UNKNOWN)
            if intent_type != IntentType.UNKNOWN:
                return GestureIntent(
                    intent_type=intent_type,
                    confidence=0.85,
                    position=position,
                    metadata={'direction': swipe_direction}
                )
        
        # 4. Click intent (index pointing)
        if is_index_pointing:
            return GestureIntent(
                intent_type=IntentType.CLICK,
                confidence=0.8,
                position=position
            )
        
        # 5. Hover intent (open palm, no other gestures)
        if is_open_palm:
            return GestureIntent(
                intent_type=IntentType.HOVER_OBJECT,
                confidence=0.7,
                position=position
            )
        
        # 6. Drag intent (fist with movement)
        if is_fist and velocity and (abs(velocity[0]) > 0.01 or abs(velocity[1]) > 0.01):
            return GestureIntent(
                intent_type=IntentType.DRAG,
                confidence=0.85,
                position=position,
                metadata={'velocity': velocity}
            )
        
        # Unknown intent
        return GestureIntent(
            intent_type=IntentType.UNKNOWN,
            confidence=0.0,
            position=position
        )
    
    def update_last_intent(self, intent: GestureIntent):
        """Update the last processed intent."""
        self.last_intent = intent


def intent_to_action(intent: GestureIntent) -> str:
    """
    Convert intent to a human-readable action description.
    
    Args:
        intent: GestureIntent to convert
    
    Returns:
        String description of the action
    """
    action_map = {
        IntentType.GRAB_OBJECT: "Grab nearest object",
        IntentType.RELEASE_OBJECT: "Release object",
        IntentType.HOVER_OBJECT: "Hover over object",
        IntentType.SWIPE_LEFT: "Switch to left panel/app",
        IntentType.SWIPE_RIGHT: "Switch to right panel/app",
        IntentType.SWIPE_UP: "Scroll up / Switch to upper menu",
        IntentType.SWIPE_DOWN: "Scroll down / Switch to lower menu",
        IntentType.OPEN_MENU: "Open contextual menu",
        IntentType.CLOSE_MENU: "Close menu",
        IntentType.SELECT_OPTION: "Select menu option",
        IntentType.CLICK: "Click on object",
        IntentType.DRAG: "Drag object",
        IntentType.SCROLL: "Scroll content",
        IntentType.ZOOM: "Zoom in/out",
        IntentType.ROTATE: "Rotate object",
        IntentType.UNKNOWN: "Unknown gesture"
    }
    
    return action_map.get(intent.intent_type, "Unknown action")

