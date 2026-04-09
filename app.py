import threading
import time
import json
import os
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import tkinter.font as tkfont

from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/download")
def download_app():
    return FileResponse(
        path="app.exe", 
        filename="MediCareAI.exe", 
        media_type="application/octet-stream"
    )


# ─────────────────────────────────────────
#  IMPORT APP LOGIC
# ─────────────────────────────────────────
import training as _train_module
from training import train_and_upload, upload_weights, predict_disease, detect_data_type, get_models, add_model_to_server

# ─────────────────────────────────────────
#  MODEL ID MAPPING
#  Maps UI model keys → backend model_id strings
# ─────────────────────────────────────────
MODEL_ID_MAP = {
    "tumor": "xray",    # image model
    "heart": "heart",   # tabular model
}

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

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def styled_entry(parent, show=None):
    e = tk.Entry(parent, show=show, font=("Helvetica", 11),
                 bg=WHITE, fg=TEXT, relief="flat",
                 insertbackground=GREEN_DARK,
                 highlightthickness=1,
                 highlightbackground=BORDER,
                 highlightcolor=GREEN_MID)
    return e

def styled_button(parent, text, command, secondary=False):
    bg = GRAY_LITE if secondary else GREEN_DARK
    fg = GRAY    if secondary else WHITE
    b = tk.Button(parent, text=text, command=command,
                  font=("Helvetica", 11, "bold"),
                  bg=bg, fg=fg, relief="flat",
                  activebackground=GREEN_MID,
                  activeforeground=WHITE,
                  cursor="hand2", pady=8)
    return b

def label(parent, text, size=11, bold=False, color=None):
    font = ("Helvetica", size, "bold") if bold else ("Helvetica", size)
    return tk.Label(parent, text=text, font=font,
                    bg=parent["bg"] if hasattr(parent, "__getitem__") else BG,
                    fg=color or TEXT)

def divider(parent):
    tk.Frame(parent, height=1, bg=BORDER).pack(fill="x", padx=30, pady=8)

# ─────────────────────────────────────────
#  APP / SCREEN MANAGER
# ─────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MediCare Portal")
        self.state("zoomed")
        self.resizable(True, True)
        self.configure(bg=BG)
        # Shared state across screens
        self.filepath = None
        self.train_result = None   # return value from train_and_upload()
        self.upload_result = None  # return value from upload_weights()
        self.show_login()

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    def show_login(self):
        self.clear()
        LoginScreen(self)

    def show_terms(self):
        self.clear()
        TermsScreen(self)

    def show_main(self):
        self.clear()
        MainScreen(self)

    def show_upload(self, model):
        self.clear()
        UploadScreen(self, model)

    def show_loading(self, model, filepath, epochs):
        self.clear()
        LoadingScreen(self, model, filepath, epochs)

    def show_result(self, model, filepath, epochs, train_result=None):
        self.filepath = filepath
        self.train_result = train_result
        self.clear()
        ResultScreen(self, model, filepath, epochs, train_result)

    def show_upload_server(self, model, epochs):
        self.clear()
        ServerUploadScreen(self, model, epochs)

    def show_server_loading(self, model, epochs):
        self.clear()
        ServerLoadingScreen(self, model, epochs)

# ─────────────────────────────────────────
#  LOGIN SCREEN  (unchanged)
# ─────────────────────────────────────────
class LoginScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.master = master
        self.pack(fill="both", expand=True)

        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")

        header = tk.Frame(self, bg=GREEN_DARK)
        header.pack(fill="x")
        tk.Label(header, text="✚  MediCare Portal",
                 font=("Helvetica", 17, "bold"),
                 bg=GREEN_DARK, fg=WHITE,
                 pady=18).pack()

        card = tk.Frame(self, bg=WHITE, padx=40, pady=30,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="x", padx=120, pady=40)

        label(card, "Welcome back", size=16, bold=True).pack(anchor="w", pady=(0,4))
        label(card, "Sign in to access your medical portal",
              color=GRAY).pack(anchor="w", pady=(0,20))

        label(card, "Username or Staff ID", size=10, color=GRAY).pack(anchor="w")
        self.username = styled_entry(card)
        self.username.pack(fill="x", pady=(4, 14), ipady=6)

        label(card, "Password", size=10, color=GRAY).pack(anchor="w")
        self.password = styled_entry(card, show="•")
        self.password.pack(fill="x", pady=(4, 20), ipady=6)

        styled_button(card, "Sign In", self.login).pack(fill="x")

        label(card, "Demo mode — no data is stored or transmitted",
              size=9, color=GRAY).pack(pady=(12, 0))
        self.bind_all("<Return>", lambda event: self.login())

    def login(self):
        u = self.username.get().strip()
        p = self.password.get().strip()
        if not u or not p:
            messagebox.showwarning("Missing Fields",
                                   "Please enter your username and password.")
        else:
            self.master.show_terms()

