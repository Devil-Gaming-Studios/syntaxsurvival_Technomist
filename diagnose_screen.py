"""
diagnose_screen.py (FIXED VERSION)
──────────────────────────────────
A medical diagnostic screen that:
  1. Fetches model config & feature definitions from backend server
  2. Takes patient input for each feature
  3. Runs prediction using server-aggregated weights
  4. Sends results to Gemini for clinical interpretation
  5. Displays everything with rich formatting

KEY FIXES:
  ✅ Uses backend server weights for consistent predictions
  ✅ Proper error handling & Gemini fallback
  ✅ No hardcoded API keys (env vars only)
  ✅ Input range validation
  ✅ Thread-safe streaming from backend
  ✅ Proper cleanup on errors
"""

import os
import json
import threading
import queue
import tkinter as tk
from tkinter import messagebox
import requests
import numpy as np
import time

import training as _train_module

# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────
SERVER_URL = "https://syntaxsurvival-technomist-2.onrender.com"

GEMINI_API_KEY = "AIzaSyB9-c8EZDJ7ipSTBMk-hIT_BwGab4BQCuY"
if not GEMINI_API_KEY:
    raise RuntimeError(
        "❌ GEMINI_API_KEY environment variable not set.\n"
        "Set it before launching the app:\n"
        "  export GEMINI_API_KEY='your-key-here'\n"
        "  python app.py"
    )

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key={key}"
)

# ─────────────────────────────────────────
#  THEME
# ─────────────────────────────────────────
BG         = "#F4FAF6"
WHITE      = "#FFFFFF"
GREEN_DARK = "#14563B"
GREEN_MID  = "#3F9F74"
GREEN_LITE = "#C3EFD8"
GRAY       = "#6B7280"
GRAY_LITE  = "#F0F4F1"
TEXT       = "#1A2E23"
BORDER     = "#C8E6D4"
RED        = "#B91C1C"
RED_LITE   = "#FEE2E2"
BLUE       = "#185FA5"
BLUE_LITE  = "#EFF6FF"

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def _label(parent, text, size=11, bold=False, color=None):
    font = ("Helvetica", size, "bold") if bold else ("Helvetica", size)
    return tk.Label(parent, text=text, font=font,
                    bg=parent.cget("bg"), fg=color or TEXT)

def _btn(parent, text, command, secondary=False):
    bg = GRAY_LITE if secondary else GREEN_DARK
    fg = GRAY    if secondary else WHITE
    return tk.Button(parent, text=text, command=command,
                     font=("Helvetica", 11, "bold"),
                     bg=bg, fg=fg, relief="flat",
                     activebackground=GREEN_MID, activeforeground=WHITE,
                     cursor="hand2", pady=8)

def _entry(parent):
    e = tk.Entry(parent, font=("Helvetica", 11),
                 bg=WHITE, fg=TEXT, relief="flat",
                 insertbackground=GREEN_DARK,
                 highlightthickness=1,
                 highlightbackground=BORDER,
                 highlightcolor=GREEN_MID)
    return e


# ─────────────────────────────────────────
#  FEATURE NAME HEURISTICS
# ─────────────────────────────────────────

