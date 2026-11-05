import pandas as pd
import numpy as np

# Load data
df = pd.read_excel('ref-des-medicaments-cnops-2014 2.xlsx', sheet_name=0)

# Encode target: G=1 (générique), P=0 (princeps)
df['target'] = (df['PRINCEPS_GENERIQUE'] == 'G').astype(int)

# Select features: PPV (prix), DOSAGE1 (dosage), TAUX_REMBOURSEMENT (taux de remboursement)
df['DOSAGE1_NUM'] = pd.to_numeric(df['DOSAGE1'], errors='coerce')

# Check for missing values
print("Missing values per column:")
print(df[['PPV', 'DOSAGE1_NUM', 'TAUX_REMBOURSEMENT', 'target']].isnull().sum())

# Check value ranges
print("\nFeature statistics:")
print(df[['PPV', 'DOSAGE1_NUM', 'TAUX_REMBOURSEMENT']].describe())

# Check PPV format (may have € or other chars)
print("\nPPV sample values:")
print(df['PPV'].head(10).tolist())

# Check if we can convert PPV to numeric
df['PPV_NUM'] = pd.to_numeric(df['PPV'].astype(str).str.replace(',', '.').str.replace('€', '').str.replace(' ', ''), errors='coerce')

# Convert TAUX_REMBOURSEMENT to numeric (remove % sign)
df['TAUX_REMBOURSEMENT_NUM'] = pd.to_numeric(df['TAUX_REMBOURSEMENT'].astype(str).str.replace('%', ''), errors='coerce')

print("\nPPV_NUM sample values:")
print(df['PPV_NUM'].head(10))

print("\nTAUX_REMBOURSEMENT_NUM sample values:")
print(df['TAUX_REMBOURSEMENT_NUM'].head(10))

# Correlation with target
print("\nCorrelation with target:")
for col in ['PPV_NUM', 'DOSAGE1_NUM', 'TAUX_REMBOURSEMENT_NUM']:
    corr = df[col].corr(df['target'])
    print(f"  {col}: {corr}")

# Clean data - remove rows with missing values in key columns
df_clean = df.dropna(subset=['PPV_NUM', 'DOSAGE1_NUM', 'TAUX_REMBOURSEMENT_NUM', 'target'])
print(f"\nClean dataset shape: {df_clean.shape}")

# Save cleaned data for later use
df_clean.to_csv('data/medicaments_clean.csv', index=False)
print("Clean data saved to data/medicaments_clean.csv")