#!/usr/bin/env python3
"""
Define the 37-column CoalLog v3.1 schema for Earthworm Moltbot.
Based on analysis of TEMPLATE.xlsx and current implementation.
"""

# Current 14 columns in lithology_table.py
current_columns = [
    'From', 'To', 'Thick', 'Litho', 'Qual',
    'Shade', 'Hue', 'Colour', 'Weath', 'Str',
    'Rec Seq', 'Inter-rel', 'Percent', 'Bed Sp'
]

# Current internal column names from lithology_table.py
current_internal_columns = [
    'from_depth', 'to_depth', 'thickness', 'LITHOLOGY_CODE', 'lithology_qualifier',
    'shade', 'hue', 'colour', 'weathering', 'estimated_strength',
    'record_sequence', 'inter_relationship', 'percentage', 'bed_spacing'
]

# Based on TEMPLATE.xlsx analysis, here are 37 core CoalLog v3.1 columns
# Grouped by category for organization
coallog_v31_columns = {
    # Depth/Thickness columns (3)
    'depth': ['From Depth', 'To Depth', 'Recovered Thickness'],
    
    # Identification columns (7)
    'identification': ['Record Sequence Flag', 'Seam', 'Ply', 'Horizon', 
                      'Sample Purpose', 'Lithology Sample Number', 'Interval Status'],
    
    # Lithology description columns (12)
    'lithology': ['Lithology', 'Lithology Qualifier', 'Lithology %', 
                  'Shade', 'Hue', 'Colour', 
                  'Adjective 1', 'Adjective 2', 'Adjective 3', 'Adjective 4',
                  'Interrelationship', 'Lithology Descriptor'],
    
    # Geotechnical columns (6)
    'geotechnical': ['Weathering', 'Estimated Strength', 'Bed Spacing',
                     'Core State', 'Mechanical State', 'Texture'],
    
    # Structural/Defect columns (5)
    'structural': ['Defect Type', 'Intact', 'Defect Spacing', 
                   'Defect Dip', 'Bedding Dip'],
    
    # Sedimentology columns (3)
    'sedimentology': ['Basal Contact', 'Sed. Feature 1', 'Sed. Feature 2'],
    
    # Mineralogy columns (3)
    'mineralogy': ['Mineral / Fossil', 'Mineral Association', 'Abundance'],
    
    # Additional columns (2)
    'additional': ['Gas', 'Comments']
}

# Flatten the dictionary to get all 37 columns
all_columns = []
for category, columns in coallog_v31_columns.items():
    all_columns.extend(columns)

print(f"Total columns defined: {len(all_columns)}")
print("\n37-column CoalLog v3.1 Schema:")
for i, col in enumerate(all_columns, 1):
    print(f"{i:2d}. {col}")

# Map to internal Python-friendly column names
# This converts display names to valid Python variable names
internal_names = []
for col in all_columns:
    # Convert to lowercase, replace spaces and special chars with underscores
    internal = col.lower().replace(' ', '_').replace('.', '').replace('/', '_').replace('-', '_')
    internal_names.append(internal)

print("\n\nInternal column names (Python-friendly):")
for i, (display, internal) in enumerate(zip(all_columns, internal_names), 1):
    print(f"{i:2d}. {display:30s} -> {internal}")

# Check which columns already exist in current implementation
print("\n\nMapping current 14 columns to new 37-column schema:")
current_to_new_map = {}
for i, current in enumerate(current_columns):
    # Try to find matching column in new schema
    found = False
    for new_col in all_columns:
        if current.lower() in new_col.lower() or new_col.lower() in current.lower():
            current_to_new_map[current] = new_col
            found = True
            break
    if not found:
        current_to_new_map[current] = f"NEW: {current}"
        
for current, new in current_to_new_map.items():
    print(f"{current:15s} -> {new}")

print(f"\n\nSummary:")
print(f"- Current columns: {len(current_columns)}")
print(f"- New 37-column schema: {len(all_columns)}")
print(f"- Columns to add: {len(all_columns) - len(current_columns)}")