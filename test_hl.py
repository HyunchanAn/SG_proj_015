import sys
import pandas as pd
import sqlite3
sys.path.append("/Users/hyunchanan/Documents/GitHub/SG_proj_010")
from src.matcher import SubstrateMatcher

conn = sqlite3.connect("/Users/hyunchanan/Documents/GitHub/SG_proj_010/data/substrate.db")
db_df = pd.read_sql_query("SELECT * FROM substrates", conn)
matcher = SubstrateMatcher(db_df)

# test 1: vsams output for HL
print("Test 1: V-SAMS HL output (ra=100, gloss=30, sfe=78)")
res = matcher.find_top_k(100.0, 30.0, 78.10, k=1)
print(res)

# test 2: vsams output for 2B
print("\nTest 2: V-SAMS 2B output (ra=80, gloss=200, sfe=78)")
res = matcher.find_top_k(80.0, 200.0, 78.10, k=1)
print(res)

