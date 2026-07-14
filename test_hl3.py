import sys
import pandas as pd
import sqlite3
sys.path.append("/Users/hyunchanan/Documents/GitHub/SG_proj_010")
from src.matcher import SubstrateMatcher

conn = sqlite3.connect("/Users/hyunchanan/Documents/GitHub/SG_proj_010/data/substrate.db")
db_df = pd.read_sql_query("SELECT * FROM substrates", conn)
matcher = SubstrateMatcher(db_df)

print("Test 1: New V-SAMS HL output (ra=190, gloss=260, sfe=78.10)")
res = matcher.find_top_k(190.0, 260.0, 78.10, k=3)
for r in res:
    print(r)

