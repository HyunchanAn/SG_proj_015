import sys
import pandas as pd
import sqlite3
import numpy as np
sys.path.append("/Users/hyunchanan/Documents/GitHub/SG_proj_010")
from src.matcher import SubstrateMatcher

# Load DB
conn = sqlite3.connect("/Users/hyunchanan/Documents/GitHub/SG_proj_010/data/substrate.db")
df = pd.read_sql_query("SELECT * FROM substrates", conn)

matcher = SubstrateMatcher(df)

# Test with our values
res = matcher.find_top_k(100.0, 320.0, 78.10, k=1)
print("Input: 100.0, 320.0, 78.10")
print(res)

res = matcher.find_top_k(100.0, 320.0, 40.0, k=1)
print("Input: 100.0, 320.0, 40.0")
print(res)
