import threading
import time
import json
import os
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import tkinter.font as tkfont

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

    def show_result(self, model, filepath, epochs):
        self.filepath = filepath   # ✅ store it
        self.clear()
        ResultScreen(self, model, filepath, epochs)
        
    def show_upload_server(self, model, epochs, weights):
        self.clear()
        ServerUploadScreen(self, model, epochs, weights)
        
    def show_server_loading(self, model, epochs, weights):
        self.clear()
        ServerLoadingScreen(self, model, epochs, weights)

# ─────────────────────────────────────────
#  LOGIN SCREEN
# ─────────────────────────────────────────
class LoginScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.master = master
        self.pack(fill="both", expand=True)

        # Top accent bar
        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")

        # Logo / header area
        header = tk.Frame(self, bg=GREEN_DARK)
        header.pack(fill="x")
        tk.Label(header, text="✚  MediCare Portal",
                 font=("Helvetica", 17, "bold"),
                 bg=GREEN_DARK, fg=WHITE,
                 pady=18).pack()

        # Card
        card = tk.Frame(self, bg=WHITE, padx=40, pady=30,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="x", padx=120, pady=40)

        label(card, "Welcome back", size=16, bold=True).pack(anchor="w", pady=(0,4))
        label(card, "Sign in to access your medical portal",
              color=GRAY).pack(anchor="w", pady=(0,20))

        # Username
        label(card, "Username or Staff ID", size=10, color=GRAY).pack(anchor="w")
        self.username = styled_entry(card)
        self.username.pack(fill="x", pady=(4, 14), ipady=6)

        # Password
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
#  TERMS & CONDITIONS SCREEN
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

        # Scrollable text box
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

        # Checkbox + buttons
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
#  MAIN SCREEN
# ─────────────────────────────────────────
class MainScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)

        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")

        # Header
        header = tk.Frame(self, bg=GREEN_DARK)
        header.pack(fill="x")
        tk.Label(header, text="✚  MediCare Portal",
                 font=("Helvetica", 15, "bold"),
                 bg=GREEN_DARK, fg=WHITE, pady=14).pack()

        # Search bar
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

        # Section label
        tk.Label(self, text="Select a diagnostic model",
                 font=("Helvetica", 12, "bold"), bg=BG, fg=TEXT).pack(pady=(8, 12))

        # Model cards row
        self.selected = tk.StringVar(value="")

        cards_frame = tk.Frame(self, bg=BG)
        cards_frame.pack(padx=200, fill="x")

        self.card_frames = {}
        models = [
            ("tumor",   "Tumor Detection",      "Analyzes imaging data to identify and classify tumor regions."),
            ("heart",   "Heart Disease Model",  "Evaluates cardiac indicators to assess heart disease risk."),
        ]

        for key, title, desc in models:
            self._make_card(cards_frame, key, title, desc)

        # Custom model option
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

        # Proceed button
        styled_button(self, "Proceed with Selected Model →",
                      self._proceed).pack(pady=28)

        # Status label
        self.status = tk.Label(self, text="", font=("Helvetica", 10),
                               bg=BG, fg=GRAY)
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

        title_label = tk.Label(card, text=title,
                               font=("Helvetica", 13, "bold"),
                               bg=WHITE, fg=GREEN_DARK)
        title_label.pack(anchor="w")

        desc_label = tk.Label(card, text=desc,
                              font=("Helvetica", 9),
                              bg=WHITE, fg=GRAY,
                              wraplength=220, justify="left")
        desc_label.pack(anchor="w", pady=(4, 10))

        select_btn = tk.Button(card, text="Select",
                               font=("Helvetica", 10),
                               bg=GREEN_LITE, fg=GREEN_DARK,
                               activebackground=GREEN_MID,
                               activeforeground=WHITE,
                               relief="flat", cursor="hand2",
                               command=lambda k=key, c=card, t=title: self._select(k, c, t))
        select_btn.pack(anchor="w")

        self.card_frames[key] = card
        return card

    def _select(self, key, card, title):
        # Reset all cards
        for k, c in self.card_frames.items():
            c.config(highlightbackground=BORDER, highlightthickness=2, bg=WHITE)
            for child in c.winfo_children():
                child.config(bg=WHITE)

        # Highlight selected
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

        # Add new card below existing ones in a new row
        container = list(self.card_frames.values())[0].master
        new_frame = tk.Frame(self, bg=BG)
        new_frame.pack(padx=200, fill="x", pady=(0, 4))

        self._make_card.__func__
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

        # Clear entry
        self.custom_entry.delete(0, "end")
        self._restore_placeholder(None)
        self.status.config(text=f'Model "{name}" added.', fg=GREEN_MID)

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

        # Card
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
        tk.Label(card, text="Accepted formats: .json, .csv",
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

        # ── Buttons ──
        btn_row = tk.Frame(card, bg=WHITE)
        btn_row.pack(fill="x")
        styled_button(
            btn_row,
            "← Back",
            lambda: self.master.show_result(self.model, self.master.filepath, self.epochs),
            secondary=True
        ).pack(side="left", padx=(0, 8))
        styled_button(btn_row, "Run Model →", self._run).pack(side="right")
        self.unbind_all("<Return>")

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select Dataset",
            filetypes=[("JSON files", "*.json"),
                       ("CSV files", "*.csv"),
                       ("All files", "*.*")]
        )
        if path:
            self.filepath = path
            self.file_label.config(text=f"✔  {os.path.basename(path)}", fg=GREEN_DARK)

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
# ─────────────────────────────────────────
class LoadingScreen(tk.Frame):
    def __init__(self, master, model, filepath, epochs):
        super().__init__(master, bg=BG)
        self.master = master
        self.model = model
        self.filepath = filepath
        self.epochs = epochs 
        self.pack(fill="both", expand=True)

        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")
        header = tk.Frame(self, bg=GREEN_DARK)
        header.pack(fill="x")
        tk.Label(header, text="✚  MediCare Portal",
                 font=("Helvetica", 15, "bold"),
                 bg=GREEN_DARK, fg=WHITE, pady=14).pack()

        # Center content
        center = tk.Frame(self, bg=BG)
        center.pack(expand=True)

        tk.Label(center, text="Processing Dataset",
                 font=("Helvetica", 20, "bold"), bg=BG, fg=TEXT).pack(pady=(0, 8))
        tk.Label(center, text=f"Running {self.model.title()} model — please wait...",
                 font=("Helvetica", 11), bg=BG, fg=GRAY).pack(pady=(0, 30))

        # Progress bar (manual)
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

        # Start processing in background
        self.duration = 10
        self.start_time = time.time()
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
        elapsed = time.time() - self.start_time
        pct = min(int((elapsed / self.duration) * 100), 99)
        self.bar_fill.place(x=0, y=0, relheight=1, width=int(400 * pct / 100))
        self.pct_label.config(text=f"{pct}%")
        self.step_label.config(text=self._steps(pct))
        if elapsed < self.duration:
            self.after(100, self._animate)

    def _process(self):
        time.sleep(self.duration)
        self.after(0, lambda: self.master.show_result(self.model, self.filepath, self.epochs))


