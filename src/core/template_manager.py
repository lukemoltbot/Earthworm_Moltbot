"""
Template Manager for Earthworm Moltbot
Manages predefined project templates for different geological project types.
"""
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from .config import DEFAULT_LITHOLOGY_RULES, RESEARCHED_LITHOLOGY_DEFAULTS
from .settings_manager import DEFAULT_SETTINGS_FILE, load_settings, save_settings


class ProjectTemplate:
    """Represents a project template with predefined settings."""
    
    def __init__(self, name: str, description: str = "", 
                 lithology_rules: List[Dict] = None,
                 workspace_layout: Dict = None,
                 default_settings: Dict = None):
        self.name = name
        self.description = description
        self.lithology_rules = lithology_rules or DEFAULT_LITHOLOGY_RULES.copy()
        self.workspace_layout = workspace_layout or {}
        self.default_settings = default_settings or {}
        self.created = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert template to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "lithology_rules": self.lithology_rules,
            "workspace_layout": self.workspace_layout,
            "default_settings": self.default_settings,
            "created": self.created.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectTemplate':
        """Create template from dictionary."""
        template = cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            lithology_rules=data.get("lithology_rules", DEFAULT_LITHOLOGY_RULES.copy()),
            workspace_layout=data.get("workspace_layout", {}),
            default_settings=data.get("default_settings", {})
        )
        
        # Parse creation timestamp
        created_str = data.get("created")
        if created_str:
            template.created = datetime.fromisoformat(created_str)
        
        return template
    
    def __str__(self) -> str:
        return f"Template(name='{self.name}', description='{self.description}')"


