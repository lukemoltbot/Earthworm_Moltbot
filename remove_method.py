#!/usr/bin/env python3
import sys

with open('src/ui/main_window.py', 'r') as f:
    lines = f.readlines()

# Find start and end of setup_settings_tab method
start = None
for i, line in enumerate(lines):
    if line.strip() == 'def setup_settings_tab(self):':
        start = i
        break

if start is None:
    print("Method not found")
    sys.exit(1)

# Find next method at same indentation level
end = None
for i in range(start + 1, len(lines)):
    if lines[i].strip() and not lines[i].startswith(' ' * 8):
        # Check if it's a method definition (starts with 'def ')
        if lines[i].startswith('    def '):
            end = i
            break

if end is None:
    end = len(lines)

print(f"Removing lines {start+1} to {end}")  # +1 for 1-based line numbers
del lines[start:end]

with open('src/ui/main_window.py', 'w') as f:
    f.writelines(lines)

print("Done")