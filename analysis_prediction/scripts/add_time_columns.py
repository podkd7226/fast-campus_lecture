"""
Add time columns to model datasets for time-based splitting
"""
import pandas as pd
import os

# Base path
base_path = '/Users/hyungjun/Desktop/fast campus_lecture'

# Load admissions data with time information
admissions = pd.read_csv(f'{base_path}/processed_data/core/admissions_sampled.csv')
admissions_time = admissions[['hadm_id', 'admittime', 'dischtime', 'deathtime']].copy()

# Load patients data for dod
patients = pd.read_csv(f'{base_path}/processed_data/core/patients_sampled.csv')
patients_dod = patients[['subject_id', 'dod']].copy()

# Process each dataset
datasets = [
    'essential/model_dataset_essential.csv',
    'extended/model_dataset_extended.csv',
    'comprehensive/model_dataset_comprehensive.csv'
]

for dataset_path in datasets:
    full_path = f'{base_path}/analysis_prediction/data/{dataset_path}'
    
    if os.path.exists(full_path):
        print(f"Processing {dataset_path}...")
        
        # Load dataset
        df = pd.read_csv(full_path)
        
        # Merge time columns
        df = df.merge(admissions_time, on='hadm_id', how='left')
        df = df.merge(patients_dod, on='subject_id', how='left')
        
        # Reorder columns - put time columns after ids but before other features
        id_cols = ['hadm_id', 'subject_id']
        time_cols = ['admittime', 'dischtime', 'deathtime', 'dod']
        target_cols = ['death_type', 'death_binary', 'hospital_death', 'los_hours', 'los_days']
        
        # Get other columns
        other_cols = [col for col in df.columns if col not in id_cols + time_cols + target_cols]
        
        # Reorder
        ordered_cols = id_cols + time_cols + target_cols + other_cols
        df = df[ordered_cols]
        
        # Save updated dataset
        df.to_csv(full_path, index=False)
        print(f"  - Updated {dataset_path}")
        print(f"  - Shape: {df.shape}")
        print(f"  - Columns added: {time_cols}")
        print()

print("All datasets updated with time columns!")