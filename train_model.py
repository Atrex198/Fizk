import os
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from dotenv import load_dotenv

import torch
from torch import nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.preprocessing import StandardScaler
import time

load_dotenv()

CSV_PATH = os.getenv('CSV_PATH', 'cardio_train.csv')
MODEL_PATH = os.getenv('MODEL_PATH', 'model.joblib')
RANDOM_STATE = int(os.getenv('RANDOM_STATE', 42))
TEST_SIZE = float(os.getenv('TEST_SIZE', 0.2))

import sys
# allow override from command-line argument
if len(sys.argv) > 1:
    CSV_PATH = sys.argv[1]


def load_and_prepare(csv_path: str):
    # try to read csv (detect delimiter automatically if possible)
    try:
        df = pd.read_csv(csv_path)
    except Exception:
        df = pd.read_csv(csv_path, sep=';')

    # drop common id
    if 'id' in df.columns:
        df = df.drop(columns=['id'])

    # detect target column from common names
    possible_targets = ['cardio', 'HeartDisease', 'heart_disease', 'target', 'cardiovascular', 'cardio_disease']
    target_col = None
    for t in possible_targets:
        if t in df.columns:
            target_col = t
            break
    if target_col is None:
        raise ValueError('No target column found in CSV; expected one of: ' + ','.join(possible_targets))

    # map common Yes/No or similar to 1/0
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

    # basic cleaning for numeric-like columns
    for col in df.select_dtypes(include=['float64','int64']).columns:
        # replace impossible zeros for known fields later if needed
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].fillna(df[col].median())

    # create pulse pressure if pressures present
    if all(c in df.columns for c in ['ap_hi', 'ap_lo']):
        df['pulse_pressure'] = df['ap_hi'] - df['ap_lo']

    # if BMI not present but weight/height are, compute
    if 'BMI' not in df.columns and all(c in df.columns for c in ['weight', 'height']):
        df['bmi'] = df['weight'] / ((df['height'] / 100) ** 2)

    # convert common categorical yes/no columns to 0/1 via map
    obj_cols = df.select_dtypes(include=['object']).columns.tolist()
    # don't include target if it is object (we already converted it)
    obj_cols = [c for c in obj_cols if c != target_col]

    # convert obvious boolean strings
    for c in obj_cols:
        sample = df[c].dropna().astype(str).str.strip().str.lower()
        uniq = sample.unique()[:10]
        if set(uniq).issubset({'yes','no','y','n','true','false','1','0'}):
            df[c] = df[c].apply(map_yesno)

    # after mapping, update object columns list and one-hot encode remaining objects
    obj_cols = df.select_dtypes(include=['object']).columns.tolist()
    if len(obj_cols) > 0:
        df = pd.get_dummies(df, columns=obj_cols, drop_first=True)

    X = df.drop(columns=[target_col])
    y = df[target_col]
    return X, y


def to_tensor_loader(X: np.ndarray, y: np.ndarray, batch_size=256, shuffle=True):
    xt = torch.tensor(X, dtype=torch.float32)
    yt = torch.tensor(y, dtype=torch.float32).unsqueeze(1)
    ds = TensorDataset(xt, yt)
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle)


class LinearModel(nn.Module):
    def __init__(self, n_in):
        super().__init__()
        self.linear = nn.Linear(n_in, 1)

    def forward(self, x):
        return self.linear(x)


def train():
    X, y = load_and_prepare(CSV_PATH)

    # simple encoding: one-hot for candidate categoricals
    cat_cols = [c for c in ['gender', 'cholesterol', 'gluc', 'smoke', 'alco', 'active'] if c in X.columns]
    X = pd.get_dummies(X, columns=cat_cols, drop_first=True)

    base_columns = X.columns.tolist()

    # ensure numeric matrix (after get_dummies some columns can be object if mixed types)
    X = X.apply(pd.to_numeric, errors='coerce')
    X = X.fillna(0.0)
    # split train / test
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X.values.astype(np.float32), y.values.astype(np.float32), test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y.values
    )
    # hold out a small validation set from train for threshold selection & early stopping
    val_frac = 0.1
    if X_train_full.shape[0] > 50:
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_full, y_train_full, test_size=val_frac, random_state=RANDOM_STATE, stratify=y_train_full
        )
    else:
        X_train, X_val, y_train, y_val = X_train_full, X_test, y_train_full, y_test

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print('Using device:', device)

    # scale features (fit on training)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)

    train_loader = to_tensor_loader(X_train, y_train, batch_size=256, shuffle=True)
    val_loader = to_tensor_loader(X_val, y_val, batch_size=1024, shuffle=False)

    model = LinearModel(X_train.shape[1]).to(device)
    # use Adam with weight_decay for L2 regularization
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    loss_fn = nn.BCEWithLogitsLoss()

    epochs = 200
    best_val_loss = float('inf')
    patience = 15
    cur_patience = 0
    start = time.time()
    for epoch in range(epochs):
        model.train()
        running = 0.0
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)
            pred = model(xb)
            loss = loss_fn(pred, yb)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            running += loss.item() * xb.size(0)

        # validation loss
        model.eval()
        v_running = 0.0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb = xb.to(device)
                yb = yb.to(device)
                pred = model(xb)
                vloss = loss_fn(pred, yb)
                v_running += vloss.item() * xb.size(0)
        train_loss = running / len(X_train)
        val_loss = v_running / len(X_val)
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f'Epoch {epoch+1}/{epochs} train loss: {train_loss:.6f} val loss: {val_loss:.6f}')

        # early stopping
        if val_loss < best_val_loss - 1e-6:
            best_val_loss = val_loss
            cur_patience = 0
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            cur_patience += 1
            if cur_patience >= patience:
                print('Early stopping')
                break
    elapsed = time.time() - start
    print(f'Training completed in {elapsed:.1f}s')

    # load best weights
    model.load_state_dict(best_state)

    # evaluate raw scores on test set
    model.eval()
    with torch.no_grad():
        X_test_t = torch.tensor(X_test, dtype=torch.float32).to(device)
        scores = model(X_test_t).cpu().numpy().ravel()

    # choose threshold on validation by maximizing F1 (use val set)
    from sklearn.metrics import precision_recall_curve, f1_score
    with torch.no_grad():
        X_val_t = torch.tensor(X_val, dtype=torch.float32).to(device)
        val_scores = model(X_val_t).cpu().numpy().ravel()
    precisions, recalls, thresholds = precision_recall_curve(y_val, val_scores)
    best_f1 = 0.0
    best_thresh = 0.0
    for t in np.unique(thresholds):
        preds = (val_scores >= t).astype(int)
        f1 = f1_score(y_val, preds)
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = t

    preds = (scores >= best_thresh).astype(int)
    acc = accuracy_score(y_test, preds)
    auc = roc_auc_score(y_test, scores)
    print(f'Test accuracy (threshold {best_thresh:.6f}): {acc:.4f}, F1 (val): {best_f1:.4f}, AUC: {auc:.4f}')
    print(classification_report(y_test, preds))

    # save model weights and metadata
    weights = model.linear.weight.detach().cpu().numpy().ravel()
    bias = float(model.linear.bias.detach().cpu().numpy())
    Path(MODEL_PATH).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'weights': weights, 'bias': bias, 'threshold': float(best_thresh), 'feature_names': base_columns, 'scaler': scaler}, MODEL_PATH)
    print('Saved linear model and scaler to', MODEL_PATH)


if __name__ == '__main__':
    train()
