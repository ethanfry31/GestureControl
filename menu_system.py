"""
Radial/Contextual Menu System for Iron Man Gesture Control
"""

from typing import List, Optional, Dict, Callable
from enum import Enum


class MenuType(Enum):
    """Types of contextual menus"""
    OBJECT_MENU = "object_menu"  # Menu for objects (windows, apps)
    SYSTEM_MENU = "system_menu"  # System-level menu
    CONTEXT_MENU = "context_menu"  # Context-specific menu


class MenuOption:
    """Represents a menu option"""
    
    def __init__(self, label: str, action: Callable, icon: str = ""):
        """
        Initialize menu option.
        
        Args:
            label: Display label
            action: Function to call when selected
            icon: Optional icon character
        """
        self.label = label
        self.action = action
        self.icon = icon or label[0].upper()


class RadialMenu:
    """
    Radial/contextual menu that appears around hand position.
    """
    
    def __init__(self, menu_type: MenuType, options: List[MenuOption]):
        """
        Initialize radial menu.
        
        Args:
            menu_type: Type of menu
            options: List of menu options
        """
        self.menu_type = menu_type
        self.options = options
        self.is_open = False
        self.selected_index: Optional[int] = None
        self.position: Optional[tuple] = None  # (x, y) in normalized space
    
    def open(self, x: float, y: float):
        """Open menu at position."""
        self.is_open = True
        self.position = (x, y)
        self.selected_index = None
    
    def close(self):
        """Close menu."""
        self.is_open = False
        self.position = None
        self.selected_index = None
    
    def select_option(self, index: int):
        """
        Select a menu option by index.
        
        Args:
            index: Option index (0-based)
        """
        if 0 <= index < len(self.options):
            self.selected_index = index
    
    def execute_selected(self):
        """Execute the currently selected option."""
        if self.selected_index is not None:
            option = self.options[self.selected_index]
            option.action()
            self.close()
    
    def get_option_labels(self) -> List[str]:
        """Get list of option labels."""
        return [opt.label for opt in self.options]


class MenuManager:
    """
    Manages all menus in the system.
    """
    
    def __init__(self):
        """Initialize menu manager."""
        self.active_menu: Optional[RadialMenu] = None
        self.menu_templates: Dict[MenuType, List[MenuOption]] = {}
        self._initialize_default_menus()
    
    def _initialize_default_menus(self):
        """Initialize default menu templates."""
        # Object menu (for windows/apps)
        self.menu_templates[MenuType.OBJECT_MENU] = [
            MenuOption("Close", lambda: print("Close object")),
            MenuOption("Minimize", lambda: print("Minimize object")),
            MenuOption("Maximize", lambda: print("Maximize object")),
            MenuOption("Properties", lambda: print("Show properties"))
        ]
        
        # System menu
        self.menu_templates[MenuType.SYSTEM_MENU] = [
            MenuOption("Settings", lambda: print("Open settings")),
            MenuOption("Help", lambda: print("Show help")),
            MenuOption("Exit", lambda: print("Exit system"))
        ]
    
    def create_menu(self, menu_type: MenuType, custom_options: Optional[List[MenuOption]] = None) -> RadialMenu:
        """
        Create a menu of specified type.
        
        Args:
            menu_type: Type of menu to create
            custom_options: Optional custom options (uses template if None)
        
        Returns:
            RadialMenu instance
        """
        options = custom_options or self.menu_templates.get(menu_type, [])
        return RadialMenu(menu_type, options)
    
    def open_menu(self, menu: RadialMenu, x: float, y: float):
        """
        Open a menu at position.
        
        Args:
            menu: Menu to open
            x, y: Position in normalized space
        """
        # Close any existing menu
        if self.active_menu:
            self.active_menu.close()
        
        self.active_menu = menu
        menu.open(x, y)
    
    def close_menu(self):
        """Close the active menu."""
        if self.active_menu:
            self.active_menu.close()
            self.active_menu = None
    
    def select_menu_option(self, angle: float):
        """
        Select menu option based on angle from center.
        
        Args:
            angle: Angle in radians (0 = right, π/2 = down, π = left, 3π/2 = up)
        """
        if not self.active_menu or not self.active_menu.is_open:
            return
        
        # Normalize angle to 0-2π
        angle = angle % (2 * 3.14159)
        
        # Adjust for menu starting at top (-π/2)
        angle = (angle + 3.14159 / 2) % (2 * 3.14159)
        
        # Calculate option index
        num_options = len(self.active_menu.options)
        option_angle = 2 * 3.14159 / num_options
        index = int(angle / option_angle) % num_options
        
        self.active_menu.select_option(index)
    
    def execute_menu_action(self):
        """Execute the selected menu action."""
        if self.active_menu:
            self.active_menu.execute_selected()
            if not self.active_menu.is_open:
                self.active_menu = None