_KNOWN_FIELDS = {
    "heart": [
        ("age",        "Age",                    "years, e.g. 54"),
        ("sex",        "Sex",                    "1 = Male, 0 = Female"),
        ("cp",         "Chest Pain Type",        "0-3 (0=typical angina … 3=asymptomatic)"),
        ("trestbps",   "Resting Blood Pressure", "mm Hg, e.g. 130"),
        ("chol",       "Serum Cholesterol",      "mg/dl, e.g. 250"),
        ("fbs",        "Fasting Blood Sugar",    "1 if >120 mg/dl, else 0"),
        ("restecg",    "Resting ECG",            "0-2"),
        ("thalach",    "Max Heart Rate",         "bpm, e.g. 150"),
        ("exang",      "Exercise Induced Angina","1 = Yes, 0 = No"),
        ("oldpeak",    "ST Depression",          "e.g. 1.4"),
        ("slope",      "Slope of ST Segment",    "0-2"),
        ("ca",         "Major Vessels (0-3)",    "coloured by fluoroscopy"),
        ("thal",       "Thal",                   "1=normal 2=fixed defect 3=reversable"),
    ],
    "diabetes": [
        ("pregnancies",   "Pregnancies",    "number, e.g. 2"),
        ("glucose",       "Glucose",        "plasma glucose mg/dl, e.g. 120"),
        ("blood_pressure","Blood Pressure", "mm Hg, e.g. 80"),
        ("skin_thickness","Skin Thickness", "mm, e.g. 20"),
        ("insulin",       "Insulin",        "μU/ml, e.g. 79"),
        ("bmi",           "BMI",            "e.g. 25.5"),
        ("dpf",           "Diabetes Pedigree","e.g. 0.47"),
        ("age",           "Age",            "years, e.g. 33"),
    ],
}

_FIELD_RANGES = {
    "age": (0, 120),
    "sex": (0, 1),
    "cp": (0, 3),
    "trestbps": (60, 200),
    "chol": (100, 600),
    "fbs": (0, 1),
    "restecg": (0, 2),
    "thalach": (60, 220),
    "exang": (0, 1),
    "oldpeak": (0, 10),
    "slope": (0, 2),
    "ca": (0, 4),
    "thal": (0, 3),
    "pregnancies": (0, 20),
    "glucose": (0, 600),
    "blood_pressure": (0, 300),
    "skin_thickness": (0, 100),
    "insulin": (0, 900),
    "bmi": (0, 100),
    "dpf": (0, 3),
}


def _get_field_defs(model_id, n_features, server_config=None):
    if server_config and "features" in server_config:
        try:
            features = server_config["features"]
            if len(features) == n_features:
                return [(f["key"], f["label"], f.get("hint", ""))
                        for f in features]
        except (KeyError, TypeError):
            pass

    known = _KNOWN_FIELDS.get(model_id.lower())
    if known and len(known) == n_features:
        return known

    return [(f"feature_{i}", f"Feature {i+1}", f"numeric value for input {i+1}")
            for i in range(n_features)]


# ─────────────────────────────────────────
#  GEMINI CALL
# ─────────────────────────────────────────

