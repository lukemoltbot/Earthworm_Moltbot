"""
DictionaryManager class for managing CoalLog dictionaries.

This class provides a centralized interface for loading and accessing
CoalLog dictionary data with caching for performance.
"""

import pandas as pd
import os
from typing import Dict, List, Optional, Tuple
from .coallog_utils import load_coallog_dictionaries


class DictionaryManager:
    """Manages CoalLog dictionaries with caching and easy access methods."""
    
    def __init__(self, coal_log_path: Optional[str] = None):
        """
        Initialize the DictionaryManager.
        
        Args:
            coal_log_path: Path to the CoalLog Excel file. If None, will look
                          for the default file in src/assets/CoalLog v3.1 Dictionaries.xlsx
        """
        self._dictionaries: Optional[Dict[str, pd.DataFrame]] = None
        self._code_cache: Dict[str, List[Tuple[str, str]]] = {}  # category -> [(code, description)]
        self._coal_log_path = coal_log_path
        
        if not self._coal_log_path:
            # Try to find the default CoalLog file
            default_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "src", "assets", "CoalLog v3.1 Dictionaries.xlsx"
            )
            if os.path.exists(default_path):
                self._coal_log_path = default_path
            else:
                # Fallback to hardcoded sample codes
                self._initialize_fallback_dictionaries()
                return
        
        # Load dictionaries
        self._load_dictionaries()
    
    def _initialize_fallback_dictionaries(self):
        """Initialize with hardcoded sample codes when CoalLog file is missing."""
        print("WARNING: CoalLog Excel file not found. Using fallback dictionaries.")
        
        # Sample fallback dictionaries
        self._dictionaries = {
            'Litho_Type': pd.DataFrame({
                'Code': ['CO', 'SS', 'SH', 'CL', 'SI', 'GR', 'COAL', 'SAND', 'SHALE'],
                'Description': ['Coal', 'Sandstone', 'Shale', 'Clay', 'Siltstone', 
                              'Gravel', 'Coal (detailed)', 'Sandstone (detailed)', 
                              'Shale (detailed)']
            }),
            'Litho_Qual': pd.DataFrame({
                'Code': ['G', 'M', 'P', 'VG', 'EX'],
                'Description': ['Good', 'Medium', 'Poor', 'Very Good', 'Excellent']
            }),
            'Shade': pd.DataFrame({
                'Shade': ['L', 'M', 'D'],
                'Description': ['Light', 'Medium', 'Dark']
            }),
            'Hue': pd.DataFrame({
                'Hue': ['R', 'Y', 'G', 'B'],
                'Description': ['Red', 'Yellow', 'Green', 'Blue']
            }),
            'Colour': pd.DataFrame({
                'Colour': ['WH', 'GY', 'BK', 'BN'],
                'Description': ['White', 'Gray', 'Black', 'Brown']
            }),
            'Weathering': pd.DataFrame({
                'Weathering': ['FR', 'MW', 'HW'],
                'Description': ['Fresh', 'Moderately Weathered', 'Highly Weathered']
            }),
            'Est_Strength': pd.DataFrame({
                'Estimated Strength': ['VS', 'S', 'M', 'H', 'VH'],
                'Description': ['Very Soft', 'Soft', 'Medium', 'Hard', 'Very Hard']
            }),
            'Litho_Interrel': pd.DataFrame({
                'Code': ['SH', 'GR', 'IN'],
                'Description': ['Sharp', 'Gradual', 'Interbedded']
            }),
            'Bed_Spacing': pd.DataFrame({
                'Code': ['VL', 'L', 'M', 'H', 'VH'],
                'Description': ['Very Low', 'Low', 'Medium', 'High', 'Very High']
            })
        }
        
        # Build cache
        self._build_cache()
    
    def _load_dictionaries(self):
        """Load dictionaries from the CoalLog Excel file."""
        try:
            self._dictionaries = load_coallog_dictionaries(self._coal_log_path)
            self._build_cache()
            print(f"Successfully loaded dictionaries from: {self._coal_log_path}")
        except Exception as e:
            print(f"Error loading dictionaries: {e}")
            self._initialize_fallback_dictionaries()
    
    def _build_cache(self):
        """Build cache for faster access to codes and descriptions."""
        if not self._dictionaries:
            return
        
        self._code_cache.clear()
        
        for category, df in self._dictionaries.items():
            if df is None or df.empty:
                continue
            
            # Determine column names based on category
            if category in ['Litho_Type', 'Litho_Qual', 'Litho_Interrel', 'Bed_Spacing']:
                code_col = 'Code'
                desc_col = 'Description'
            elif category == 'Est_Strength':
                code_col = 'Estimated Strength'
                desc_col = 'Description'
            else:
                # Shade, Hue, Colour, Weathering
                code_col = category
                desc_col = 'Description'
            
            # Ensure columns exist
            if code_col in df.columns and desc_col in df.columns:
                codes = []
                for _, row in df.iterrows():
                    code = str(row[code_col]).strip()
                    desc = str(row[desc_col]).strip()
                    if code and desc:  # Skip empty entries
                        codes.append((code, desc))
                self._code_cache[category] = codes
    
    def get_codes_for_category(self, category: str) -> List[Tuple[str, str]]:
        """
        Get list of (code, description) tuples for a given category.
        
        Args:
            category: Dictionary category (e.g., 'Litho_Type', 'Litho_Qual')
            
        Returns:
            List of (code, description) tuples
        """
        return self._code_cache.get(category, [])
    
    def get_codes_as_strings(self, category: str) -> List[str]:
        """
        Get list of formatted strings "Description (Code)" for a given category.
        
        Args:
            category: Dictionary category
            
        Returns:
            List of formatted strings
        """
        codes = self.get_codes_for_category(category)
        return [f"{desc} ({code})" for code, desc in codes]
    
    def get_code_from_display(self, display_text: str) -> Optional[str]:
        """
        Extract code from display text "Description (Code)".
        
        Args:
            display_text: Formatted display text
            
        Returns:
            Code string or None if not found
        """
        if "(" in display_text and display_text.endswith(")"):
            return display_text.split("(")[-1].replace(")", "").strip()
        return display_text.strip()
    
    def get_description_for_code(self, category: str, code: str) -> Optional[str]:
        """
        Get description for a specific code in a category.
        
        Args:
            category: Dictionary category
            code: Code to look up
            
        Returns:
            Description string or None if not found
        """
        codes = self.get_codes_for_category(category)
        for c, desc in codes:
            if c == code:
                return desc
        return None
    
    def search_codes(self, search_term: str, categories: Optional[List[str]] = None) -> List[Tuple[str, str, str]]:
        """
        Search across dictionary categories for codes/descriptions matching search term.
        
        Args:
            search_term: Text to search for
            categories: List of categories to search (None = all categories)
            
        Returns:
            List of (category, code, description) tuples
        """
        results = []
        search_lower = search_term.lower()
        
        if categories is None:
            categories = list(self._code_cache.keys())
        
        for category in categories:
            codes = self.get_codes_for_category(category)
            for code, desc in codes:
                if (search_lower in code.lower() or 
                    search_lower in desc.lower()):
                    results.append((category, code, desc))
        
        return results
    
    def get_all_categories(self) -> List[str]:
        """Get list of all available dictionary categories."""
        return list(self._code_cache.keys())
    
    def reload(self):
        """Reload dictionaries from file."""
        if self._coal_log_path and os.path.exists(self._coal_log_path):
            self._load_dictionaries()
        else:
            print("WARNING: Cannot reload - CoalLog file not found")
    
    @property
    def is_loaded(self) -> bool:
        """Check if dictionaries are loaded."""
        return self._dictionaries is not None and len(self._code_cache) > 0


# Singleton instance for easy access
_dictionary_manager_instance = None

def get_dictionary_manager(coal_log_path: Optional[str] = None) -> DictionaryManager:
    """
    Get or create the singleton DictionaryManager instance.
    
    Args:
        coal_log_path: Path to CoalLog Excel file (only used on first call)
        
    Returns:
        DictionaryManager instance
    """
    global _dictionary_manager_instance
    if _dictionary_manager_instance is None:
        _dictionary_manager_instance = DictionaryManager(coal_log_path)
    return _dictionary_manager_instance