import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error

# Set random seed for reproducibility
np.random.seed(42)

def generate_synthetic_data(n_samples=500):
    # 4 monomers: BA, 2-EHA, MMA, AA
    # Random ratios summing to 100
    ratios = np.random.dirichlet(alpha=[10, 10, 5, 2], size=n_samples) * 100
    df = pd.DataFrame(ratios, columns=['BA', '2-EHA', 'MMA', 'AA'])
    
    # Process variables
    df['temp'] = np.random.uniform(80, 90, n_samples)
    df['time'] = np.random.uniform(4, 6, n_samples)
    
    # Real physical parameters for monomers (Tg, Surface Energy, Density)
    # Tg: BA (-54), 2-EHA (-70), MMA (105), AA (106)
    # SFE: BA (32), 2-EHA (29), MMA (41), AA (44)
    # Density: BA (0.90), 2-EHA (0.88), MMA (0.94), AA (1.05)
    phys_props = {
        'BA': [-54.0, 32.0, 0.90],
        '2-EHA': [-70.0, 29.0, 0.88],
        'MMA': [105.0, 41.0, 0.94],
        'AA': [106.0, 44.0, 1.05]
    }
    
    # Calculate bulk properties (Weighted averages)
    bulk_tg = sum(df[m] * phys_props[m][0] for m in phys_props) / 100.0
    bulk_sfe = sum(df[m] * phys_props[m][1] for m in phys_props) / 100.0
    bulk_density = sum(df[m] * phys_props[m][2] for m in phys_props) / 100.0
    
    # Target: Adhesion (non-linear relationship with bulk properties and process)
    # SFE peak around 35mN/m, lower Tg -> higher adhesion, temp/time optimal zone
    adhesion = (
        1500.0 
        - 15.0 * (bulk_tg + 30.0)**2 
        - 50.0 * (bulk_sfe - 34.0)**2
        + 200.0 * (df['temp'] - 83.0)
        - 50.0 * (df['time'] - 5.0)**2
        + np.random.normal(0, 50, n_samples) # Noise
    )
    df['adhesion'] = np.clip(adhesion, 100.0, 3000.0)
    
    return df, phys_props

# Generate mock high-dimensional embeddings for monomers (size 256 each)
def get_mock_embeddings():
    # Simulate GNN embeddings (normally 256 dimensions)
    return {
        'BA': np.random.normal(0.1, 0.2, 256),
        '2-EHA': np.random.normal(-0.1, 0.2, 256),
        'MMA': np.random.normal(0.3, 0.1, 256),
        'AA': np.random.normal(-0.2, 0.3, 256)
    }

def run_evaluation(df, phys_props, embeddings, n_train):
    n_samples = len(df)
    
    # 1. Feature Set A: Direct Embedding Concatenation
    # Concatenate raw monomer embeddings scaled by ratios
    features_a = []
    for idx, row in df.iterrows():
        # Scale each embedding by ratio
        ba_emb = row['BA'] * embeddings['BA']
        eha_emb = row['2-EHA'] * embeddings['2-EHA']
        mma_emb = row['MMA'] * embeddings['MMA']
        aa_emb = row['AA'] * embeddings['AA']
        
        # Concatenate them (1024 dimensions)
        concat_emb = np.concatenate([ba_emb, eha_emb, mma_emb, aa_emb])
        
        # Add process variables
        feat = np.append(concat_emb, [row['temp'], row['time']])
        features_a.append(feat)
        
    X_a = np.array(features_a)
    y = df['adhesion'].values
    
    # 2. Feature Set B: Physical Properties Summary
    # Weight monomer physical properties by ratios (9 dimensions total)
    features_b = []
    for idx, row in df.iterrows():
        # Weighted Tg, SFE, Density
        w_tg = sum(row[m] * phys_props[m][0] for m in phys_props) / 100.0
        w_sfe = sum(row[m] * phys_props[m][1] for m in phys_props) / 100.0
        w_density = sum(row[m] * phys_props[m][2] for m in phys_props) / 100.0
        
        feat = np.array([
            row['BA'], row['2-EHA'], row['MMA'], row['AA'],
            w_tg, w_sfe, w_density,
            row['temp'], row['time']
        ])
        features_b.append(feat)
    X_b = np.array(features_b)
    
    # Split datasets
    test_size = n_samples - n_train
    
    X_train_a, X_test_a, y_train_a, y_test_a = train_test_split(X_a, y, train_size=n_train, test_size=test_size, random_state=42)
    X_train_b, X_test_b, y_train_b, y_test_b = train_test_split(X_b, y, train_size=n_train, test_size=test_size, random_state=42)
    
    # Model 1: Ridge Regression (Linear with Regularization)
    model_a_ridge = Ridge(alpha=1.0)
    model_a_ridge.fit(X_train_a, y_train_a)
    
    model_b_ridge = Ridge(alpha=1.0)
    model_b_ridge.fit(X_train_b, y_train_b)
    
    # Model 2: RandomForest (Non-linear)
    model_a_rf = RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42)
    model_a_rf.fit(X_train_a, y_train_a)
    
    model_b_rf = RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42)
    model_b_rf.fit(X_train_b, y_train_b)
    
    # Evaluate
    results = {}
    
    for name, model, X_tr, X_te, y_tr, y_te in [
        ('Ridge - Concat (A)', model_a_ridge, X_train_a, X_test_a, y_train_a, y_test_a),
        ('Ridge - Physical (B)', model_b_ridge, X_train_b, X_test_b, y_train_b, y_test_b),
        ('RF - Concat (A)', model_a_rf, X_train_a, X_test_a, y_train_a, y_test_a),
        ('RF - Physical (B)', model_b_rf, X_train_b, X_test_b, y_train_b, y_test_b)
    ]:
        tr_pred = model.predict(X_tr)
        te_pred = model.predict(X_te)
        
        tr_r2 = r2_score(y_tr, tr_pred)
        te_r2 = r2_score(y_te, te_pred)
        te_mae = mean_absolute_error(y_te, te_pred)
        
        results[name] = {
            'Train R2': tr_r2,
            'Test R2': te_r2,
            'Test MAE': te_mae,
            'Overfitting Margin (R2 diff)': tr_r2 - te_r2
        }
        
    return results

if __name__ == "__main__":
    df, phys_props = generate_synthetic_data(500)
    embeddings = get_mock_embeddings()
    
    print("--- Case 1: Data Scarcity (Train size = 80, Test size = 420) ---")
    res_scarcity = run_evaluation(df, phys_props, embeddings, n_train=80)
    for k, v in res_scarcity.items():
        print(f"[{k}]")
        print(f"  Train R2: {v['Train R2']:.4f} | Test R2: {v['Test R2']:.4f} (MAE: {v['Test MAE']:.2f})")
        print(f"  Overfitting Margin: {v['Overfitting Margin (R2 diff)']:.4f}")
        
    print("\n--- Case 2: Ample Data (Train size = 400, Test size = 100) ---")
    res_ample = run_evaluation(df, phys_props, embeddings, n_train=400)
    for k, v in res_ample.items():
        print(f"[{k}]")
        print(f"  Train R2: {v['Train R2']:.4f} | Test R2: {v['Test R2']:.4f} (MAE: {v['Test MAE']:.2f})")
        print(f"  Overfitting Margin: {v['Overfitting Margin (R2 diff)']:.4f}")
