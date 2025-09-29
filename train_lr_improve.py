import os
import joblib
import time
import numpy as np
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

import torch
from torch import nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, classification_report

load_dotenv()
CSV_PATH = os.getenv('CSV_PATH', 'cardio_train.csv')
MODEL_PATH = os.getenv('MODEL_PATH', 'model_improved.joblib')
RANDOM_STATE = int(os.getenv('RANDOM_STATE', 42))
TEST_SIZE = float(os.getenv('TEST_SIZE', 0.2))


def load_and_engineer(path):
    df = pd.read_csv(path, sep=';')
    if 'id' in df.columns:
        df = df.drop(columns=['id'])
    if 'age' in df.columns and df['age'].median() > 200:
        df['age'] = (df['age'] / 365).astype(int)
    for col in ['height', 'weight', 'ap_hi', 'ap_lo']:
        if col in df.columns:
            df[col] = df[col].replace({0: np.nan})
            df[col] = df[col].fillna(df[col].median())
    if all(c in df.columns for c in ['weight', 'height']):
        df['bmi'] = df['weight'] / ((df['height'] / 100) ** 2)
    if all(c in df.columns for c in ['ap_hi', 'ap_lo']):
        df['pulse_pressure'] = df['ap_hi'] - df['ap_lo']
        df['ap_ratio'] = df['ap_hi'] / (df['ap_lo'] + 1e-6)

    # engineered: age squared, age*bmi
    if 'age' in df.columns:
        df['age_sq'] = df['age'] ** 2
    if all(c in df.columns for c in ['age', 'bmi']):
        df['age_bmi'] = df['age'] * df['bmi']

    # simple age buckets
    if 'age' in df.columns:
        df['age_bin'] = pd.cut(df['age'], bins=[0,30,40,50,60,200], labels=False)

    X = df.drop(columns=['cardio'])
    y = df['cardio'].astype(float)
    return X, y


def to_loader(X, y, batch=256, shuffle=True):
    xt = torch.tensor(X, dtype=torch.float32)
    yt = torch.tensor(y, dtype=torch.float32).unsqueeze(1)
    ds = TensorDataset(xt, yt)
    return DataLoader(ds, batch_size=batch, shuffle=shuffle)


class LinearModel(nn.Module):
    def __init__(self, n):
        super().__init__()
        self.linear = nn.Linear(n, 1)
    def forward(self, x):
        return self.linear(x)


def train_single(X_tr, y_tr, X_val, y_val, params, device):
    model = LinearModel(X_tr.shape[1]).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=params['lr'], weight_decay=params['weight_decay'])
    loss_fn = nn.BCEWithLogitsLoss()
    train_loader = to_loader(X_tr, y_tr, batch=256, shuffle=True)
    val_loader = to_loader(X_val, y_val, batch=1024, shuffle=False)
    best = {'loss': 1e9, 'state': None}
    patience = 20
    cur_p = 0
    for epoch in range(300):
        model.train()
        for xb, yb in train_loader:
            xb = xb.to(device); yb = yb.to(device)
            pred = model(xb)
            loss = loss_fn(pred, yb)
            if params.get('l1', 0) > 0:
                l1 = 0.0
                for p in model.parameters():
                    l1 = l1 + p.abs().sum()
                loss = loss + params['l1'] * l1
            opt.zero_grad(); loss.backward(); opt.step()
        # val
        model.eval(); vloss = 0.0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb = xb.to(device); yb = yb.to(device)
                pred = model(xb); vloss += loss_fn(pred, yb).item() * xb.size(0)
        vloss = vloss / len(X_val)
        if vloss < best['loss'] - 1e-6:
            best['loss'] = vloss; best['state'] = {k:v.cpu().clone() for k,v in model.state_dict().items()}; cur_p = 0
        else:
            cur_p += 1
            if cur_p >= patience:
                break
    model.load_state_dict(best['state'])
    return model, best['loss']


def evaluate_ensemble(models, X, device):
    xt = torch.tensor(X, dtype=torch.float32).to(device)
    preds = []
    with torch.no_grad():
        for m in models:
            m.to(device); m.eval(); preds.append(torch.sigmoid(m(xt)).cpu().numpy().ravel())
    avgp = np.mean(preds, axis=0)
    return avgp