# ─────────────────────────────────────────
#  TERMS SCREEN  (unchanged)
# ─────────────────────────────────────────
class TermsScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.master = master
        self.pack(fill="both", expand=True)

        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")

        header = tk.Frame(self, bg=GREEN_DARK)
        header.pack(fill="x")
        tk.Label(header, text="Terms & Conditions",
                 font=("Helvetica", 15, "bold"),
                 bg=GREEN_DARK, fg=WHITE, pady=14).pack()

        tk.Label(self, text="Please read and accept before continuing.",
                 font=("Helvetica", 11), bg=BG, fg=GRAY).pack(pady=(16, 8))

        box_frame = tk.Frame(self, bg=WHITE,
                             highlightthickness=1,
                             highlightbackground=BORDER)
        box_frame.pack(fill="x", padx=120, pady=(0, 10))

        scrollbar = tk.Scrollbar(box_frame)
        scrollbar.pack(side="right", fill="y")

        self.text = tk.Text(box_frame, wrap="word",
                       yscrollcommand=scrollbar.set,
                       font=("Helvetica", 11),
                       bg=WHITE, fg="#000000",
                       relief="flat", padx=16, pady=16,
                       height=20)
        self.text.pack(side="left", fill="x", expand=True)
        scrollbar.config(command=self.text.yview)

        terms = (
            "1. Acceptance of Terms\n"
            "By accessing this portal, you agree to be bound by these Terms and Conditions.\n\n"
            "2. Authorized Use Only\n"
            "This portal is for authorized medical personnel and registered patients only. "
            "Unauthorized access is strictly prohibited.\n\n"
            "3. Patient Data & Privacy\n"
            "All patient data is handled in accordance with applicable healthcare regulations. "
            "This demo does not collect, store, or transmit any personal or medical information.\n\n"
            "4. Medical Disclaimer\n"
            "Information in this portal is for reference only and does not constitute medical advice. "
            "Always consult a qualified healthcare professional.\n\n"
            "5. Confidentiality\n"
            "Users are responsible for maintaining the confidentiality of their credentials. "
            "Report any unauthorized access immediately.\n\n"
            "6. Limitation of Liability\n"
            "The hospital and its affiliates are not liable for decisions made based on "
            "information accessed through this portal.\n\n"
            "7. Changes to Terms\n"
            "These terms may be updated periodically. Continued use constitutes acceptance "
            "of any revised terms.\n"
        )

        self.text.insert("1.0", terms)
        self.text.config(state="disabled")

        bottom = tk.Frame(self, bg=BG)
        bottom.pack(fill="x", padx=120, pady=14)

        self.agreed = tk.BooleanVar()
        tk.Checkbutton(bottom,
                       text="I have read and agree to the Terms & Conditions",
                       variable=self.agreed,
                       bg=BG, fg=TEXT,
                       activebackground=BG,
                       selectcolor=WHITE,
                       font=("Helvetica", 10)).pack(anchor="w", pady=(0, 10))

        btn_row = tk.Frame(bottom, bg=BG)
        btn_row.pack(fill="x")
        styled_button(btn_row, "Decline", self.decline,
                      secondary=True).pack(side="left", expand=True, fill="x", padx=(0, 6))
        styled_button(btn_row, "Accept & Continue",
                      self.accept).pack(side="left", expand=True, fill="x")
        self.bind_all("<Return>", lambda event: self.accept())

    def accept(self):
        if not self.agreed.get():
            messagebox.showwarning("Agreement Required",
                                   "Please tick the checkbox to confirm you agree.")
        else:
            self.master.show_main()

    def decline(self):
        self.master.destroy()

