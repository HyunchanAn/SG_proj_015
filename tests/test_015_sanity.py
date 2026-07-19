import os
import sys

# Ensure module path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_cli_import():
    try:
        import cli_operator
        assert cli_operator.BASE_DIR is not None
        assert "SG_proj_001" in cli_operator.modules
    except ImportError as e:
        assert False, f"Failed to import cli_operator: {e}"

def test_visualize_masks_syntax():
    # Only checking if it compiles/parses without syntax errors, 
    # we don't execute it to avoid heavy PyTorch/SAM2 initialization in CI.
    import ast
    filepath = os.path.join(os.path.dirname(__file__), '..', 'visualize_masks.py')
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    try:
        ast.parse(source)
    except SyntaxError as e:
        assert False, f"Syntax error in visualize_masks.py: {e}"
