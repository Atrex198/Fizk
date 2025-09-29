import tkinter as tk
from tkinter import ttk
from model_utils import load_artifacts, prepare_input
from dotenv import load_dotenv
import os

load_dotenv()
THRESHOLD = float(os.getenv('THRESHOLD', 0.5))


class HeartApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Heart Disease Predictor')
        self.geometry('420x600')

        self.model, self.scaler, self.columns = load_artifacts()

        # Define input fields based on expected base features
        # base features from dataset
        self.fields = ['age', 'gender', 'height', 'weight', 'ap_hi', 'ap_lo', 'cholesterol', 'gluc', 'smoke', 'alco', 'active']

        self.vars = {}
        row = 0
        for f in self.fields:
            tk.Label(self, text=f).grid(row=row, column=0, sticky='w', padx=8, pady=6)
            v = tk.StringVar()
            entry = ttk.Entry(self, textvariable=v)
            entry.grid(row=row, column=1, padx=8, pady=6)
            self.vars[f] = v
            row += 1

        ttk.Button(self, text='Predict', command=self.predict).grid(row=row, column=0, columnspan=2, pady=12)
        row += 1
        self.result_lbl = tk.Label(self, text='Result will appear here', font=('Arial', 12, 'bold'))
        self.result_lbl.grid(row=row, column=0, columnspan=2, pady=12)

    def predict(self):
        try:
            user_inputs = {}
            for k, v in self.vars.items():
                val = v.get().strip()
                if val == '':
                    self.result_lbl.config(text=f'Missing: {k}')
                    return
                # cast numeric fields
                if k in ['age', 'height', 'weight', 'ap_hi', 'ap_lo']:
                    user_inputs[k] = float(val)
                else:
                    user_inputs[k] = int(val)

            # if age seems in years but model was trained on years it's fine. If user gives years, we accept.
            x = prepare_input(user_inputs, self.columns)
            x_scaled = self.scaler.transform(x)
            prob = self.model.predict_proba(x_scaled)[0][1]
            pred = int(prob >= THRESHOLD)
            text = f'Probability of heart disease: {prob:.3f} -> Prediction: {pred}'
            self.result_lbl.config(text=text)
        except Exception as e:
            self.result_lbl.config(text=f'Error: {e}')


if __name__ == '__main__':
    app = HeartApp()
    app.mainloop()
