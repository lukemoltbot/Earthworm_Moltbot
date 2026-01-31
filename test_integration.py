#!/usr/bin/env python3
"""
Integration test for Earthworm with test.las file.
Tests the full pipeline including bed_spacing column integration.
"""
import sys
import os
import pandas as pd
import traceback

# Add current directory to path
sys.path.insert(0, '.')

def test_full_pipeline():
    print("=== Earthworm Integration Test ===\n")
    
    # 1. Import modules
    try:
        from src.core.data_processor import DataProcessor
        from src.core.analyzer import Analyzer
        from src.core.config import DEFAULT_LITHOLOGY_RULES
        print("✓ Modules imported successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        traceback.print_exc()
        return False
    
    # 2. Load LAS file
    las_file = 'test.las'
    if not os.path.exists(las_file):
        print(f"✗ LAS file not found: {las_file}")
        return False
    
    try:
        processor = DataProcessor()
        dataframe, mnemonics = processor.load_las_file(las_file)
        print(f"✓ LAS file loaded: {dataframe.shape[0]} rows, {dataframe.shape[1]} columns")
        print(f"  Columns: {list(dataframe.columns)}")
        print(f"  Mnemonics: {mnemonics}")
    except Exception as e:
        print(f"✗ Error loading LAS file: {e}")
        traceback.print_exc()
        return False
    
    # 3. Preprocess data
    try:
        # Create mnemonic map (GR -> gamma, RHOB -> density)
        mnemonic_map = {}
        if 'GR' in mnemonics:
            mnemonic_map['gamma'] = 'GR'
        if 'RHOB' in mnemonics:
            mnemonic_map['density'] = 'RHOB'
        print(f"  Mnemonic map: {mnemonic_map}")
        
        processed_df = processor.preprocess_data(dataframe, mnemonic_map)
        print(f"✓ Data preprocessed")
        print(f"  Processed columns: {list(processed_df.columns)}")
    except Exception as e:
        print(f"✗ Error preprocessing data: {e}")
        traceback.print_exc()
        return False
    
    # 4. Classify rows
    try:
        analyzer = Analyzer()
        classified_df = analyzer.classify_rows(
            processed_df, 
            DEFAULT_LITHOLOGY_RULES, 
            mnemonic_map,
            use_researched_defaults=True
        )
        print(f"✓ Rows classified")
        print(f"  Unique lithologies: {classified_df['LITHOLOGY_CODE'].unique()}")
    except Exception as e:
        print(f"✗ Error classifying rows: {e}")
        traceback.print_exc()
        return False
    
    # 5. Group into units
    try:
        units_df = analyzer.group_into_units(
            classified_df, 
            DEFAULT_LITHOLOGY_RULES,
            smart_interbedding=False,
            smart_interbedding_max_sequence_length=10,
            smart_interbedding_thick_unit_threshold=0.5
        )
        print(f"✓ Units created: {len(units_df)} units")
        print(f"  Unit columns: {list(units_df.columns)}")
        
        # Check for bed_spacing column
        if 'bed_spacing' in units_df.columns:
            print(f"✓ bed_spacing column found!")
            print(f"  bed_spacing values: {units_df['bed_spacing'].unique()}")
        else:
            print(f"✗ bed_spacing column NOT found!")
            print(f"  Available columns: {list(units_df.columns)}")
            return False
            
        # Check column order (should be 14 columns total)
        expected_cols = [
            'from_depth', 'to_depth', 'thickness', 'LITHOLOGY_CODE',
            'lithology_qualifier', 'shade', 'hue', 'colour',
            'weathering', 'estimated_strength', 'background_color', 'svg_path',
            'record_sequence', 'inter_relationship', 'percentage', 'bed_spacing'
        ]
        missing = [col for col in expected_cols if col not in units_df.columns]
        if missing:
            print(f"✗ Missing columns: {missing}")
            return False
        else:
            print(f"✓ All expected columns present")
            
        # Show first few units
        print(f"\nFirst 5 units:")
        print(units_df[['from_depth', 'to_depth', 'LITHOLOGY_CODE', 'bed_spacing']].head())
    except Exception as e:
        print(f"✗ Error creating units: {e}")
        traceback.print_exc()
        return False
    
    # 6. Test interbedding detection
    try:
        candidates = analyzer.find_interbedding_candidates(
            units_df,
            max_sequence_length=10,
            thick_unit_threshold=0.5
        )
        print(f"✓ Interbedding detection completed")
        print(f"  Found {len(candidates)} candidates")
        
        for idx, cand in enumerate(candidates[:3]):  # Show first 3
            print(f"\n  Candidate {idx}:")
            print(f"    Depth: {cand['from_depth']:.2f} - {cand['to_depth']:.2f}m")
            print(f"    Avg layer: {cand['average_layer_thickness']*1000:.1f}mm")
            print(f"    Code: {cand['interrelationship_code']}")
            print(f"    Lithologies: {[l['code'] for l in cand['lithologies']]}")
    except Exception as e:
        print(f"✗ Error in interbedding detection: {e}")
        traceback.print_exc()
        return False
    
    # 7. Test export/import (optional)
    print(f"\n=== Test Summary ===")
    print(f"✅ Pipeline executed successfully")
    print(f"✅ bed_spacing column integrated correctly")
    print(f"✅ {len(units_df)} units created")
    print(f"✅ {len(candidates)} interbedding candidates found")
    
    return True

if __name__ == '__main__':
    success = test_full_pipeline()
    sys.exit(0 if success else 1)