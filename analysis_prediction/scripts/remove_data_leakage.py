"""
Remove hospital_expire_flag from all model datasets to prevent data leakage
"""
import pandas as pd
import os

# Base path
base_path = '/Users/hyungjun/Desktop/fast campus_lecture/analysis_prediction/data'

# Process each dataset
datasets = [
    'essential/model_dataset_essential.csv',
    'extended/model_dataset_extended.csv',
    'comprehensive/model_dataset_comprehensive.csv'
]

for dataset_path in datasets:
    full_path = f'{base_path}/{dataset_path}'
    
    if os.path.exists(full_path):
        print(f"Processing {dataset_path}...")
        
        # Load dataset
        df = pd.read_csv(full_path)
        
        # Check if hospital_expire_flag exists
        if 'hospital_expire_flag' in df.columns:
            # Remove the column
            df = df.drop('hospital_expire_flag', axis=1)
            
            # Save updated dataset
            df.to_csv(full_path, index=False)
            
            print(f"  - Removed hospital_expire_flag from {dataset_path}")
            print(f"  - New shape: {df.shape}")
            print(f"  - Remaining columns: {df.shape[1]}")
        else:
            print(f"  - hospital_expire_flag not found in {dataset_path}")
        print()

print("Data leakage issue fixed!")