"""
Curve Settings Template Manager - Manages curve configuration templates for cross-hole synchronization.

This module provides:
1. Save curve configurations as templates
2. Load and apply templates to different holes
3. Template management (create, update, delete)
4. Foundation for cross-hole synchronization
"""

import json
import os
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, List, Any, Optional


class CurveSettingsTemplate:
    """Represents a curve settings template."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.curve_configs = []  # List of curve configurations
        self.metadata = {
            'created_date': '',
            'modified_date': '',
            'author': '',
            'version': '1.0'
        }
        
    def add_curve_config(self, config: Dict[str, Any]) -> None:
        """Add a curve configuration to the template."""
        self.curve_configs.append(config)
        
    def remove_curve_config(self, curve_name: str) -> bool:
        """Remove a curve configuration by name."""
        for i, config in enumerate(self.curve_configs):
            if config.get('name') == curve_name:
                self.curve_configs.pop(i)
                return True
        return False
        
    def update_curve_config(self, curve_name: str, updates: Dict[str, Any]) -> bool:
        """Update a curve configuration."""
        for config in self.curve_configs:
            if config.get('name') == curve_name:
                config.update(updates)
                return True
        return False
        
    def get_curve_config(self, curve_name: str) -> Optional[Dict[str, Any]]:
        """Get a curve configuration by name."""
        for config in self.curve_configs:
            if config.get('name') == curve_name:
                return config.copy()
        return None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary for serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'curve_configs': self.curve_configs,
            'metadata': self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CurveSettingsTemplate':
        """Create template from dictionary."""
        template = cls(data['name'], data.get('description', ''))
        template.curve_configs = data.get('curve_configs', [])
        template.metadata = data.get('metadata', {})
        return template


class CurveSettingsTemplateManager(QObject):
    """Manages curve settings templates for cross-hole synchronization."""
    
    # Signals
    templateSaved = pyqtSignal(str, dict)  # template_name, template_data
    templateLoaded = pyqtSignal(str, dict)  # template_name, template_data
    templateDeleted = pyqtSignal(str)  # template_name
    templateApplied = pyqtSignal(str, list)  # template_name, curve_configs
    
    def __init__(self, templates_dir: Optional[str] = None):
        super().__init__()
        
        # Templates directory
        if templates_dir is None:
            templates_dir = os.path.expanduser('~/earthworm_project-master/curve_templates')
        
        self.templates_dir = templates_dir
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Loaded templates
        self.templates: Dict[str, CurveSettingsTemplate] = {}
        
        # Load existing templates
        self.load_all_templates()
        
    def load_all_templates(self) -> None:
        """Load all templates from the templates directory."""
        self.templates.clear()
        
        if not os.path.exists(self.templates_dir):
            return
            
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                template_path = os.path.join(self.templates_dir, filename)
                try:
                    with open(template_path, 'r') as f:
                        data = json.load(f)
                        template = CurveSettingsTemplate.from_dict(data)
                        self.templates[template.name] = template
                except Exception as e:
                    print(f"Error loading template {filename}: {e}")
    
    def save_template(self, template: CurveSettingsTemplate) -> bool:
        """Save a template to disk."""
        try:
            # Update metadata
            import time
            template.metadata['modified_date'] = time.ctime()
            if 'created_date' not in template.metadata or not template.metadata['created_date']:
                template.metadata['created_date'] = time.ctime()
            
            # Save to file
            filename = f"{template.name.replace(' ', '_').lower()}.json"
            template_path = os.path.join(self.templates_dir, filename)
            
            with open(template_path, 'w') as f:
                json.dump(template.to_dict(), f, indent=2)
            
            # Update in-memory cache
            self.templates[template.name] = template
            
            # Emit signal
            self.templateSaved.emit(template.name, template.to_dict())
            return True
            
        except Exception as e:
            print(f"Error saving template {template.name}: {e}")
            return False
    
    def create_template_from_curves(self, name: str, curve_configs: List[Dict[str, Any]], 
                                   description: str = "") -> CurveSettingsTemplate:
        """Create a template from current curve configurations."""
        template = CurveSettingsTemplate(name, description)
        
        # Add curve configurations
        for config in curve_configs:
            # Create a clean copy with only relevant settings
            clean_config = {
                'name': config.get('name', ''),
                'column': config.get('column', ''),
                'visible': config.get('visible', True),
                'color': config.get('color', '#0000FF'),
                'line_style': config.get('line_style', 'solid'),
                'line_width': config.get('line_width', 1.0),
                'inverted': config.get('inverted', False),
                'y_axis': config.get('y_axis', 'left'),
                'display_mode': config.get('display_mode', 'line')
            }
            template.add_curve_config(clean_config)
        
        return template
    
    def get_template(self, name: str) -> Optional[CurveSettingsTemplate]:
        """Get a template by name."""
        return self.templates.get(name)
    
    def get_all_templates(self) -> List[CurveSettingsTemplate]:
        """Get all templates."""
        return list(self.templates.values())
    
    def get_template_names(self) -> List[str]:
        """Get all template names."""
        return list(self.templates.keys())
    
    def delete_template(self, name: str) -> bool:
        """Delete a template."""
        if name not in self.templates:
            return False
            
        try:
            # Delete file
            filename = f"{name.replace(' ', '_').lower()}.json"
            template_path = os.path.join(self.templates_dir, filename)
            
            if os.path.exists(template_path):
                os.remove(template_path)
            
            # Remove from cache
            del self.templates[name]
            
            # Emit signal
            self.templateDeleted.emit(name)
            return True
            
        except Exception as e:
            print(f"Error deleting template {name}: {e}")
            return False
    
    def apply_template(self, template_name: str, target_curves: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply a template to target curves.
        
        Args:
            template_name: Name of template to apply
            target_curves: List of target curve configurations
            
        Returns:
            Updated curve configurations
        """
        template = self.get_template(template_name)
        if not template:
            return target_curves
        
        # Create mapping of curve names to configurations
        template_configs = {cfg['name']: cfg for cfg in template.curve_configs}
        
        # Apply template settings to target curves
        updated_curves = []
        for target_config in target_curves:
            curve_name = target_config.get('name', '')
            if curve_name in template_configs:
                # Merge template settings with target config
                template_config = template_configs[curve_name]
                merged_config = target_config.copy()
                
                # Apply template settings (don't overwrite column or name)
                for key, value in template_config.items():
                    if key not in ['name', 'column']:
                        merged_config[key] = value
                
                updated_curves.append(merged_config)
            else:
                # Keep target config as-is
                updated_curves.append(target_config.copy())
        
        # Emit signal
        self.templateApplied.emit(template_name, updated_curves)
        return updated_curves
    
    def export_template(self, template_name: str, export_path: str) -> bool:
        """Export a template to a specific path."""
        template = self.get_template(template_name)
        if not template:
            return False
            
        try:
            with open(export_path, 'w') as f:
                json.dump(template.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting template {template_name}: {e}")
            return False
    
    def import_template(self, import_path: str) -> Optional[CurveSettingsTemplate]:
        """Import a template from a file."""
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)
                template = CurveSettingsTemplate.from_dict(data)
                
                # Save to templates directory
                if self.save_template(template):
                    return template
                return None
                
        except Exception as e:
            print(f"Error importing template from {import_path}: {e}")
            return None


