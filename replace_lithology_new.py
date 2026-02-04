#!/usr/bin/env python3
import re
import sys

file_path = 'src/core/analyzer.py'
with open(file_path, 'r') as f:
    content = f.read()

# Replace LITHOLOGY_COLUMN_NEW with LITHOLOGY_COLUMN
new_content = content.replace('LITHOLOGY_COLUMN_NEW', 'LITHOLOGY_COLUMN')

with open(file_path, 'w') as f:
    f.write(new_content)

print(f'Replaced LITHOLOGY_COLUMN_NEW with LITHOLOGY_COLUMN in {file_path}')

# Also need to replace 'LITHOLOGY_CODE' string occurrences? Let's check.
# We'll do that separately.