# ─────────────────────────────────────────
#  MAIN SCREEN  (unchanged)
# ─────────────────────────────────────────
class MainScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)

        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")

        header = tk.Frame(self, bg=GREEN_DARK)
        header.pack(fill="x")
        tk.Label(header, text="✚  MediCare Portal",
                 font=("Helvetica", 15, "bold"),
                 bg=GREEN_DARK, fg=WHITE, pady=14).pack()

        search_frame = tk.Frame(self, bg=BG)
        search_frame.pack(fill="x", padx=200, pady=(24, 16))

        tk.Label(search_frame, text="Search",
                 font=("Helvetica", 10), bg=BG, fg=GRAY).pack(anchor="w")

        search_row = tk.Frame(search_frame, bg=WHITE,
                              highlightthickness=1,
                              highlightbackground=BORDER)
        search_row.pack(fill="x", pady=(4, 0))

        tk.Label(search_row, text="⌕", font=("Helvetica", 14),
                 bg=WHITE, fg=GRAY).pack(side="left", padx=(10, 0))

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_row, textvariable=self.search_var,
                                font=("Helvetica", 12), bg=WHITE, fg=TEXT,
                                relief="flat", insertbackground=GREEN_DARK)
        search_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=8)
        search_entry.bind("<Return>", lambda e: self.do_search())

        styled_button(search_row, "Search", self.do_search).pack(side="right", padx=6, pady=4)

        tk.Label(self, text="Select a diagnostic model",
                 font=("Helvetica", 12, "bold"), bg=BG, fg=TEXT).pack(pady=(8, 12))

        self.selected = tk.StringVar(value="")

        cards_frame = tk.Frame(self, bg=BG)
        cards_frame.pack(padx=200, fill="x")

        self.card_frames = {}

        # Status label created early so it can show "Loading..." during fetch
        self.status = tk.Label(self, text="", font=("Helvetica", 10),
                               bg=BG, fg=GRAY)

        # ✅ Fetch model list from server via training.py
        # Falls back to defaults if server is unreachable
        self.status.config(text="Loading models from server...", fg=GRAY)
        self.update()
        models = get_models()
        self.status.config(text="")

        for key, title, desc in models:
            self._make_card(cards_frame, key, title, desc)

        custom_frame = tk.Frame(self, bg=BG)
        custom_frame.pack(padx=200, fill="x", pady=(12, 0))

        tk.Label(custom_frame, text="Or add your own model",
                 font=("Helvetica", 10), bg=BG, fg=GRAY).pack(anchor="w")

        input_row = tk.Frame(custom_frame, bg=WHITE,
                             highlightthickness=1,
                             highlightbackground=BORDER)
        input_row.pack(fill="x", pady=(4, 0))

        self.custom_entry = tk.Entry(input_row, font=("Helvetica", 11),
                                     bg=WHITE, fg=TEXT, relief="flat",
                                     insertbackground=GREEN_DARK)
        self.custom_entry.insert(0, "Enter custom model name...")
        self.custom_entry.config(fg=GRAY)
        self.custom_entry.bind("<FocusIn>",  self._clear_placeholder)
        self.custom_entry.bind("<FocusOut>", self._restore_placeholder)
        self.custom_entry.bind("<Return>",   lambda e: self._add_custom())
        self.custom_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=10)

        styled_button(input_row, "+ Add", self._add_custom).pack(side="right", padx=6, pady=4)

        styled_button(self, "Proceed with Selected Model →",
                      self._proceed).pack(pady=28)

        self.status.pack()

    def _make_card(self, parent, key, title, desc, custom=False):
        card = tk.Frame(parent, bg=WHITE, padx=20, pady=16,
                        highlightthickness=2,
                        highlightbackground=BORDER,
                        cursor="hand2")
        card.pack(side="left" if not custom else "top",
                  expand=not custom, fill="x",
                  padx=(0, 12) if not custom else 0,
                  pady=(0, 8))

        tk.Label(card, text=title,
                 font=("Helvetica", 13, "bold"),
                 bg=WHITE, fg=GREEN_DARK).pack(anchor="w")

        tk.Label(card, text=desc,
                 font=("Helvetica", 9),
                 bg=WHITE, fg=GRAY,
                 wraplength=220, justify="left").pack(anchor="w", pady=(4, 10))

        tk.Button(card, text="Select",
                  font=("Helvetica", 10),
                  bg=GREEN_LITE, fg=GREEN_DARK,
                  activebackground=GREEN_MID,
                  activeforeground=WHITE,
                  relief="flat", cursor="hand2",
                  command=lambda k=key, c=card, t=title: self._select(k, c, t)).pack(anchor="w")

        self.card_frames[key] = card
        return card

    def _select(self, key, card, title):
        for k, c in self.card_frames.items():
            c.config(highlightbackground=BORDER, highlightthickness=2, bg=WHITE)
            for child in c.winfo_children():
                child.config(bg=WHITE)

        card.config(highlightbackground=GREEN_DARK, highlightthickness=2, bg=GREEN_LITE)
        for child in card.winfo_children():
            child.config(bg=GREEN_LITE)

        self.selected.set(key)
        self.status.config(text=f"Selected: {title}", fg=GREEN_DARK)

    def _clear_placeholder(self, event):
        if self.custom_entry.get() == "Enter custom model name...":
            self.custom_entry.delete(0, "end")
            self.custom_entry.config(fg=TEXT)

    def _restore_placeholder(self, event):
        if not self.custom_entry.get():
            self.custom_entry.insert(0, "Enter custom model name...")
            self.custom_entry.config(fg=GRAY)

    def _add_custom(self):
        name = self.custom_entry.get().strip()
        if not name or name == "Enter custom model name...":
            messagebox.showwarning("Empty", "Please enter a model name.")
            return
        if name in self.card_frames:
            messagebox.showinfo("Exists", f'"{name}" is already added.')
            return

        # ✅ Push to server first
        self.status.config(text=f'Adding "{name}" to server...', fg=GRAY)
        self.update()
        success, message = add_model_to_server(name, model_type="tabular")

        if not success:
            # Still add locally even if server is unreachable
            self.status.config(text=f'Server: {message} — added locally only.', fg=GRAY)
        else:
            self.status.config(text=f'"{name}" added to server.', fg=GREEN_MID)

        new_frame = tk.Frame(self, bg=BG)
        new_frame.pack(padx=200, fill="x", pady=(0, 4))

        card = tk.Frame(new_frame, bg=WHITE, padx=20, pady=16,
                        highlightthickness=2,
                        highlightbackground=BORDER,
                        cursor="hand2")
        card.pack(fill="x")

        tk.Label(card, text=name, font=("Helvetica", 13, "bold"),
                 bg=WHITE, fg=GREEN_DARK).pack(anchor="w")
        tk.Label(card, text="Custom user-defined model.",
                 font=("Helvetica", 9), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(4, 10))
        tk.Button(card, text="Select", font=("Helvetica", 10),
                  bg=GREEN_LITE, fg=GREEN_DARK, relief="flat", cursor="hand2",
                  command=lambda k=name, c=card, t=name: self._select(k, c, t)).pack(anchor="w")

        self.card_frames[name] = card

        self.custom_entry.delete(0, "end")
        self._restore_placeholder(None)

    def do_search(self):
        query = self.search_var.get().strip()
        if query:
            self.status.config(text=f'Searching for: "{query}"...', fg=GRAY)

    def _proceed(self):
        sel = self.selected.get()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a diagnostic model first.")
        else:
            self.master.show_upload(sel)