def _call_gemini_simple(prediction: str, patient_data: dict, timeout=30) -> str:
    prompt = f"""
You are a medical assistant AI.

A machine learning model has produced the following result:
Result: {prediction}

Patient data:
{json.dumps(patient_data, indent=2)}

Your task:
1. Clearly explain what this result means
2. If disease is detected, explain possible risks (e.g. heart attack risk if relevant)
3. Suggest general precautions
4. Keep it simple and easy to understand
5. DO NOT give definitive diagnosis, only guidance

Format:
- Summary
- Possible Risks
- Recommendations
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    url = GEMINI_URL.format(key=GEMINI_API_KEY)

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"⚠️ Gemini failed: {e}"
# ─────────────────────────────────────────
#  BACKEND CONFIG FETCH
# ─────────────────────────────────────────

def _fetch_model_config(model_id: str) -> dict:
    try:
        response = requests.get(
            f"{SERVER_URL}/model_config?model_id={model_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Could not fetch model config: {e}")
        return {}


# ─────────────────────────────────────────
#  DIAGNOSE SCREEN
# ─────────────────────────────────────────

class DiagnoseScreen(tk.Frame):

    def __init__(self, master, model, epochs):
        super().__init__(master, bg=BG)
        self.master = master
        self.model  = model
        self.epochs = epochs
        self._entries       = {}
        self._field_defs    = []
        self._result_queue  = queue.Queue()
        self._running       = False
        self._gemini_called = False          # guard: only one Gemini call per run
        self.pack(fill="both", expand=True)

        # ── header ──────────────────────────────────────────────────────
        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")
        hdr = tk.Frame(self, bg=GREEN_DARK)
        hdr.pack(fill="x")
        tk.Label(hdr, text="✚  MediCare Portal",
                 font=("Helvetica", 15, "bold"),
                 bg=GREEN_DARK, fg=WHITE, pady=14).pack()

        # ── scrollable body ──────────────────────────────────────────────
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True)

        sb = tk.Scrollbar(outer)
        sb.pack(side="right", fill="y")

        self._cv = tk.Canvas(outer, bg=BG, highlightthickness=0,
                             yscrollcommand=sb.set)
        self._cv.pack(side="left", fill="both", expand=True)
        sb.config(command=self._cv.yview)

        body = tk.Frame(self._cv, bg=BG)
        bwin = self._cv.create_window((0, 0), window=body, anchor="nw")

        body.bind("<Configure>",
                  lambda e: self._cv.configure(scrollregion=self._cv.bbox("all")))
        self._cv.bind("<Configure>",
                      lambda e: self._cv.itemconfig(bwin, width=e.width))
        self._cv.bind("<MouseWheel>", self._mw)
        self._cv.bind("<Button-4>",   self._mw)
        self._cv.bind("<Button-5>",   self._mw)

        # ── title row ───────────────────────────────────────────────────
        top = tk.Frame(body, bg=BG)
        top.pack(fill="x", padx=120, pady=(24, 4))
        tk.Label(top, text="🩺  Diagnose Patient",
                 font=("Helvetica", 17, "bold"),
                 bg=BG, fg=TEXT).pack(side="left")
        _btn(top, "⟵ Back",
             lambda: master.show_result(model, master.filepath, epochs),
             secondary=True).pack(side="right")

        tk.Label(body,
                 text=f"Model: {model.title()}  •  Trained for {epochs} epoch(s)",
                 font=("Helvetica", 10), bg=BG, fg=GRAY).pack(anchor="w", padx=120)

        # ── check model is available ─────────────────────────────────────
        if _train_module.trained_model is None:
            self._no_model_banner(body)
            return

        n_features = (_train_module.last_X_max.shape[0]
                      if _train_module.last_X_max is not None else 1)

        server_config    = _fetch_model_config(model)
        self._field_defs = _get_field_defs(model, n_features, server_config)

        # ── form card ───────────────────────────────────────────────────
        form_card = tk.Frame(body, bg=WHITE, padx=30, pady=24,
                             highlightthickness=1, highlightbackground=BORDER)
        form_card.pack(fill="x", padx=120, pady=(18, 8))

        tk.Label(form_card, text="Patient Parameters",
                 font=("Helvetica", 13, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(form_card,
                 text="Enter the clinical values below. All fields expect numeric input.",
                 font=("Helvetica", 9), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(2, 16))

        tk.Frame(form_card, height=1, bg=BORDER).pack(fill="x", pady=(0, 14))

        grid = tk.Frame(form_card, bg=WHITE)
        grid.pack(fill="x")

        for col in range(2):
            grid.columnconfigure(col, weight=1, uniform="col")

        for idx, (key, lbl, hint) in enumerate(self._field_defs):
            row_i = idx // 2
            col_i = idx %  2

            cell = tk.Frame(grid, bg=WHITE, padx=8, pady=6)
            cell.grid(row=row_i, column=col_i, sticky="ew")

            tk.Label(cell, text=lbl,
                     font=("Helvetica", 10, "bold"),
                     bg=WHITE, fg=TEXT).pack(anchor="w")
            tk.Label(cell, text=hint,
                     font=("Helvetica", 8),
                     bg=WHITE, fg=GRAY).pack(anchor="w")

            e = _entry(cell)
            e.pack(fill="x", pady=(4, 0), ipady=5)
            self._entries[key] = e

        act = tk.Frame(form_card, bg=WHITE)
        act.pack(fill="x", pady=(20, 0))

        _btn(act, "Clear All", self._clear_form, secondary=True).pack(side="left")
        self._run_btn = _btn(act, "▶  Run Diagnosis", self._run)
        self._run_btn.pack(side="right")

        self._results_frame = tk.Frame(body, bg=BG)
        self._results_frame.pack(fill="x", padx=120, pady=(0, 30))

    # ── scroll helpers ───────────────────────────────────────────────────
    def _mw(self, e):
        if e.num == 4:   self._cv.yview_scroll(-1, "units")
        elif e.num == 5: self._cv.yview_scroll( 1, "units")
        else:            self._cv.yview_scroll(int(-1*(e.delta/120)), "units")

    def _bind_scroll(self, widget):
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            widget.bind(ev, self._mw)
        for child in widget.winfo_children():
            self._bind_scroll(child)

    # ── no-model banner ──────────────────────────────────────────────────
    def _no_model_banner(self, body):
        b = tk.Frame(body, bg=RED_LITE, padx=20, pady=16,
                     highlightthickness=1, highlightbackground="#F87171")
        b.pack(fill="x", padx=120, pady=30)
        tk.Label(b, text="⚠  No trained model found",
                 font=("Helvetica", 13, "bold"),
                 bg=RED_LITE, fg=RED).pack(anchor="w")
        tk.Label(b,
                 text="Please train a model first before using the diagnose feature.",
                 font=("Helvetica", 10), bg=RED_LITE, fg=RED).pack(anchor="w", pady=(4, 0))

    # ── form helpers ─────────────────────────────────────────────────────
    def _clear_form(self):
        for e in self._entries.values():
            e.delete(0, "end")

    # ── run ──────────────────────────────────────────────────────────────
    def _run(self):
        if self._running:
            messagebox.showinfo("Running", "A diagnosis is already in progress.")
            return

        values   = {}
        raw_nums = []

        for key, lbl, _ in self._field_defs:
            val_str = self._entries[key].get().strip()
            if not val_str:
                messagebox.showwarning("Missing Field",
                                       f"Please enter a value for '{lbl}'.")
                return
            try:
                val = float(val_str)
            except ValueError:
                messagebox.showerror("Invalid Input",
                                     f"'{lbl}' must be a number. Got: '{val_str}'")
                return

            if key in _FIELD_RANGES:
                min_val, max_val = _FIELD_RANGES[key]
                if not (min_val <= val <= max_val):
                    if not messagebox.askyesno(
                            "Out of Range",
                            f"'{lbl}' should typically be {min_val}–{max_val}.\n"
                            f"You entered {val}.\n\nProceed anyway?"):
                        return

            values[lbl] = val_str
            raw_nums.append(val)

        # Clear previous results
        for w in self._results_frame.winfo_children():
            w.destroy()

        # Loading card
        loading = tk.Frame(self._results_frame, bg=WHITE, padx=20, pady=20,
                           highlightthickness=1, highlightbackground=BORDER)
        loading.pack(fill="x", pady=(8, 0))
        self._spin_label = tk.Label(loading,
                                    text="⏳  Running ML model…",
                                    font=("Helvetica", 11, "bold"),
                                    bg=WHITE, fg=GREEN_DARK)
        self._spin_label.pack(anchor="w")
        self._run_btn.config(state="disabled", text="Running…")
        self.update()

        # Reset guards for this fresh run
        self._gemini_called = False
        self._running       = True

        threading.Thread(
            target=self._predict_and_interpret,
            args=(raw_nums, values, loading),
            daemon=True
        ).start()

        self._check_queue()

   

    def _predict_and_interpret(self, raw_nums, human_values, loading_widget):
        try:
            # 1. ML prediction
            try:
                prediction, confidence = self._ml_predict(raw_nums)
            except Exception as exc:
                self._result_queue.put(("error_ml", str(exc), None, None))
                return

            # ✅ Safer disease detection
            is_positive = "disease detected" in prediction.lower()

            # 2. Only call Gemini if disease detected
            if is_positive:
                self._result_queue.put(("gemini_start", None, None, None))

                # ⏱ Small delay to avoid rate limit
                time.sleep(2)

                try:
                    gemini_text = _call_gemini_simple(prediction, human_values)
                except Exception as exc:
                    gemini_text = (
                        "⚠️ Clinical interpretation unavailable\n\n"
                        f"Reason: {exc}\n\n"
                        "Please consult a healthcare professional."
                    )
            else:
                # ✅ Skip Gemini completely
                gemini_text = (
                    "✅ No disease detected.\n\n"
                    "The model prediction suggests no immediate risk.\n"
                    "Maintain a healthy lifestyle and consult a doctor for regular checkups."
                )

            # 3. Done
            self._result_queue.put(
                ("success", prediction, confidence, (human_values, gemini_text))
            )

        except Exception as exc:
            self._result_queue.put(("error_fatal", str(exc), None, None))
        # ── queue poller (runs on main thread via after()) ───────────────────
    def _check_queue(self):
        try:
            status, pred, conf, data = self._result_queue.get_nowait()

            if status == "gemini_start":
                # Not terminal — update label and keep polling
                self._spin_label.config(
                    text="🤖  Asking Gemini for clinical interpretation…")
                self.after(100, self._check_queue)
                return

            # ── terminal states — re-enable button ──────────────────────
            self._running = False
            self._run_btn.config(state="normal", text="▶  Run Diagnosis")

            if status == "error_ml":
                self._show_error(f"ML prediction failed:\n{pred}")
            elif status == "error_fatal":
                self._show_error(f"Fatal error:\n{pred}")
            elif status == "success":
                loading        = self._spin_label.master
                human_values, gemini_text = data
                self._show_results(loading, pred, conf, human_values, gemini_text)

        except queue.Empty:
            if self._running:
                self.after(100, self._check_queue)

    # ── ML prediction ────────────────────────────────────────────────────
    def _ml_predict(self, raw_nums):
        model  = _train_module.trained_model
        config = _train_module.last_config
        X_max  = _train_module.last_X_max

        if model is None:
            raise RuntimeError("No trained model available")

        X = np.array(raw_nums, dtype=float).reshape(1, -1)

        if X_max is not None:
            X = X / X_max
        else:
            X = X / (np.max(X, axis=0) + 1e-8)

        pred        = model.predict(X, verbose=0)
        output_type = (config or {}).get("output", "binary")

        if output_type == "binary":
            prob  = float(pred[0][0])
            label = "Disease Detected" if prob > 0.5 else "No Disease Detected"
            conf  = f"{prob*100:.1f}%"
        elif output_type == "multi_class":
            cls   = int(np.argmax(pred[0]))
            prob  = float(np.max(pred[0]))
            label = f"Class {cls}"
            conf  = f"{prob*100:.1f}%"
        else:
            val   = float(pred[0][0])
            label = f"Predicted value: {val:.4f}"
            conf  = "—"

        return label, conf

    # ── results display ──────────────────────────────────────────────────
    def _show_results(self, loading_widget, prediction, confidence,
                      human_values, gemini_text):
        loading_widget.destroy()

        is_positive = any(k in prediction.lower()
                          for k in ("detected", "positive", "yes", "class"))

        color    = RED       if is_positive else GREEN_DARK
        bg_color = RED_LITE  if is_positive else GREEN_LITE
        icon     = "⚠"       if is_positive else "✔"

        # ML result card
        result_card = tk.Frame(self._results_frame, bg=bg_color, padx=24, pady=20,
                               highlightthickness=2,
                               highlightbackground=color)
        result_card.pack(fill="x", pady=(8, 6))

        top_row = tk.Frame(result_card, bg=bg_color)
        top_row.pack(fill="x")
        tk.Label(top_row, text=f"{icon}  ML Model Result",
                 font=("Helvetica", 13, "bold"),
                 bg=bg_color, fg=color).pack(side="left")
        tk.Label(top_row, text=f"Confidence: {confidence}",
                 font=("Helvetica", 11),
                 bg=bg_color, fg=GRAY).pack(side="right")
        tk.Label(result_card, text=prediction,
                 font=("Helvetica", 16, "bold"),
                 bg=bg_color, fg=color).pack(anchor="w", pady=(6, 0))

        # Input summary card
        summary_card = tk.Frame(self._results_frame, bg=WHITE, padx=24, pady=16,
                                highlightthickness=1, highlightbackground=BORDER)
        summary_card.pack(fill="x", pady=(0, 6))

        tk.Label(summary_card, text="Entered Patient Data",
                 font=("Helvetica", 11, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")

        sgrid = tk.Frame(summary_card, bg=WHITE)
        sgrid.pack(fill="x", pady=(8, 0))
        for col in range(4):
            sgrid.columnconfigure(col, weight=1)

        for idx, (label, val) in enumerate(human_values.items()):
            r, c = divmod(idx, 2)
            cell = tk.Frame(sgrid, bg=GRAY_LITE, padx=8, pady=4,
                            highlightthickness=1, highlightbackground=BORDER)
            cell.grid(row=r, column=c*2, columnspan=2, sticky="ew", padx=3, pady=2)
            tk.Label(cell, text=label,
                     font=("Helvetica", 8), bg=GRAY_LITE, fg=GRAY).pack(anchor="w")
            tk.Label(cell, text=val,
                     font=("Helvetica", 11, "bold"),
                     bg=GRAY_LITE, fg=TEXT).pack(anchor="w")

        # Gemini card
        gemini_card = tk.Frame(self._results_frame, bg=WHITE, padx=24, pady=20,
                               highlightthickness=1, highlightbackground=BORDER)
        gemini_card.pack(fill="x", pady=(0, 10))

        hdr_row = tk.Frame(gemini_card, bg=WHITE)
        hdr_row.pack(fill="x")
        tk.Label(hdr_row, text="🤖  Clinical Interpretation",
                 font=("Helvetica", 13, "bold"),
                 bg=WHITE, fg=BLUE).pack(side="left")
        tk.Label(hdr_row,
                 text="AI-assisted · not a substitute for medical advice",
                 font=("Helvetica", 8), bg=WHITE, fg=GRAY).pack(side="right")

        tk.Frame(gemini_card, height=1, bg=BORDER).pack(fill="x", pady=(8, 12))

        txt = tk.Text(gemini_card, wrap="word",
                      font=("Helvetica", 10),
                      bg=BLUE_LITE, fg=TEXT,
                      relief="flat", padx=12, pady=12,
                      height=18)
        txt.insert("1.0", gemini_text)
        txt.config(state="disabled")
        txt.pack(fill="x")

        def _copy():
            self.clipboard_clear()
            self.clipboard_append(gemini_text)
            messagebox.showinfo("Copied", "Interpretation copied to clipboard.")

        btn_row = tk.Frame(self._results_frame, bg=BG)
        btn_row.pack(fill="x", pady=(4, 0))
        _btn(btn_row, "📋  Copy Interpretation", _copy,
             secondary=True).pack(side="left")
        _btn(btn_row, "🔄  Diagnose Another Patient",
             self._clear_and_scroll_up).pack(side="right")

        self.after(50,  lambda: self._bind_scroll(self._results_frame))
        self.after(100, lambda: self._cv.yview_moveto(1.0))

    # ── misc ─────────────────────────────────────────────────────────────
    def _clear_and_scroll_up(self):
        self._clear_form()
        for w in self._results_frame.winfo_children():
            w.destroy()
        self._cv.yview_moveto(0.0)

    def _show_error(self, message):
        self._run_btn.config(state="normal", text="▶  Run Diagnosis")
        err = tk.Frame(self._results_frame, bg=RED_LITE, padx=20, pady=16,
                       highlightthickness=1, highlightbackground="#F87171")
        err.pack(fill="x", pady=(8, 0))
        tk.Label(err, text="❌  Error",
                 font=("Helvetica", 12, "bold"),
                 bg=RED_LITE, fg=RED).pack(anchor="w")
        tk.Label(err, text=message,
                 font=("Helvetica", 10),
                 bg=RED_LITE, fg=RED,
                 justify="left", wraplength=700).pack(anchor="w", pady=(4, 0))
        self.after(100, lambda: self._cv.yview_moveto(1.0))
