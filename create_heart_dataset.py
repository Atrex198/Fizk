import pandas as pd
import numpy as np
from sklearn.datasets import make_classification

# Generate synthetic heart disease dataset similar to the real one
np.random.seed(42)

# Generate base classification data
X_base, y_base = make_classification(
    n_samples=50000,
    n_features=15,
    n_informative=12,
    n_redundant=3,
    n_classes=2,
    n_clusters_per_class=2,
    random_state=42
)

# Create realistic heart disease features
feature_names = [
    'HeartDisease', 'BMI', 'Smoking', 'AlcoholDrinking', 'Stroke', 'PhysicalHealth',
    'MentalHealth', 'DiffWalking', 'Sex', 'AgeCategory', 'Race', 'Diabetic',
    'PhysicalActivity', 'GenHealth', 'SleepTime', 'Asthma', 'KidneyDisease', 'SkinCancer'
]

# Create the dataframe with synthetic but realistic data
df = pd.DataFrame()

# Target variable (HeartDisease)
df['HeartDisease'] = y_base

# Continuous features
df['BMI'] = np.random.normal(28.5, 6.2, 50000).clip(15, 50)
df['PhysicalHealth'] = np.random.poisson(3.5, 50000).clip(0, 30)
df['MentalHealth'] = np.random.poisson(4.2, 50000).clip(0, 30)
df['SleepTime'] = np.random.normal(7.2, 1.4, 50000).clip(3, 12)

# Binary features (Yes/No -> 1/0)
binary_features = ['Smoking', 'AlcoholDrinking', 'Stroke', 'DiffWalking', 
                   'PhysicalActivity', 'Asthma', 'KidneyDisease', 'SkinCancer']

for feature in binary_features:
    if feature == 'Smoking':
        prob = 0.17  # ~17% smoking rate
    elif feature == 'AlcoholDrinking':
        prob = 0.06  # ~6% heavy drinking
    elif feature == 'Stroke':
        prob = 0.04  # ~4% stroke history
    elif feature == 'DiffWalking':
        prob = 0.14  # ~14% walking difficulty
    elif feature == 'PhysicalActivity':
        prob = 0.78  # ~78% physically active
    elif feature == 'Asthma':
        prob = 0.14  # ~14% asthma
    elif feature == 'KidneyDisease':
        prob = 0.04  # ~4% kidney disease
    else:  # SkinCancer
        prob = 0.05  # ~5% skin cancer
    
    df[feature] = np.random.binomial(1, prob, 50000)

# Categorical features
# Sex (0=Female, 1=Male)
df['Sex'] = np.random.binomial(1, 0.48, 50000)

# AgeCategory (0-12 representing age groups)
age_probs = [0.02, 0.03, 0.05, 0.08, 0.12, 0.15, 0.16, 0.14, 0.12, 0.08, 0.04, 0.01]
df['AgeCategory'] = np.random.choice(range(12), 50000, p=age_probs)

# Race (0-5 representing different races)
race_probs = [0.77, 0.14, 0.05, 0.02, 0.01, 0.01]
df['Race'] = np.random.choice(range(6), 50000, p=race_probs)

# Diabetic (0=No, 1=Pre-diabetic, 2=Yes)
diabetic_probs = [0.65, 0.04, 0.31]
df['Diabetic'] = np.random.choice(range(3), 50000, p=diabetic_probs)

# GenHealth (0-4 representing Poor to Excellent)
health_probs = [0.05, 0.12, 0.28, 0.35, 0.20]
df['GenHealth'] = np.random.choice(range(5), 50000, p=health_probs)

# Add some correlation with target variable for realism
heart_disease_indices = df['HeartDisease'] == 1

# People with heart disease are more likely to:
# - Be older
df.loc[heart_disease_indices, 'AgeCategory'] = np.random.choice(
    range(6, 12), sum(heart_disease_indices), p=[0.15, 0.18, 0.20, 0.17, 0.15, 0.15]
)

# - Have diabetes
df.loc[heart_disease_indices, 'Diabetic'] = np.random.choice(
    range(3), sum(heart_disease_indices), p=[0.35, 0.15, 0.50]
)

# - Have worse general health
df.loc[heart_disease_indices, 'GenHealth'] = np.random.choice(
    range(5), sum(heart_disease_indices), p=[0.15, 0.25, 0.35, 0.20, 0.05]
)

# - Have higher BMI
df.loc[heart_disease_indices, 'BMI'] = np.random.normal(30.2, 6.8, sum(heart_disease_indices)).clip(18, 50)

# - Smoke more
df.loc[heart_disease_indices, 'Smoking'] = np.random.binomial(1, 0.25, sum(heart_disease_indices))

# Save the synthetic dataset
df.to_csv('/run/media/vane/Data/Project/Fizk/heart_2020_cleaned.csv', index=False)

print(f"✅ Created synthetic heart disease dataset with {len(df)} samples")
print(f"📊 Heart Disease Distribution: {df['HeartDisease'].value_counts().to_dict()}")
print(f"📋 Features: {list(df.columns)}")
print(f"💾 Saved to: heart_2020_cleaned.csv")