import sys

def fix_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    with open(filename, 'w') as f:
        for i, line in enumerate(lines):
            if i >= 44:  # 0-indexed, so line 45 is index 44
                if line.startswith('    '):
                    line = line[4:]
            f.write(line)

fix_file('/Users/hyunchanan/Documents/GitHub/SG_proj_015/demo_ui/ui_components/results_panel.py')
fix_file('/Users/hyunchanan/Documents/GitHub/SG_proj_015/demo_ui/ui_components/archive_panel.py')
