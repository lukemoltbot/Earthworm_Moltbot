#!/usr/bin/env python3
"""
Continuous monitor for Development Plan 2 (2026-02-03) progress.
This script will be called by the subagent to check progress and send updates.
Monitors Phases 1-5 only (ignores previous Phase 5 & 6 from old plan).
"""

import time
import re
from datetime import datetime

def parse_roadmap(filepath):
    """Parse the new roadmap file and return progress data for Phases 1-5."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return None
    
    # Find progress summary table
    table_start = content.find('| Phase | Tasks Completed | Total Tasks | Completion |')
    if table_start == -1:
        return None
    
    # Get table lines
    lines = content[table_start:].split('\n')
    phase_data = {}
    
    for line in lines:
        # Skip lines that don't start with '|'
        if not line.startswith('|'):
            continue
        # Split by '|' and clean cells
        cells = [cell.strip() for cell in line.split('|')[1:-1]]  # exclude empty first/last due to leading/trailing '|'
        if len(cells) != 4:
            continue
        # Remove ** markers
        cells = [re.sub(r'\*+', '', cell) for cell in cells]
        
        phase_cell = cells[0]
        tasks_cell = cells[1]
        total_cell = cells[2]
        percent_cell = cells[3]
        
        # Parse phase number
        if phase_cell == 'Overall':
            phase_key = 'overall'
        elif phase_cell.startswith('Phase'):
            # Extract number
            match = re.search(r'Phase\s*(\d+)', phase_cell)
            if not match:
                continue
            phase_num = int(match.group(1))
            if phase_num < 1 or phase_num > 5:
                continue  # ignore other phases
            phase_key = phase_num
        else:
            continue
        
        # Parse tasks completed (format "2/2" or "3")
        if '/' in tasks_cell:
            completed = int(tasks_cell.split('/')[0])
        else:
            completed = int(tasks_cell)
        
        total = int(total_cell)
        
        # Parse percentage (remove % sign)
        percent_match = re.search(r'(\d+)', percent_cell)
        percent = int(percent_match.group(1)) if percent_match else 0
        
        phase_data[phase_key] = {
            'completed': completed,
            'total': total,
            'percent': percent,
            'remaining': total - completed
        }
    
    # Also extract "Active Sub-agents" line if present
    active_match = re.search(r'\*\*Active Sub-agents:\*\*\s*(\d+)\s*\(([^)]+)\)', content)
    active_agents = None
    if active_match:
        active_agents = active_match.group(2)
    
    # Extract last commit info
    commit_match = re.search(r'\*\*Last Commit:\*\*\s*([^\n]+)', content)
    last_commit = commit_match.group(1) if commit_match else 'Unknown'
    
    return {
        'phases': phase_data,
        'active_agents': active_agents,
        'last_commit': last_commit
    }

def create_update_message(progress):
    """Create a formatted update message for Development Plan 2."""
    current_time = datetime.now().strftime("%H:%M")
    
    message = f"**Development Plan 2 Progress Update** ({current_time})\n\n"
    
    phases = progress.get('phases', {})
    overall = phases.get('overall', {})
    
    # Add overall progress
    if overall:
        message += f"**Overall Progress:** {overall['percent']}% ({overall['completed']}/{overall['total']} tasks)\n"
        message += f"**Remaining Tasks:** {overall['remaining']}\n\n"
    
    # Add each phase
    for phase_num in sorted([p for p in phases.keys() if isinstance(p, int)]):
        p = phases[phase_num]
        message += f"**Phase {phase_num}:** {p['percent']}% ({p['completed']}/{p['total']} tasks)"
        if p['remaining'] > 0:
            message += f" – {p['remaining']} task{'s' if p['remaining'] > 1 else ''} remaining"
        message += "\n"
    
    # Add active agents if any
    if progress.get('active_agents'):
        message += f"\n**Active:** {progress['active_agents']}\n"
    
    # Add last commit
    message += f"\n**Latest:** {progress.get('last_commit', 'Unknown')}\n"
    
    return message

def check_and_report():
    """Check progress and return message if update should be sent."""
    roadmap_path = "/Users/lukemoltbot/clawd/Earthworm_Moltbot/DEVELOPMENT_PLAN_2026_02_03_ROADMAP.md"
    
    progress = parse_roadmap(roadmap_path)
    if not progress or 'phases' not in progress:
        return None
    
    message = create_update_message(progress)
    
    # Check if all phases are complete (Phase 1-5 at 100%)
    all_complete = True
    phases = progress['phases']
    for phase_num in range(1, 6):
        if phase_num not in phases or phases[phase_num]['percent'] < 100:
            all_complete = False
            break
    
    return message, all_complete

if __name__ == "__main__":
    # Test the functions
    result = check_and_report()
    if result:
        message, done = result
        print("Test message:")
        print(message)
        print(f"Done: {done}")
    else:
        print("Failed to check progress")