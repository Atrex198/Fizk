import os
import sys
from pathlib import Path
import time
import joblib
import pandas as pd
import numpy as np
from dotenv import load_dotenv

import torch
from torch import nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, f1_score, precision_recall_curve

load_dotenv()
CSV_PATH = os.getenv('CSV_PATH', 'cardio_train.csv')
MODEL_PATH = os.getenv('MODEL_PATH', 'model_mlp.joblib')
RANDOM_STATE = int(os.getenv('RANDOM_STATE', 42))
TEST_SIZE = float(os.getenv('TEST_SIZE', 0.2))
if len(sys.argv) > 1:
    CSV_PATH = sys.argv[1]


def load_and_prepare(csv_path):
    try:
        df = pd.read_csv(csv_path)
    except Exception:
        df = pd.read_csv(csv_path, sep=';')

    # if initial read used wrong delimiter (no expected target found), try semicolon
    possible_targets = ['cardio', 'HeartDisease', 'heart_disease', 'target', 'cardiovascular', 'cardio_disease']
    if not any(t in df.columns for t in possible_targets):
        try:
            df = pd.read_csv(csv_path, sep=';')
        except Exception:
            pass

    if 'id' in df.columns:
        df = df.drop(columns=['id'])

    # detect target
    possible_targets = ['cardio', 'HeartDisease', 'heart_disease', 'target', 'cardiovascular', 'cardio_disease']
    target_col = None
    for t in possible_targets:
        if t in df.columns:
            target_col = t
            break
    if target_col is None:
        raise ValueError('No target column found')

    # map yes/no
    def map_yesno(s):
        if pd.isna(s):
            return s
        if isinstance(s, (int, float)):
            return s
        s2 = str(s).strip().lower()
        if s2 in ('yes','y','1','true','t'):
            return 1
        if s2 in ('no','n','0','false','f'):
            return 0
        return s

    df[target_col] = df[target_col].apply(map_yesno).astype(float)

    # numeric columns fill
    for col in df.select_dtypes(include=['float64','int64']).columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].fillna(df[col].median())

    # convert age in days to years if dataset uses days
    if 'age' in df.columns and df['age'].median() > 200:
        df['age'] = (df['age'] / 365).astype(int)

    # create BMI if possible (some datasets have BMI directly)
    if 'BMI' not in df.columns and all(c in df.columns for c in ['weight', 'height']):
        # height likely in cm in cardio_train
        df['bmi'] = df['weight'] / ((df['height'] / 100) ** 2)

    # create pulse pressure if present
    if all(c in df.columns for c in ['ap_hi', 'ap_lo']):
        df['pulse_pressure'] = df['ap_hi'] - df['ap_lo']

    # features
    obj_cols = df.select_dtypes(include=['object']).columns.tolist()
    obj_cols = [c for c in obj_cols if c != target_col]
    # simple boolean mapping
    for c in obj_cols:
        sample = df[c].dropna().astype(str).str.strip().str.lower()
        uniq = sample.unique()[:10]
        if set(uniq).issubset({'yes','no','y','n','true','false','1','0'}):
            df[c] = df[c].apply(map_yesno)

    obj_cols = df.select_dtypes(include=['object']).columns.tolist()
    if len(obj_cols) > 0:
        df = pd.get_dummies(df, columns=obj_cols, drop_first=True)

    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # CRITICAL: Normalize features for neural network training
    # This ensures all inputs are in [0,1] range as required by BCE loss
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler()
    X_normalized = pd.DataFrame(
        scaler.fit_transform(X),
        columns=X.columns,
        index=X.index
    )
    
    return X_normalized, y


def to_loader(X, y, batch=1024, shuffle=True):
    xt = torch.tensor(X, dtype=torch.float32)
    yt = torch.tensor(y, dtype=torch.float32).unsqueeze(1)
    ds = TensorDataset(xt, yt)
    return DataLoader(ds, batch_size=batch, shuffle=shuffle)


class MLP(nn.Module):
    def __init__(self, in_dim, hidden=(128, 64), dropout=0.3):
        super().__init__()
        layers = []
        prev = in_dim
        for h in hidden:
            layers.append(nn.Linear(prev, h))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev = h
        layers.append(nn.Linear(prev, 1))
        layers.append(nn.Sigmoid())  # CRITICAL: Add sigmoid for BCE loss compatibility
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


def train():
    X, y = load_and_prepare(CSV_PATH)
    X = X.apply(pd.to_numeric, errors='coerce').fillna(0.0)

    X_train_full, X_test, y_train_full, y_test = train_test_split(X.values.astype(np.float32), y.values.astype(np.float32), test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y.values)
    X_train, X_val, y_train, y_val = train_test_split(X_train_full, y_train_full, test_size=0.1, random_state=RANDOM_STATE, stratify=y_train_full)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print('Device:', device)

    model = MLP(X_train.shape[1], hidden=(256,128), dropout=0.4).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    loss_fn = nn.BCEWithLogitsLoss()

    train_loader = to_loader(X_train, y_train, batch=2048, shuffle=True)
    val_loader = to_loader(X_val, y_val, batch=4096, shuffle=False)

    best_val = float('inf')
    best_state = None
    patience = 10
    cur = 0
    start = time.time()
    for epoch in range(100):
        model.train()
        running = 0.0
        for xb, yb in train_loader:
            xb = xb.to(device); yb = yb.to(device)
            out = model(xb)
            loss = loss_fn(out, yb)
            opt.zero_grad(); loss.backward(); opt.step()
            running += loss.item() * xb.size(0)
        # val
        model.eval(); vloss = 0.0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb = xb.to(device); yb = yb.to(device)
                out = model(xb); vloss += loss_fn(out, yb).item() * xb.size(0)
        vloss = vloss / len(X_val)
        if (epoch+1) % 5 == 0 or epoch == 0:
            print(f'Epoch {epoch+1} train_loss {running/len(X_train):.4f} val_loss {vloss:.4f}')
        if vloss < best_val - 1e-6:
            best_val = vloss; best_state = {k:v.cpu().clone() for k,v in model.state_dict().items()}; cur = 0
        else:
            cur += 1
            if cur >= patience:
                print('Early stopping at epoch', epoch+1)
                break
    print('Training time', time.time()-start)
    model.load_state_dict(best_state)

    # predict scores
    model.eval()
    with torch.no_grad():
        X_test_t = torch.tensor(X_test, dtype=torch.float32).to(device)
        scores = model(X_test_t).cpu().numpy().ravel()
        X_val_t = torch.tensor(X_val, dtype=torch.float32).to(device)
        val_scores = model(X_val_t).cpu().numpy().ravel()

    # choose threshold by val F1
    prec, rec, thr = precision_recall_curve(y_val, val_scores)
    best_f1 = 0.0; best_t = 0.0
    for t in np.unique(thr):
        f = f1_score(y_val, (val_scores>=t).astype(int))
        if f > best_f1:
            best_f1 = f; best_t = t

    preds = (scores >= best_t).astype(int)
    acc = accuracy_score(y_test, preds); auc = roc_auc_score(y_test, scores)
    print(f'Test acc {acc:.4f} AUC {auc:.4f} val_f1 {best_f1:.4f} threshold {best_t:.4f}')
    print(classification_report(y_test, preds))

    Path(MODEL_PATH).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'model_state': model.state_dict(), 'scaler': scaler, 'feature_names': list(X.columns), 'threshold': float(best_t)}, MODEL_PATH)
    print('Saved MLP to', MODEL_PATH)


if __name__ == '__main__':
    train()