# ─────────────────────────────────────────
#  RESULT SCREEN
# ─────────────────────────────────────────
class ResultScreen(tk.Frame):
    def __init__(self, master, model, filepath, epochs):
        super().__init__(master, bg=BG)
        self.master   = master
        self.model    = model
        self.filepath = filepath
        self.epochs   = epochs
        self.weights  = None
        self.pack(fill="both", expand=True)

        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")
        header = tk.Frame(self, bg=GREEN_DARK)
        header.pack(fill="x")
        tk.Label(header, text="✚  MediCare Portal",
                 font=("Helvetica", 15, "bold"),
                 bg=GREEN_DARK, fg=WHITE, pady=14).pack()

        # Top row
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=120, pady=(20, 4))
        tk.Label(top, text="Training Complete",
                 font=("Helvetica", 16, "bold"), bg=BG, fg=TEXT).pack(side="left")
        styled_button(top, "⟵ Run Another", self.master.show_main,
                      secondary=True).pack(side="right")

        tk.Label(self,
                 text=f"Model: {model.title()}  •  File: {os.path.basename(filepath)}  •  Epochs: {epochs}",
                 font=("Helvetica", 10), bg=BG, fg=GRAY).pack(anchor="w", padx=120)

        tk.Frame(self, height=1, bg=BORDER).pack(fill="x", padx=120, pady=12)

        # Weights preview card
        preview_card = tk.Frame(self, bg=WHITE, padx=20, pady=16,
                                highlightthickness=1,
                                highlightbackground=BORDER)
        preview_card.pack(fill="x", padx=120, pady=(0, 16))

        tk.Label(preview_card, text="Model Weights Output",
                 font=("Helvetica", 12, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(preview_card, text="Preview of the generated weights JSON (first 6 keys shown).",
                 font=("Helvetica", 9), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(2, 12))

        self.weights = self._generate_weights()

        preview = dict(list(self.weights.items())[:6])
        text_widget = tk.Text(preview_card, font=("Courier", 10),
                              bg=GRAY_LITE, fg=TEXT,
                              relief="flat", height=14,
                              padx=12, pady=12)
        text_widget.insert("1.0", json.dumps(preview, indent=2))
        text_widget.config(state="disabled")
        text_widget.pack(fill="x")

        # Download
        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(pady=16)

        styled_button(btn_row, "⬇  Download Weights as JSON",
                    self._download, secondary=True).pack(side="left", padx=(0, 12))
        styled_button(btn_row, "☁  Upload to Server →",
                    self._upload_to_server).pack(side="left")

    def _generate_weights(self):
        """
        Placeholder — replace this with your actual backend call.
        Simulates a weights JSON output based on model + epochs.
        """
        import random
        random.seed(42)
        layers = {
            "tumor":  ["conv1", "conv2", "conv3", "fc1", "fc2", "output"],
            "heart":  ["input_layer", "dense1", "dense2", "dense3", "output"],
        }.get(self.model, ["layer1", "layer2", "layer3", "output"])

        weights = {
            "model":  self.model,
            "epochs": self.epochs,
            "file":   os.path.basename(self.filepath),
        }
        for layer in layers:
            weights[layer] = {
                "weights": [round(random.uniform(-1, 1), 6)
                            for _ in range(8)],
                "bias":    [round(random.uniform(-0.5, 0.5), 6)
                            for _ in range(4)],
                "trained_epochs": self.epochs,
            }
        return weights

    def _download(self):
        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"{self.model}_weights_e{self.epochs}.json",
            title="Save Weights"
        )
        if save_path:
            with open(save_path, "w") as f:
                json.dump(self.weights, f, indent=2)
            messagebox.showinfo("Saved", f"Weights saved to:\n{save_path}")    
            
            
    def _upload_to_server(self):
        self.master.show_upload_server(self.model, self.epochs, self.weights)     
        
# ─────────────────────────────────────────
#  SERVER UPLOAD SCREEN
# ─────────────────────────────────────────
class ServerUploadScreen(tk.Frame):
    def __init__(self, master, model, epochs, weights):
        super().__init__(master, bg=BG)
        self.master  = master
        self.model   = model
        self.epochs  = epochs
        self.weights = weights
        self.pack(fill="both", expand=True)

        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")
        header = tk.Frame(self, bg=GREEN_DARK)
        header.pack(fill="x")
        tk.Label(header, text="✚  MediCare Portal",
                 font=("Helvetica", 15, "bold"),
                 bg=GREEN_DARK, fg=WHITE, pady=14).pack()

        # Card
        card = tk.Frame(self, bg=WHITE, padx=40, pady=30,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="x", padx=300, pady=60)

        tk.Label(card, text="Upload to Server",
                 font=("Helvetica", 16, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(card, text="Send your trained model weights to the server.",
                 font=("Helvetica", 10), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(4, 20))

        tk.Frame(card, height=1, bg=BORDER).pack(fill="x", pady=(0, 16))

        # Summary
        summary = tk.Frame(card, bg=GREEN_LITE,
                           highlightthickness=1,
                           highlightbackground=BORDER,
                           padx=16, pady=12)
        summary.pack(fill="x", pady=(0, 20))

        tk.Label(summary, text="Upload Summary",
                 font=("Helvetica", 10, "bold"), bg=GREEN_LITE, fg=GREEN_DARK).pack(anchor="w")

        for key, val in [
            ("Model",   self.model.title()),
            ("Epochs",  str(self.epochs)),
            ("Layers",  str(len(self.weights) - 3)),  # minus meta keys
            ("Size",    f"{len(json.dumps(self.weights))} bytes"),
        ]:
            row = tk.Frame(summary, bg=GREEN_LITE)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=key + ":",
                     font=("Helvetica", 10), bg=GREEN_LITE, fg=GRAY,
                     width=10, anchor="w").pack(side="left")
            tk.Label(row, text=val,
                     font=("Helvetica", 10, "bold"), bg=GREEN_LITE, fg=TEXT).pack(side="left")

        # Server URL
        tk.Label(card, text="Server Endpoint",
                 font=("Helvetica", 10), bg=WHITE, fg=GRAY).pack(anchor="w")

        url_frame = tk.Frame(card, bg=WHITE,
                             highlightthickness=1,
                             highlightbackground=BORDER)
        url_frame.pack(fill="x", pady=(4, 20))
        self.url_entry = tk.Entry(url_frame, font=("Helvetica", 11),
                                  bg=WHITE, fg=TEXT, relief="flat",
                                  insertbackground=GREEN_DARK)
        self.url_entry.insert(0, "https://api.medicare-server.com/upload")
        self.url_entry.pack(fill="x", ipady=8, padx=10)

        tk.Frame(card, height=1, bg=BORDER).pack(fill="x", pady=(0, 16))

        btn_row = tk.Frame(card, bg=WHITE)
        btn_row.pack(fill="x")
        styled_button(btn_row, "← Back", lambda: self.master.show_result(
                      self.model, None, self.epochs),
                      secondary=True).pack(side="left", padx=(0, 8))
        styled_button(btn_row, "Upload Now →",
                      self._start_upload).pack(side="right")

    def _start_upload(self):
        self.master.show_server_loading(self.model, self.epochs, self.weights)


# ─────────────────────────────────────────
#  SERVER LOADING SCREEN
# ─────────────────────────────────────────
class ServerLoadingScreen(tk.Frame):
    def __init__(self, master, model, epochs, weights):
        super().__init__(master, bg=BG)
        self.master  = master
        self.model   = model
        self.epochs  = epochs
        self.weights = weights
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

        # Progress bar
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

        self.duration   = 8
        self.start_time = time.time()
        self._animate()

        threading.Thread(target=self._upload, daemon=True).start()

    def _steps(self, pct):
        if pct < 15:  return "Connecting to server..."
        if pct < 35:  return "Authenticating..."
        if pct < 55:  return "Serializing weights..."
        if pct < 75:  return "Uploading data..."
        if pct < 90:  return "Verifying upload..."
        return "Finalizing..."

    def _animate(self):
        elapsed = time.time() - self.start_time
        pct = min(int((elapsed / self.duration) * 100), 99)
        self.bar_fill.place(x=0, y=0, relheight=1, width=int(400 * pct / 100))
        self.pct_label.config(text=f"{pct}%")
        self.step_label.config(text=self._steps(pct))
        if elapsed < self.duration:
            self.after(100, self._animate)

    def _upload(self):
        time.sleep(self.duration)
        self.after(0, self._show_success)

    def _show_success(self):
        self.master.clear()
        UploadSuccessScreen(self.master, self.model, self.epochs)


# ─────────────────────────────────────────
#  UPLOAD SUCCESS SCREEN
# ─────────────────────────────────────────
class UploadSuccessScreen(tk.Frame):
    def __init__(self, master, model, epochs):
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

        # Success icon
        icon_frame = tk.Frame(center, bg=GREEN_LITE,
                              highlightthickness=2,
                              highlightbackground=GREEN_MID,
                              width=80, height=80)
        icon_frame.pack(pady=(0, 20))
        icon_frame.pack_propagate(False)
        tk.Label(icon_frame, text="✔", font=("Helvetica", 32, "bold"),
                 bg=GREEN_LITE, fg=GREEN_DARK).place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(center, text="Upload Successful!",
                 font=("Helvetica", 22, "bold"), bg=BG, fg=GREEN_DARK).pack(pady=(0, 8))
        tk.Label(center, text=f"Model weights for {model.title()} ({epochs} epochs)\nhave been successfully uploaded to the server.",
                 font=("Helvetica", 11), bg=BG, fg=GRAY, justify="center").pack(pady=(0, 30))

        styled_button(center, "Return to Home", self.master.show_main).pack()        

   
if __name__ == "__main__":
    app = App()
    app.mainloop()