# ─────────────────────────────────────────
#  UPLOAD SCREEN
#  Collects: filepath, epochs
#  Passes to: LoadingScreen → train_and_upload()
# ─────────────────────────────────────────
class UploadScreen(tk.Frame):
    def __init__(self, master, model):
        super().__init__(master, bg=BG)
        self.master = master
        self.model = model
        self.filepath = None
        self.pack(fill="both", expand=True)

        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")
        header = tk.Frame(self, bg=GREEN_DARK)
        header.pack(fill="x")
        tk.Label(header, text="✚  MediCare Portal",
                 font=("Helvetica", 15, "bold"),
                 bg=GREEN_DARK, fg=WHITE, pady=14).pack()

        card = tk.Frame(self, bg=WHITE, padx=40, pady=30,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="x", padx=300, pady=40)

        tk.Label(card, text=f"Model: {self.model.title()}",
                 font=("Helvetica", 11), bg=WHITE, fg=GREEN_DARK).pack(anchor="w")
        tk.Label(card, text="Configure & Upload",
                 font=("Helvetica", 16, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(4, 2))
        tk.Label(card, text="Select your dataset and set training parameters before running.",
                 font=("Helvetica", 10), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(0, 20))

        tk.Frame(card, height=1, bg=BORDER).pack(fill="x", pady=(0, 16))

        # ── Dataset upload ──
        tk.Label(card, text="Dataset File",
                 font=("Helvetica", 11, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")

        # Hint changes based on model type
        if self.model == "tumor":
            hint = "Accepted formats: image folder (for tumor/image models)"
        else:
            hint = "Accepted formats: .csv (for tabular models)"
        tk.Label(card, text=hint,
                 font=("Helvetica", 9), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(2, 8))

        drop_zone = tk.Frame(card, bg=GREEN_LITE,
                             highlightthickness=1,
                             highlightbackground=BORDER,
                             pady=20, padx=20)
        drop_zone.pack(fill="x", pady=(0, 20))

        tk.Label(drop_zone, text="📂",
                 font=("Helvetica", 24), bg=GREEN_LITE).pack()
        self.file_label = tk.Label(drop_zone, text="No file selected",
                                   font=("Helvetica", 10), bg=GREEN_LITE, fg=GRAY)
        self.file_label.pack(pady=(6, 10))
        styled_button(drop_zone, "Browse File", self._browse).pack()

        tk.Frame(card, height=1, bg=BORDER).pack(fill="x", pady=16)

        # ── Epochs ──
        tk.Label(card, text="Training Configuration",
                 font=("Helvetica", 11, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(card, text="Set the number of training epochs.",
                 font=("Helvetica", 9), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(2, 12))

        epoch_row = tk.Frame(card, bg=WHITE)
        epoch_row.pack(fill="x", pady=(0, 4))

        tk.Label(epoch_row, text="Epochs:",
                 font=("Helvetica", 11), bg=WHITE, fg=TEXT).pack(side="left", padx=(0, 12))

        tk.Button(epoch_row, text="−", font=("Helvetica", 13, "bold"),
                  bg=GREEN_LITE, fg=GREEN_DARK, relief="flat",
                  width=3, cursor="hand2",
                  command=self._dec_epoch).pack(side="left")

        self.epoch_var = tk.IntVar(value=10)
        tk.Label(epoch_row, textvariable=self.epoch_var,
                 font=("Helvetica", 13, "bold"),
                 bg=WHITE, fg=GREEN_DARK, width=4).pack(side="left")

        tk.Button(epoch_row, text="+", font=("Helvetica", 13, "bold"),
                  bg=GREEN_LITE, fg=GREEN_DARK, relief="flat",
                  width=3, cursor="hand2",
                  command=self._inc_epoch).pack(side="left")

        tk.Label(epoch_row, text="or type:",
                 font=("Helvetica", 10), bg=WHITE, fg=GRAY).pack(side="left", padx=(20, 6))

        self.epoch_entry = tk.Entry(epoch_row, font=("Helvetica", 11),
                                    bg=WHITE, fg=TEXT, relief="flat",
                                    highlightthickness=1,
                                    highlightbackground=BORDER,
                                    width=6, justify="center")
        self.epoch_entry.insert(0, "10")
        self.epoch_entry.pack(side="left", ipady=4, padx=(0, 8))

        styled_button(epoch_row, "Set", self._sync_epoch).pack(side="left")
        self.epoch_entry.bind("<FocusOut>", self._sync_epoch)
        tk.Label(card, text="Recommended: 10–100 epochs for most diagnostic models.",
                 font=("Helvetica", 9), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(6, 0))

        tk.Frame(card, height=1, bg=BORDER).pack(fill="x", pady=16)

        btn_row = tk.Frame(card, bg=WHITE)
        btn_row.pack(fill="x")
        styled_button(btn_row, "← Back", self.master.show_main,
                      secondary=True).pack(side="left", padx=(0, 8))
        styled_button(btn_row, "Run Model →", self._run).pack(side="right")
        self.unbind_all("<Return>")

    def _browse(self):
        # Tumor model expects an image folder; heart/tabular models expect a CSV
        if self.model == "tumor":
            path = filedialog.askdirectory(title="Select Image Dataset Folder")
        else:
            path = filedialog.askopenfilename(
                title="Select Dataset",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
        if path:
            self.filepath = path
            self.file_label.config(
                text=f"✔  {os.path.basename(path)}", fg=GREEN_DARK
            )

    def _inc_epoch(self):
        val = self.epoch_var.get()
        if val < 1000:
            self.epoch_var.set(val + 1)
            self.epoch_entry.delete(0, "end")
            self.epoch_entry.insert(0, str(val + 1))

    def _dec_epoch(self):
        val = self.epoch_var.get()
        if val > 1:
            self.epoch_var.set(val - 1)
            self.epoch_entry.delete(0, "end")
            self.epoch_entry.insert(0, str(val - 1))

    def _sync_epoch(self, event=None):
        try:
            val = max(1, min(1000, int(self.epoch_entry.get().strip())))
            self.epoch_var.set(val)
            self.epoch_entry.delete(0, "end")
            self.epoch_entry.insert(0, str(val))
        except ValueError:
            self.epoch_entry.delete(0, "end")
            self.epoch_entry.insert(0, str(self.epoch_var.get()))

    def _run(self):
        if not self.filepath:
            messagebox.showwarning("No File", "Please select a dataset file first.")
            return
        self._sync_epoch()
        epochs = self.epoch_var.get()
        self.master.show_loading(self.model, self.filepath, epochs)

# ─────────────────────────────────────────
#  LOADING SCREEN
#  Calls train_and_upload() in background thread
#  Passes result → ResultScreen
# ─────────────────────────────────────────
class LoadingScreen(tk.Frame):
    def __init__(self, master, model, filepath, epochs):
        super().__init__(master, bg=BG)
        self.master   = master
        self.model    = model
        self.filepath = filepath
        self.epochs   = epochs
        self.pack(fill="both", expand=True)

        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")
        header = tk.Frame(self, bg=GREEN_DARK)
        header.pack(fill="x")
        tk.Label(header, text="✚  MediCare Portal",
                 font=("Helvetica", 15, "bold"),
                 bg=GREEN_DARK, fg=WHITE, pady=14).pack()

        center = tk.Frame(self, bg=BG)
        center.pack(expand=True)

        tk.Label(center, text="Processing Dataset",
                 font=("Helvetica", 20, "bold"), bg=BG, fg=TEXT).pack(pady=(0, 8))
        tk.Label(center, text=f"Running {self.model.title()} model — please wait...",
                 font=("Helvetica", 11), bg=BG, fg=GRAY).pack(pady=(0, 30))

        bar_bg = tk.Frame(center, bg=BORDER, height=12, width=400)
        bar_bg.pack(pady=(0, 8))
        bar_bg.pack_propagate(False)

        self.bar_fill = tk.Frame(bar_bg, bg=GREEN_DARK, height=12, width=0)
        self.bar_fill.place(x=0, y=0, relheight=1)

        self.pct_label = tk.Label(center, text="0%",
                                  font=("Helvetica", 11, "bold"),
                                  bg=BG, fg=GREEN_DARK)
        self.pct_label.pack()

        self.step_label = tk.Label(center, text="Initializing...",
                                   font=("Helvetica", 10), bg=BG, fg=GRAY)
        self.step_label.pack(pady=(6, 0))

        # Progress animation runs independently; actual training drives completion
        self._train_result = None
        self._train_done   = False
        self._anim_start   = time.time()
        self._animate()

        threading.Thread(target=self._process, daemon=True).start()

    def _steps(self, pct):
        if pct < 15:  return "Initializing model..."
        if pct < 30:  return "Loading dataset..."
        if pct < 50:  return "Preprocessing data..."
        if pct < 70:  return "Running inference..."
        if pct < 85:  return "Analyzing results..."
        if pct < 95:  return "Generating report..."
        return "Finalizing..."

    def _animate(self):
        if self._train_done:
            # Snap to 100 % and move on
            self.bar_fill.place(x=0, y=0, relheight=1, width=400)
            self.pct_label.config(text="100%")
            self.step_label.config(text="Complete!")
            self.after(300, lambda: self.master.show_result(
                self.model, self.filepath, self.epochs, self._train_result))
            return

        elapsed = time.time() - self._anim_start
        # Cap at 95 % while still training
        pct = min(int((elapsed / 30) * 95), 95)
        self.bar_fill.place(x=0, y=0, relheight=1, width=int(400 * pct / 100))
        self.pct_label.config(text=f"{pct}%")
        self.step_label.config(text=self._steps(pct))
        self.after(200, self._animate)

    def _process(self):
        """
        Calls train_and_upload() from train.py with the correct arguments:
          - path      : file or folder path from UploadScreen
          - epochs    : integer from the epoch widget
          - model_id  : resolved via MODEL_ID_MAP; falls back to the raw key
                        so custom models also work (server will handle unknown IDs)
        """
        model_id = MODEL_ID_MAP.get(self.model, self.model)
        try:
            result = train_and_upload(
                path=self.filepath,
                epochs=self.epochs,
                use_server_model=True,
                model_id=model_id,
            )
        except Exception as exc:
            result = f"Error: {exc}"

        self._train_result = result
        self._train_done   = True  # _animate() will pick this up on next tick

# ─────────────────────────────────────────
#  RESULT SCREEN
#  Shows train_result string + lets user
#  download placeholder weights or upload
# ─────────────────────────────────────────
class ResultScreen(tk.Frame):
    def __init__(self, master, model, filepath, epochs, train_result=None):
        super().__init__(master, bg=BG)
        self.master      = master
        self.model       = model
        self.filepath    = filepath
        self.epochs      = epochs
        self.train_result = train_result
        self.pack(fill="both", expand=True)

        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")
        header = tk.Frame(self, bg=GREEN_DARK)
        header.pack(fill="x")
        tk.Label(header, text="✚  MediCare Portal",
                 font=("Helvetica", 15, "bold"),
                 bg=GREEN_DARK, fg=WHITE, pady=14).pack()

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=120, pady=(20, 4))
        tk.Label(top, text="Training Complete",
                 font=("Helvetica", 16, "bold"), bg=BG, fg=TEXT).pack(side="left")
        styled_button(top, "⟵ Run Another", self.master.show_main,
                      secondary=True).pack(side="right")

        fname = os.path.basename(filepath) if filepath else "—"
        tk.Label(self,
                 text=f"Model: {model.title()}  •  File: {fname}  •  Epochs: {epochs}",
                 font=("Helvetica", 10), bg=BG, fg=GRAY).pack(anchor="w", padx=120)

        # ── Training result banner ──
        result_text = train_result if train_result else "No result returned."
        result_color = GREEN_DARK if "completed" in str(result_text).lower() else "#B91C1C"

        result_banner = tk.Frame(self, bg=WHITE, padx=20, pady=12,
                                 highlightthickness=1,
                                 highlightbackground=BORDER)
        result_banner.pack(fill="x", padx=120, pady=(12, 8))
        tk.Label(result_banner, text="Training Result",
                 font=("Helvetica", 11, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(result_banner, text=result_text,
                 font=("Helvetica", 11), bg=WHITE, fg=result_color).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, height=1, bg=BORDER).pack(fill="x", padx=120, pady=8)

        # ── Weights preview (fetched from the trained model via upload_weights dry-run) ──
        preview_card = tk.Frame(self, bg=WHITE, padx=20, pady=16,
                                highlightthickness=1,
                                highlightbackground=BORDER)
        preview_card.pack(fill="x", padx=120, pady=(0, 16))

        tk.Label(preview_card, text="Model Weights Output",
                 font=("Helvetica", 12, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(preview_card,
                 text="Preview of the trained model weights (structure summary).",
                 font=("Helvetica", 9), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(2, 12))

        # Build a lightweight JSON preview from the real trained model
        preview_text = self._build_weights_preview()

        text_widget = tk.Text(preview_card, font=("Courier", 10),
                              bg=GRAY_LITE, fg=TEXT,
                              relief="flat", height=14,
                              padx=12, pady=12)
        text_widget.insert("1.0", preview_text)
        text_widget.config(state="disabled")
        text_widget.pack(fill="x")

        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(pady=16)

        styled_button(btn_row, "⬇  Download Weights as JSON",
                      self._download, secondary=True).pack(side="left", padx=(0, 12))
        styled_button(btn_row, "☁  Upload to Server →",
                      self._upload_to_server).pack(side="left")

    def _build_weights_preview(self):
        """
        Pulls the real weights from the trained model (train.py's global)
        and returns a JSON-formatted preview string.
        """
        trained_model = _train_module.trained_model
        last_config   = _train_module.last_config

        if trained_model is None:
            return json.dumps({"status": "no model trained yet"}, indent=2)

        try:
            weights = trained_model.get_weights()
            preview = {
                "model":          self.model,
                "epochs":         self.epochs,
                "config":         last_config,
                "layers":         len(weights),
                "shapes":         [list(w.shape) for w in weights],
                "sample_layer_0": weights[0].flatten()[:8].tolist() if weights else [],
            }
            return json.dumps(preview, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    def _download(self):
        """
        Saves the full trained model weights to a JSON file chosen by the user.
        Uses the real weights from train.py's global trained_model.
        """
        trained_model = _train_module.trained_model
        if trained_model is None:
            messagebox.showwarning("No Model", "No trained model available to download.")
            return

        try:
            weights = trained_model.get_weights()
            weights_data = {
                "model":   self.model,
                "epochs":  self.epochs,
                "weights": [w.tolist() for w in weights],
            }
        except Exception as e:
            messagebox.showerror("Error", f"Could not read weights:\n{e}")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"{self.model}_weights_e{self.epochs}.json",
            title="Save Weights"
        )
        if save_path:
            with open(save_path, "w") as f:
                json.dump(weights_data, f, indent=2)
            messagebox.showinfo("Saved", f"Weights saved to:\n{save_path}")

    def _upload_to_server(self):
        self.master.show_upload_server(self.model, self.epochs)

# ─────────────────────────────────────────
#  SERVER UPLOAD SCREEN  (unchanged visually)
# ─────────────────────────────────────────
class ServerUploadScreen(tk.Frame):
    def __init__(self, master, model, epochs):
        super().__init__(master, bg=BG)
        self.master = master
        self.model  = model
        self.epochs = epochs
        self.pack(fill="both", expand=True)

        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")
        header = tk.Frame(self, bg=GREEN_DARK)
        header.pack(fill="x")
        tk.Label(header, text="✚  MediCare Portal",
                 font=("Helvetica", 15, "bold"),
                 bg=GREEN_DARK, fg=WHITE, pady=14).pack()

        card = tk.Frame(self, bg=WHITE, padx=40, pady=30,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="x", padx=300, pady=60)

        tk.Label(card, text="Upload to Server",
                 font=("Helvetica", 16, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(card, text="Send your trained model weights to the server.",
                 font=("Helvetica", 10), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(4, 20))

        tk.Frame(card, height=1, bg=BORDER).pack(fill="x", pady=(0, 16))

        # Summary — pull real info from the trained model
        summary = tk.Frame(card, bg=GREEN_LITE,
                           highlightthickness=1,
                           highlightbackground=BORDER,
                           padx=16, pady=12)
        summary.pack(fill="x", pady=(0, 20))

        tk.Label(summary, text="Upload Summary",
                 font=("Helvetica", 10, "bold"), bg=GREEN_LITE, fg=GREEN_DARK).pack(anchor="w")

        try:
            trained_model = _train_module.trained_model
            num_layers = len(trained_model.get_weights()) if trained_model else 0
            size_bytes = sum(w.nbytes for w in trained_model.get_weights()) if trained_model else 0
            size_str   = f"{size_bytes:,} bytes"
        except Exception:
            num_layers = "—"
            size_str   = "—"

        for key, val in [
            ("Model",   self.model.title()),
            ("Epochs",  str(self.epochs)),
            ("Layers",  str(num_layers)),
            ("Size",    size_str),
        ]:
            row = tk.Frame(summary, bg=GREEN_LITE)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=key + ":",
                     font=("Helvetica", 10), bg=GREEN_LITE, fg=GRAY,
                     width=10, anchor="w").pack(side="left")
            tk.Label(row, text=val,
                     font=("Helvetica", 10, "bold"), bg=GREEN_LITE, fg=TEXT).pack(side="left")

        tk.Label(card, text="Server Endpoint",
                 font=("Helvetica", 10), bg=WHITE, fg=GRAY).pack(anchor="w")

        url_frame = tk.Frame(card, bg=WHITE,
                             highlightthickness=1,
                             highlightbackground=BORDER)
        url_frame.pack(fill="x", pady=(4, 20))
        self.url_entry = tk.Entry(url_frame, font=("Helvetica", 11),
                                  bg=WHITE, fg=TEXT, relief="flat",
                                  insertbackground=GREEN_DARK)
        self.url_entry.insert(0, "https://syntaxsurvival-technomist-2.onrender.com/send_weights")
        self.url_entry.pack(fill="x", ipady=8, padx=10)

        tk.Frame(card, height=1, bg=BORDER).pack(fill="x", pady=(0, 16))

        btn_row = tk.Frame(card, bg=WHITE)
        btn_row.pack(fill="x")
        styled_button(btn_row, "← Back",
                      lambda: self.master.show_result(self.model, self.master.filepath, self.epochs),
                      secondary=True).pack(side="left", padx=(0, 8))
        styled_button(btn_row, "Upload Now →",
                      self._start_upload).pack(side="right")

    def _start_upload(self):
        self.master.show_server_loading(self.model, self.epochs)

# ─────────────────────────────────────────
#  SERVER LOADING SCREEN
#  Calls upload_weights() from train.py
# ─────────────────────────────────────────
class ServerLoadingScreen(tk.Frame):
    def __init__(self, master, model, epochs):
        super().__init__(master, bg=BG)
        self.master  = master
        self.model   = model
        self.epochs  = epochs
        self._upload_result = None
        self._upload_done   = False
        self.pack(fill="both", expand=True)

        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")
        header = tk.Frame(self, bg=GREEN_DARK)
        header.pack(fill="x")
        tk.Label(header, text="✚  MediCare Portal",
                 font=("Helvetica", 15, "bold"),
                 bg=GREEN_DARK, fg=WHITE, pady=14).pack()

        center = tk.Frame(self, bg=BG)
        center.pack(expand=True)

        tk.Label(center, text="Uploading to Server",
                 font=("Helvetica", 20, "bold"), bg=BG, fg=TEXT).pack(pady=(0, 8))
        tk.Label(center, text="Sending model weights — please do not close the app.",
                 font=("Helvetica", 11), bg=BG, fg=GRAY).pack(pady=(0, 30))

        bar_bg = tk.Frame(center, bg=BORDER, height=12, width=400)
        bar_bg.pack(pady=(0, 8))
        bar_bg.pack_propagate(False)

        self.bar_fill = tk.Frame(bar_bg, bg=GREEN_DARK, height=12, width=0)
        self.bar_fill.place(x=0, y=0, relheight=1)

        self.pct_label = tk.Label(center, text="0%",
                                  font=("Helvetica", 11, "bold"),
                                  bg=BG, fg=GREEN_DARK)
        self.pct_label.pack()

        self.step_label = tk.Label(center, text="Connecting...",
                                   font=("Helvetica", 10), bg=BG, fg=GRAY)
        self.step_label.pack(pady=(6, 0))

        self._anim_start = time.time()
        self._animate()

        threading.Thread(target=self._do_upload, daemon=True).start()

    def _steps(self, pct):
        if pct < 15:  return "Connecting to server..."
        if pct < 35:  return "Authenticating..."
        if pct < 55:  return "Serializing weights..."
        if pct < 75:  return "Uploading data..."
        if pct < 90:  return "Verifying upload..."
        return "Finalizing..."

    def _animate(self):
        if self._upload_done:
            self.bar_fill.place(x=0, y=0, relheight=1, width=400)
            self.pct_label.config(text="100%")
            self.step_label.config(text="Done!")
            self.after(300, self._show_success)
            return

        elapsed = time.time() - self._anim_start
        pct = min(int((elapsed / 15) * 90), 90)
        self.bar_fill.place(x=0, y=0, relheight=1, width=int(400 * pct / 100))
        self.pct_label.config(text=f"{pct}%")
        self.step_label.config(text=self._steps(pct))
        self.after(200, self._animate)

    def _do_upload(self):
        """
        Calls upload_weights() from train.py which POSTs to
        SERVER_URL/send_weights with the real trained model weights.
        """
        try:
            result = upload_weights()
        except Exception as exc:
            result = {"error": str(exc)}

        self._upload_result = result
        self._upload_done   = True

    def _show_success(self):
        self.master.clear()
        UploadSuccessScreen(self.master, self.model, self.epochs, self._upload_result)

# ─────────────────────────────────────────
#  UPLOAD SUCCESS SCREEN
#  Shows server response from upload_weights()
# ─────────────────────────────────────────
class UploadSuccessScreen(tk.Frame):
    def __init__(self, master, model, epochs, server_response=None):
        super().__init__(master, bg=BG)
        self.master = master
        self.pack(fill="both", expand=True)

        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")
        header = tk.Frame(self, bg=GREEN_DARK)
        header.pack(fill="x")
        tk.Label(header, text="✚  MediCare Portal",
                 font=("Helvetica", 15, "bold"),
                 bg=GREEN_DARK, fg=WHITE, pady=14).pack()

        center = tk.Frame(self, bg=BG)
        center.pack(expand=True)

        # Determine success vs error from server response
        is_error = (
            isinstance(server_response, dict) and "error" in server_response
        ) or (
            isinstance(server_response, str) and (
                server_response.startswith("❌") or "failed" in server_response.lower()
            )
        ) or server_response is None

        icon_color = "#FEE2E2" if is_error else GREEN_LITE
        icon_border = "#F87171" if is_error else GREEN_MID
        icon_text  = "✗" if is_error else "✔"
        icon_fg    = "#B91C1C" if is_error else GREEN_DARK
        title_text = "Upload Failed" if is_error else "Upload Successful!"
        title_color = "#B91C1C" if is_error else GREEN_DARK

        icon_frame = tk.Frame(center, bg=icon_color,
                              highlightthickness=2,
                              highlightbackground=icon_border,
                              width=80, height=80)
        icon_frame.pack(pady=(0, 20))
        icon_frame.pack_propagate(False)
        tk.Label(icon_frame, text=icon_text, font=("Helvetica", 32, "bold"),
                 bg=icon_color, fg=icon_fg).place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(center, text=title_text,
                 font=("Helvetica", 22, "bold"), bg=BG, fg=title_color).pack(pady=(0, 8))

        if is_error:
            err_msg = server_response.get("error", str(server_response)) if isinstance(server_response, dict) else str(server_response)
            detail = err_msg
        else:
            detail = (f"Model weights for {model.title()} ({epochs} epochs)\n"
                      f"have been successfully uploaded to the server.")
        tk.Label(center, text=detail,
                 font=("Helvetica", 11), bg=BG, fg=GRAY, justify="center").pack(pady=(0, 12))

        # Show raw server response if available
        if server_response and isinstance(server_response, dict):
            resp_frame = tk.Frame(center, bg=GRAY_LITE,
                                  highlightthickness=1,
                                  highlightbackground=BORDER,
                                  padx=12, pady=10)
            resp_frame.pack(pady=(0, 20))
            tk.Label(resp_frame, text="Server Response:",
                     font=("Helvetica", 9, "bold"), bg=GRAY_LITE, fg=GRAY).pack(anchor="w")
            tk.Label(resp_frame,
                     text=json.dumps(server_response, indent=2),
                     font=("Courier", 9), bg=GRAY_LITE, fg=TEXT,
                     justify="left").pack(anchor="w")

        styled_button(center, "Return to Home", self.master.show_main).pack()


if __name__ == "__main__":
    app = App()
    app.mainloop()