class TemplateManager:
    """Manages project templates stored in settings file."""
    
    def __init__(self, settings_file_path: Optional[str] = None):
        self.settings_file_path = settings_file_path or DEFAULT_SETTINGS_FILE
        self.templates: Dict[str, ProjectTemplate] = {}  # name -> Template
        self._load_templates()
        
        # Create default templates if none exist
        if not self.templates:
            self._create_default_templates()
    
    def _load_templates(self):
        """Load templates from settings file."""
        if not os.path.exists(self.settings_file_path):
            return
        
        try:
            settings = load_settings(self.settings_file_path)
            templates_data = settings.get("templates", {})
            
            for template_name, template_data in templates_data.items():
                try:
                    template = ProjectTemplate.from_dict(template_data)
                    self.templates[template_name] = template
                except Exception as e:
                    print(f"Warning: Failed to load template '{template_name}': {e}")
        except Exception as e:
            print(f"Warning: Failed to load templates from {self.settings_file_path}: {e}")
    
    def _save_templates(self):
        """Save templates to settings file."""
        try:
            # Load existing settings
            if os.path.exists(self.settings_file_path):
                with open(self.settings_file_path, 'r') as f:
                    settings = json.load(f)
            else:
                settings = {}
            
            # Convert templates to dict
            templates_dict = {}
            for name, template in self.templates.items():
                templates_dict[name] = template.to_dict()
            
            # Update settings
            settings["templates"] = templates_dict
            
            # Save back to file
            os.makedirs(os.path.dirname(self.settings_file_path), exist_ok=True)
            with open(self.settings_file_path, 'w') as f:
                json.dump(settings, f, indent=4)
                
        except Exception as e:
            print(f"Error: Failed to save templates to {self.settings_file_path}: {e}")
            raise
    
    def _create_default_templates(self):
        """Create default project templates."""
        # Coal Exploration Template
        coal_rules = [
            {'name': 'Coal', 'code': 'CO', 'gamma_min': 0, 'gamma_max': 20, 
             'density_min': 1.2, 'density_max': 1.8, 'background_color': '#000000'},
            {'name': 'Carbonaceous Mudstone', 'code': 'XM', 'gamma_min': 21, 'gamma_max': 60, 
             'density_min': 2.0, 'density_max': 2.4, 'background_color': '#2F4F4F'},
            {'name': 'Sandstone', 'code': 'SS', 'gamma_min': 61, 'gamma_max': 100, 
             'density_min': 2.4, 'density_max': 2.7, 'background_color': '#FFFF00'},
            {'name': 'Shale', 'code': 'SH', 'gamma_min': 101, 'gamma_max': 150, 
             'density_min': 2.5, 'density_max': 3.0, 'background_color': '#A9A9A9'},
            {'name': 'Not Logged', 'code': 'NL', 'gamma_min': -1, 'gamma_max': -1, 
             'density_min': -1, 'density_max': -1, 'background_color': '#E0E0E0'}
        ]
        
        coal_template = ProjectTemplate(
            name="Coal Exploration",
            description="Template optimized for coal exploration projects. Includes coal-specific lithology rules and workspace layout.",
            lithology_rules=coal_rules,
            workspace_layout={
                "default_docks": ["settings_dock", "holes_dock"],
                "default_view": "split_view",
                "preferred_tools": ["stratigraphic_column", "curve_plotter"]
            },
            default_settings={
                "smart_interbedding": True,
                "merge_thin_units": True,
                "merge_threshold": 0.1,
                "curve_thickness": 2.0
            }
        )
        
        # Mineral Exploration Template
        mineral_rules = [
            {'name': 'Ore Zone', 'code': 'OZ', 'gamma_min': 0, 'gamma_max': 30, 
             'density_min': 3.0, 'density_max': 5.0, 'background_color': '#FF4500'},
            {'name': 'Host Rock', 'code': 'HR', 'gamma_min': 31, 'gamma_max': 80, 
             'density_min': 2.5, 'density_max': 3.0, 'background_color': '#8B4513'},
            {'name': 'Alteration Zone', 'code': 'AZ', 'gamma_min': 81, 'gamma_max': 120, 
             'density_min': 2.2, 'density_max': 2.7, 'background_color': '#FFD700'},
            {'name': 'Waste Rock', 'code': 'WR', 'gamma_min': 121, 'gamma_max': 150, 
             'density_min': 2.0, 'density_max': 2.5, 'background_color': '#808080'},
            {'name': 'Not Logged', 'code': 'NL', 'gamma_min': -1, 'gamma_max': -1, 
             'density_min': -1, 'density_max': -1, 'background_color': '#E0E0E0'}
        ]
        
        mineral_template = ProjectTemplate(
            name="Mineral Exploration",
            description="Template for mineral exploration projects. Includes ore zone classification and mineral-specific rules.",
            lithology_rules=mineral_rules,
            workspace_layout={
                "default_docks": ["settings_dock", "holes_dock", "map_dock"],
                "default_view": "tabbed_view",
                "preferred_tools": ["map_window", "cross_section", "curve_plotter"]
            },
            default_settings={
                "smart_interbedding": False,
                "merge_thin_units": False,
                "fallback_classification": True,
                "curve_thickness": 1.5
            }
        )
        
        # Groundwater/Hydrogeology Template
        groundwater_rules = [
            {'name': 'Aquifer (Sand)', 'code': 'AQ', 'gamma_min': 20, 'gamma_max': 60, 
             'density_min': 2.0, 'density_max': 2.4, 'background_color': '#87CEEB'},
            {'name': 'Aquitard (Clay)', 'code': 'AT', 'gamma_min': 80, 'gamma_max': 120, 
             'density_min': 2.5, 'density_max': 2.8, 'background_color': '#8B7355'},
            {'name': 'Confining Layer', 'code': 'CL', 'gamma_min': 121, 'gamma_max': 150, 
             'density_min': 2.6, 'density_max': 3.0, 'background_color': '#696969'},
            {'name': 'Fractured Rock', 'code': 'FR', 'gamma_min': 30, 'gamma_max': 70, 
             'density_min': 2.2, 'density_max': 2.6, 'background_color': '#D2691E'},
            {'name': 'Not Logged', 'code': 'NL', 'gamma_min': -1, 'gamma_max': -1, 
             'density_min': -1, 'density_max': -1, 'background_color': '#E0E0E0'}
        ]
        
        groundwater_template = ProjectTemplate(
            name="Groundwater/Hydrogeology",
            description="Template for groundwater and hydrogeology projects. Includes aquifer classification and hydrostratigraphic rules.",
            lithology_rules=groundwater_rules,
            workspace_layout={
                "default_docks": ["settings_dock", "holes_dock", "cross_section_dock"],
                "default_view": "split_view",
                "preferred_tools": ["cross_section", "stratigraphic_column", "validation_panel"]
            },
            default_settings={
                "smart_interbedding": True,
                "merge_thin_units": True,
                "merge_threshold": 0.05,
                "curve_thickness": 1.8
            }
        )
        
        # Add default templates
        self.templates[coal_template.name] = coal_template
        self.templates[mineral_template.name] = mineral_template
        self.templates[groundwater_template.name] = groundwater_template
        
        # Save default templates
        self._save_templates()
    
    def get_template(self, name: str) -> Optional[ProjectTemplate]:
        """Get a template by name."""
        return self.templates.get(name)
    
    def get_all_templates(self) -> List[ProjectTemplate]:
        """Get all templates sorted by name."""
        templates = list(self.templates.values())
        templates.sort(key=lambda t: t.name)
        return templates
    
    def save_template(self, template: ProjectTemplate) -> bool:
        """
        Save a template.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self.templates[template.name] = template
            self._save_templates()
            return True
        except Exception as e:
            print(f"Error saving template '{template.name}': {e}")
            return False
    
    def delete_template(self, name: str) -> bool:
        """
        Delete a template by name.
        
        Returns:
            True if deleted, False if not found
        """
        if name in self.templates:
            del self.templates[name]
            self._save_templates()
            return True
        return False
    
    def template_exists(self, name: str) -> bool:
        """Check if a template with given name exists."""
        return name in self.templates
    
    def get_template_count(self) -> int:
        """Get total number of templates."""
        return len(self.templates)
    
    def apply_template(self, template_name: str, main_window) -> bool:
        """
        Apply template settings to current session.
        
        Args:
            template_name: Name of template to apply
            main_window: Main application window
        
        Returns:
            True if applied successfully, False otherwise
        """
        template = self.get_template(template_name)
        if not template:
            print(f"Template '{template_name}' not found.")
            return False
        
        try:
            # Apply lithology rules
            from .settings_manager import save_settings, load_settings
            
            # Load current settings
            current_settings = load_settings()
            
            # Update settings with template values
            current_settings["lithology_rules"] = template.lithology_rules
            
            # Apply default settings from template
            for key, value in template.default_settings.items():
                if key in current_settings:
                    current_settings[key] = value
            
            # Save updated settings
            save_settings(
                lithology_rules=current_settings["lithology_rules"],
                separator_thickness=current_settings.get("separator_thickness", 0.5),
                draw_separator_lines=current_settings.get("draw_separator_lines", True),
                curve_inversion_settings=current_settings.get("curve_inversion_settings", {}),
                curve_thickness=current_settings.get("curve_thickness", 1.5),
                use_researched_defaults=current_settings.get("use_researched_defaults", True),
                analysis_method=current_settings.get("analysis_method", "standard"),
                merge_thin_units=current_settings.get("merge_thin_units", False),
                merge_threshold=current_settings.get("merge_threshold", 0.05),
                smart_interbedding=current_settings.get("smart_interbedding", False),
                smart_interbedding_max_sequence_length=current_settings.get("smart_interbedding_max_sequence_length", 10),
                smart_interbedding_thick_unit_threshold=current_settings.get("smart_interbedding_thick_unit_threshold", 0.5),
                fallback_classification=current_settings.get("fallback_classification", False),
                workspace_state=current_settings.get("workspace"),
                theme=current_settings.get("theme", "dark")
            )
            
            # Update UI if main_window is provided
            if main_window and hasattr(main_window, 'update_settings_from_template'):
                main_window.update_settings_from_template(template)
            
            print(f"Template '{template_name}' applied successfully.")
            return True
            
        except Exception as e:
            print(f"Error applying template '{template_name}': {e}")
            return False