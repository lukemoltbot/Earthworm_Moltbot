#!/usr/bin/env python3
"""
Simple test to check imports and basic functionality.
"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

try:
    # Try to import the config module
    from core.config import COALLOG_V31_COLUMNS, LITHOLOGY_COLUMN
    print("✅ Successfully imported config module")
    print(f"  - COALLOG_V31_COLUMNS has {len(COALLOG_V31_COLUMNS)} columns")
    print(f"  - LITHOLOGY_COLUMN: {LITHOLOGY_COLUMN}")
    
    # Check the column list
    print("\nFirst 10 columns in COALLOG_V31_COLUMNS:")
    for i, col in enumerate(COALLOG_V31_COLUMNS[:10], 1):
        print(f"  {i:2d}. {col}")
    
    if len(COALLOG_V31_COLUMNS) == 37:
        print(f"\n✅ Correct number of columns: 37")
    else:
        print(f"\n❌ Wrong number of columns: {len(COALLOG_V31_COLUMNS)} (expected 37)")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")