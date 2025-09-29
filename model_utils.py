import os
import joblib
from dotenv import load_dotenv
import numpy as np
import pandas as pd

load_dotenv()
MODEL_PATH = os.getenv('MODEL_PATH', 'model.joblib')


def load_artifacts():
    data = joblib.load(MODEL_PATH)
    return data['model'], data.get('base_columns', []), data.get('feature_names', [])


def prepare_input(user_inputs: dict, base_columns: list, feature_names: list):
    """
    Build a single-row DataFrame from raw user inputs (base features), then rely on the saved pipeline
    to transform it. Returns a DataFrame row matching the pipeline's expected inputs (before pipeline).
    """
    # Build row with base columns present during training
    row = pd.DataFrame([{k: user_inputs.get(k, np.nan) for k in base_columns}])
    # return row (pipeline will handle encoding/scaling when predict is called)
    return row
