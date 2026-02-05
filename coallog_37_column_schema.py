#!/usr/bin/env python3
"""
Definitive 37-column CoalLog v3.1 schema for Earthworm Moltbot.
Based on industry standards and TEMPLATE.xlsx analysis.
"""

# 37-column CoalLog v3.1 schema in correct order
# This is the industry standard column order
COALLOG_V31_COLUMNS = [
    # 1-3: Depth information
    ('from_depth', 'From Depth'),
    ('to_depth', 'To Depth'),
    ('recovered_thickness', 'Recovered Thickness'),
    
    # 4-10: Borehole identification
    ('record_sequence_flag', 'Record Sequence Flag'),
    ('seam', 'Seam'),
    ('ply', 'Ply'),
    ('horizon', 'Horizon'),
    ('sample_purpose', 'Sample Purpose'),
    ('lithology_sample_number', 'Lithology Sample Number'),
    ('interval_status', 'Interval Status'),
    
    # 11-22: Lithology description
    ('lithology', 'Lithology'),
    ('lithology_qualifier', 'Lithology Qualifier'),
    ('lithology_percent', 'Lithology %'),
    ('shade', 'Shade'),
    ('hue', 'Hue'),
    ('colour', 'Colour'),
    ('adjective_1', 'Adjective 1'),
    ('adjective_2', 'Adjective 2'),
    ('adjective_3', 'Adjective 3'),
    ('adjective_4', 'Adjective 4'),
    ('interrelationship', 'Interrelationship'),
    ('lithology_descriptor', 'Lithology Descriptor'),
    
    # 23-28: Geotechnical properties
    ('weathering', 'Weathering'),
    ('estimated_strength', 'Estimated Strength'),
    ('bed_spacing', 'Bed Spacing'),
    ('core_state', 'Core State'),
    ('mechanical_state', 'Mechanical State'),
    ('texture', 'Texture'),
    
    # 29-33: Structural features
    ('defect_type', 'Defect Type'),
    ('intact', 'Intact'),
    ('defect_spacing', 'Defect Spacing'),
    ('defect_dip', 'Defect Dip'),
    ('bedding_dip', 'Bedding Dip'),
    
    # 34-35: Sedimentology
    ('basal_contact', 'Basal Contact'),
    ('sedimentary_feature', 'Sedimentary Feature'),
    
    # 36-37: Mineralogy
    ('mineral_fossil', 'Mineral / Fossil'),
    ('abundance', 'Abundance'),
    
    # Note: Gas and Comments are often included but may be part of extended schema
    # For strict 37-column compliance, we're omitting them
]

# Verify we have exactly 37 columns
assert len(COALLOG_V31_COLUMNS) == 37, f"Expected 37 columns, got {len(COALLOG_V31_COLUMNS)}"

if __name__ == "__main__":
    
    print("37-column CoalLog v3.1 Schema (Industry Standard Order):")
    print("=" * 60)
    for i, (internal_name, display_name) in enumerate(COALLOG_V31_COLUMNS, 1):
        print(f"{i:2d}. {display_name:30s} (internal: {internal_name})")
    
    # Current columns mapping
    current_columns = [
        ('from_depth', 'From'),
        ('to_depth', 'To'),
        ('thickness', 'Thick'),
        ('LITHOLOGY_CODE', 'Litho'),  # Note: different name
        ('lithology_qualifier', 'Qual'),
        ('shade', 'Shade'),
        ('hue', 'Hue'),
        ('colour', 'Colour'),
        ('weathering', 'Weath'),
        ('estimated_strength', 'Str'),
        ('record_sequence', 'Rec Seq'),  # Note: different name
        ('inter_relationship', 'Inter-rel'),  # Note: different name
        ('percentage', 'Percent'),  # Note: different name
        ('bed_spacing', 'Bed Sp')
    ]
    
    print("\n\nCurrent 14-column to 37-column mapping:")
    print("=" * 60)
    for internal, display in current_columns:
        # Find matching column in new schema
        found = False
        for new_internal, new_display in COALLOG_V31_COLUMNS:
            if internal == new_internal or internal.replace('_', ' ') in new_display.lower():
                print(f"✓ {display:15s} -> {new_display:30s} (maps directly)")
                found = True
                break
            elif display.lower() in new_display.lower() or new_display.lower() in display.lower():
                print(f"≈ {display:15s} -> {new_display:30s} (similar)")
                found = True
                break
        
        if not found:
            # Check for special cases
            if internal == 'LITHOLOGY_CODE':
                print(f"→ {display:15s} -> Lithology                (LITHOLOGY_CODE -> lithology)")
            elif internal == 'record_sequence':
                print(f"→ {display:15s} -> Record Sequence Flag     (record_sequence -> record_sequence_flag)")
            elif internal == 'inter_relationship':
                print(f"→ {display:15s} -> Interrelationship        (inter_relationship -> interrelationship)")
            elif internal == 'percentage':
                print(f"→ {display:15s} -> Lithology %             (percentage -> lithology_percent)")
            else:
                print(f"? {display:15s} -> [No direct match]")
    
    print("\n\nImplementation notes:")
    print("-" * 60)
    print("1. ✅ lithology_table.py headers and column mappings updated (37-column)")
    print("2. ✅ pandas_model.py handles all 37 columns (generic model)")
    print("3. ✅ analyzer.py creates DataFrames with all 37 columns")
    print("4. ✅ Backward compatibility maintained with existing data")
    print("5. ⚠️ Dictionary mappings need verification for new dictionary columns")