# Default templates for common workflows
def create_default_templates(manager: CurveSettingsTemplateManager) -> None:
    """Create default curve settings templates."""
    
    # Template 1: Standard Geological Logging
    standard_template = CurveSettingsTemplate(
        name="Standard Geological Logging",
        description="Standard settings for geological logging with gamma, resistivity, and density curves"
    )
    
    standard_template.add_curve_config({
        'name': 'Gamma',
        'column': 'GR',
        'visible': True,
        'color': '#FF0000',  # Red
        'line_style': 'solid',
        'line_width': 1.5,
        'inverted': False,
        'y_axis': 'left',
        'display_mode': 'line'
    })
    
    standard_template.add_curve_config({
        'name': 'Resistivity',
        'column': 'RES',
        'visible': True,
        'color': '#0000FF',  # Blue
        'line_style': 'solid',
        'line_width': 1.5,
        'inverted': False,
        'y_axis': 'right',
        'display_mode': 'line'
    })
    
    standard_template.add_curve_config({
        'name': 'Density',
        'column': 'DEN',
        'visible': True,
        'color': '#00FF00',  # Green
        'line_style': 'solid',
        'line_width': 1.5,
        'inverted': False,
        'y_axis': 'left',
        'display_mode': 'line'
    })
    
    manager.save_template(standard_template)
    
    # Template 2: Coal Quality Analysis
    coal_template = CurveSettingsTemplate(
        name="Coal Quality Analysis",
        description="Settings for coal quality analysis with ash, sulfur, and calorific value"
    )
    
    coal_template.add_curve_config({
        'name': 'Ash Content',
        'column': 'ASH',
        'visible': True,
        'color': '#8B4513',  # Brown
        'line_style': 'dashed',
        'line_width': 2.0,
        'inverted': False,
        'y_axis': 'left',
        'display_mode': 'line'
    })
    
    coal_template.add_curve_config({
        'name': 'Sulfur Content',
        'column': 'SULF',
        'visible': True,
        'color': '#FF4500',  # OrangeRed
        'line_style': 'dotted',
        'line_width': 2.0,
        'inverted': False,
        'y_axis': 'right',
        'display_mode': 'line'
    })
    
    coal_template.add_curve_config({
        'name': 'Calorific Value',
        'column': 'CV',
        'visible': True,
        'color': '#FFD700',  # Gold
        'line_style': 'solid',
        'line_width': 2.0,
        'inverted': False,
        'y_axis': 'left',
        'display_mode': 'line'
    })
    
    manager.save_template(coal_template)
    
    # Template 3: Geophysics Focus
    geophysics_template = CurveSettingsTemplate(
        name="Geophysics Focus",
        description="Geophysics-focused view with multiple resistivity curves"
    )
    
    geophysics_template.add_curve_config({
        'name': 'Shallow Resistivity',
        'column': 'RES_SHALLOW',
        'visible': True,
        'color': '#1E90FF',  # DodgerBlue
        'line_style': 'solid',
        'line_width': 1.0,
        'inverted': False,
        'y_axis': 'left',
        'display_mode': 'line'
    })
    
    geophysics_template.add_curve_config({
        'name': 'Medium Resistivity',
        'column': 'RES_MEDIUM',
        'visible': True,
        'color': '#0000CD',  # MediumBlue
        'line_style': 'dashed',
        'line_width': 1.0,
        'inverted': False,
        'y_axis': 'left',
        'display_mode': 'line'
    })
    
    geophysics_template.add_curve_config({
        'name': 'Deep Resistivity',
        'column': 'RES_DEEP',
        'visible': True,
        'color': '#000080',  # Navy
        'line_style': 'dash_dot',
        'line_width': 1.0,
        'inverted': False,
        'y_axis': 'left',
        'display_mode': 'line'
    })
    
    manager.save_template(geophysics_template)


# Factory function
def create_curve_settings_template_manager(templates_dir: Optional[str] = None) -> CurveSettingsTemplateManager:
    """Create and initialize a curve settings template manager."""
    manager = CurveSettingsTemplateManager(templates_dir)
    
    # Create default templates if none exist
    if not manager.get_all_templates():
        create_default_templates(manager)
    
    return manager