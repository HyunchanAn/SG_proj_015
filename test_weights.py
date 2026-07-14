import sys
import pandas as pd
import sqlite3
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# Load DB
conn = sqlite3.connect("/Users/hyunchanan/Documents/GitHub/SG_proj_010/data/substrate.db")
db_df = pd.read_sql_query("SELECT * FROM substrates", conn)

scaler = MinMaxScaler()
features = ['Ra_MD', 'Gloss_MD', 'SFE_MD']
scaler.fit(db_df[features])
db_normalized = scaler.transform(db_df[features])

input_ra, input_gloss, input_sfe = 100.0, 320.0, 78.10
input_vector = np.array([[input_ra, input_gloss, input_sfe]])
input_norm = scaler.transform(input_vector)

# without weights
dist_old = np.linalg.norm(db_normalized - input_norm, axis=1)
sim_old = np.clip(100 * np.exp(-dist_old), 0, 100)

# with weights
weights = np.array([0.45, 0.45, 0.1])
# We multiply difference by sqrt(weights) so that squared difference is multiplied by weight
diff = db_normalized - input_norm
dist_new = np.sqrt(np.sum((diff ** 2) * weights, axis=1))
sim_new = np.clip(100 * np.exp(-dist_new), 0, 100)

top_idx_old = np.argsort(dist_old)[0]
top_idx_new = np.argsort(dist_new)[0]

print("Old Sim:", sim_old[top_idx_old])
print("New Sim:", sim_new[top_idx_new])

