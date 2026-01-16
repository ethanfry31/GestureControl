"""
Object-Centric System for Iron Man Gesture Control
Manages virtual 3D objects in front of the camera
"""

from typing import List, Optional, Tuple
from enum import Enum
import math


class ObjectState(Enum):
    """State of a virtual object"""
    IDLE = "idle"
    HOVERED = "hovered"
    GRABBED = "grabbed"
    SELECTED = "selected"


class VirtualObject:
    """
    Represents a virtual object in 3D space that can be manipulated.
    
    Objects have position in normalized 3D space (0-1 for x, y, z)
    where z represents depth (0 = near camera, 1 = far)
    """
    
    def __init__(self, obj_id: str, name: str, obj_type: str = "window"):
        """
        Initialize a virtual object.
        
        Args:
            obj_id: Unique identifier for the object
            name: Display name
            obj_type: Type of object (window, app, panel, etc.)
        """
        self.id = obj_id
        self.name = name
        self.type = obj_type
        
        # Position in normalized 3D space (x, y, z)
        # x: 0 = left, 1 = right
        # y: 0 = top, 1 = bottom
        # z: 0 = near camera, 1 = far
        self.x: float = 0.5
        self.y: float = 0.5
        self.z: float = 0.3  # Default depth
        
        # State
        self.state: ObjectState = ObjectState.IDLE
        
        # Visual properties
        self.size: float = 0.1  # Size in normalized space
        self.hover_glow: bool = False
        self.grab_offset: Optional[Tuple[float, float, float]] = None  # Offset when grabbed
        
        # Metadata
        self.metadata: dict = {}
    
    def set_position(self, x: float, y: float, z: Optional[float] = None):
        """Set object position in 3D space."""
        self.x = max(0.0, min(1.0, x))
        self.y = max(0.0, min(1.0, y))
        if z is not None:
            self.z = max(0.0, min(1.0, z))
    
    def get_position(self) -> Tuple[float, float, float]:
        """Get object position."""
        return (self.x, self.y, self.z)
    
    def distance_to(self, x: float, y: float, z: float = 0.3) -> float:
        """
        Calculate 3D distance to a point.
        
        Args:
            x, y, z: Target position in normalized space
        
        Returns:
            Distance in normalized space
        """
        dx = self.x - x
        dy = self.y - y
        dz = self.z - z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def is_point_inside(self, x: float, y: float) -> bool:
        """
        Check if a 2D point is inside the object's bounds.
        
        Args:
            x, y: Point in normalized 2D space
        
        Returns:
            True if point is inside object bounds
        """
        half_size = self.size / 2
        return (abs(x - self.x) < half_size and 
                abs(y - self.y) < half_size)
    
    def update_state(self, new_state: ObjectState):
        """Update object state."""
        self.state = new_state
        self.hover_glow = (new_state == ObjectState.HOVERED or 
                          new_state == ObjectState.GRABBED)
    
    def set_grab_offset(self, hand_x: float, hand_y: float, hand_z: float):
        """Set offset when object is grabbed."""
        self.grab_offset = (
            hand_x - self.x,
            hand_y - self.y,
            hand_z - self.z
        )
    
    def clear_grab_offset(self):
        """Clear grab offset."""
        self.grab_offset = None
    
    def update_from_hand(self, hand_x: float, hand_y: float, hand_z: float):
        """
        Update object position based on hand position when grabbed.
        
        Args:
            hand_x, hand_y, hand_z: Hand position in normalized space
        """
        if self.grab_offset:
            self.x = max(0.0, min(1.0, hand_x - self.grab_offset[0]))
            self.y = max(0.0, min(1.0, hand_y - self.grab_offset[1]))
            self.z = max(0.0, min(1.0, hand_z - self.grab_offset[2]))


class ObjectManager:
    """
    Manages all virtual objects in the 3D space.
    """
    
    def __init__(self):
        """Initialize object manager."""
        self.objects: List[VirtualObject] = []
        self.selected_object: Optional[VirtualObject] = None
        self.grabbed_object: Optional[VirtualObject] = None
    
    def add_object(self, obj: VirtualObject):
        """Add an object to the scene."""
        self.objects.append(obj)
    
    def remove_object(self, obj_id: str):
        """Remove an object by ID."""
        self.objects = [obj for obj in self.objects if obj.id != obj_id]
        if self.selected_object and self.selected_object.id == obj_id:
            self.selected_object = None
        if self.grabbed_object and self.grabbed_object.id == obj_id:
            self.grabbed_object = None
    
    def find_nearest_object(self, x: float, y: float, z: float = 0.3, 
                           max_distance: float = 0.2) -> Optional[VirtualObject]:
        """
        Find the nearest object to a point in 3D space.
        
        Args:
            x, y, z: Position in normalized space
            max_distance: Maximum distance to consider
        
        Returns:
            Nearest object or None if none within range
        """
        nearest = None
        min_distance = max_distance
        
        for obj in self.objects:
            distance = obj.distance_to(x, y, z)
            if distance < min_distance:
                min_distance = distance
                nearest = obj
        
        return nearest
    
    def find_object_at_point(self, x: float, y: float) -> Optional[VirtualObject]:
        """
        Find object at a 2D point (for hover detection).
        
        Args:
            x, y: Point in normalized 2D space
        
        Returns:
            Object at point or None
        """
        # Check objects from front to back (z = 0 to 1)
        sorted_objects = sorted(self.objects, key=lambda o: o.z)
        
        for obj in sorted_objects:
            if obj.is_point_inside(x, y):
                return obj
        
        return None
    
    def grab_object(self, obj: VirtualObject, hand_x: float, hand_y: float, hand_z: float):
        """
        Grab an object with hand position.
        
        Args:
            obj: Object to grab
            hand_x, hand_y, hand_z: Hand position
        """
        if self.grabbed_object and self.grabbed_object != obj:
            # Release previously grabbed object
            self.grabbed_object.update_state(ObjectState.IDLE)
            self.grabbed_object.clear_grab_offset()
        
        self.grabbed_object = obj
        obj.update_state(ObjectState.GRABBED)
        obj.set_grab_offset(hand_x, hand_y, hand_z)
    
    def release_object(self):
        """Release currently grabbed object."""
        if self.grabbed_object:
            self.grabbed_object.update_state(ObjectState.IDLE)
            self.grabbed_object.clear_grab_offset()
            self.grabbed_object = None
    
    def update_hover(self, hand_x: float, hand_y: float):
        """
        Update hover state based on hand position.
        
        Args:
            hand_x, hand_y: Hand position in normalized 2D space
        """
        # Clear all hover states
        for obj in self.objects:
            if obj.state == ObjectState.HOVERED:
                obj.update_state(ObjectState.IDLE)
        
        # Find object at hand position (if not grabbing)
        if not self.grabbed_object:
            hovered = self.find_object_at_point(hand_x, hand_y)
            if hovered:
                hovered.update_state(ObjectState.HOVERED)
    
    def update_grabbed_object(self, hand_x: float, hand_y: float, hand_z: float):
        """
        Update grabbed object position based on hand movement.
        
        Args:
            hand_x, hand_y, hand_z: Hand position
        """
        if self.grabbed_object:
            self.grabbed_object.update_from_hand(hand_x, hand_y, hand_z)
    
    def get_all_objects(self) -> List[VirtualObject]:
        """Get all objects."""
        return self.objects.copy()