def run():
    X, y = load_and_engineer(CSV_PATH)
    cat_cols = [c for c in ['gender','cholesterol','gluc','smoke','alco','active','age_bin'] if c in X.columns]
    X = pd.get_dummies(X, columns=cat_cols, drop_first=True)
    X = X.apply(pd.to_numeric, errors='coerce').fillna(0.0)

    X_train_full, X_test, y_train_full, y_test = train_test_split(X.values.astype(np.float32), y.values.astype(np.float32), test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y.values)
    X_train, X_val, y_train, y_val = train_test_split(X_train_full, y_train_full, test_size=0.1, random_state=RANDOM_STATE, stratify=y_train_full)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    param_grid = [
        {'lr':1e-3, 'weight_decay':1e-4, 'l1':0.0},
        {'lr':5e-4, 'weight_decay':1e-4, 'l1':0.0},
        {'lr':1e-3, 'weight_decay':1e-5, 'l1':0.0},
        {'lr':5e-4, 'weight_decay':1e-5, 'l1':1e-6},
        {'lr':1e-3, 'weight_decay':1e-5, 'l1':1e-6},
    ]

    results = []
    for params in param_grid:
        print('Training with', params)
        model, vloss = train_single(X_train, y_train, X_val, y_val, params, device)
        # evaluate on test
        p = evaluate_ensemble([model], X_test, device)
        # select threshold by maximizing F1 on val
        pv = evaluate_ensemble([model], X_val, device)
        from sklearn.metrics import precision_recall_curve
        prec, rec, thr = precision_recall_curve(y_val, pv)
        best_f1 = 0; best_t = 0
        for t in np.unique(thr):
            f = f1_score(y_val, (pv>=t).astype(int))
            if f>best_f1: best_f1=f; best_t=t
        test_preds = (p>=best_t).astype(int)
        acc = accuracy_score(y_test, test_preds)
        auc = roc_auc_score(y_test, p)
        print('Params', params, 'val_loss', vloss, 'best_t', best_t, 'acc', acc, 'auc', auc, 'f1_val', best_f1)
        results.append({'params':params,'model':model,'acc':acc,'auc':auc,'f1_val':best_f1,'threshold':best_t})

    # try bagging using top 3 configs
    results_sorted = sorted(results, key=lambda x: x['acc'], reverse=True)
    top = results_sorted[:3]
    print('Top configs accs', [r['acc'] for r in top])

    # train bagged ensemble
    bag_models = []
    n_bag = 5
    for i in range(n_bag):
        # bootstrap
        idx = np.random.RandomState(RANDOM_STATE + i).choice(len(X_train), size=len(X_train), replace=True)
        Xb = X_train[idx]; yb = y_train[idx]
        # use best params
        params = top[0]['params']
        m, _ = train_single(Xb, yb, X_val, y_val, params, device)
        bag_models.append(m)
    pbag = evaluate_ensemble(bag_models, X_test, device)
    # threshold from val bag
    pvbag = evaluate_ensemble(bag_models, X_val, device)
    prec, rec, thr = precision_recall_curve(y_val, pvbag)
    best_f1 = 0; best_t = 0
    for t in np.unique(thr):
        f = f1_score(y_val, (pvbag>=t).astype(int))
        if f>best_f1: best_f1=f; best_t=t
    predsbag = (pbag>=best_t).astype(int)
    accbag = accuracy_score(y_test, predsbag); aucbag = roc_auc_score(y_test, pbag)
    print('Bagging acc', accbag, 'auc', aucbag, 'f1_val', best_f1)

    # save best single and bag model metadata
    best_single = max(results, key=lambda x: x['acc'])
    Path(MODEL_PATH).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'best_single':best_single, 'bag_models_state':[m.state_dict() for m in bag_models], 'scaler':scaler, 'feature_names': X.columns.tolist()}, MODEL_PATH)
    print('Saved experiment results to', MODEL_PATH)


if __name__ == '__main__':
    run()
