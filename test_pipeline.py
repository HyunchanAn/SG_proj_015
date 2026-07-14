import sys
import os

sys.path.append(os.path.abspath("demo_ui"))
from core.api_client import trigger_all_metrology_analyses_automatically

print("Testing pipeline with default HL preset...")
try:
    result = trigger_all_metrology_analyses_automatically("HL")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
