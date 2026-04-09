import threading
import time
import json
import os
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import tkinter.font as tkfont

# ─────────────────────────────────────────
#  IMPORT APP LOGIC
# ─────────────────────────────────────────
import training as _train_module
from training import train_and_upload, upload_weights, predict_disease, detect_data_type, get_models, add_model_to_server

# ─────────────────────────────────────────
#  MODEL ID MAPPING
# ─────────────────────────────────────────
MODEL_ID_MAP = {
    "tumor": "xray",
    "heart": "heart",
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
        self.filepath = None
        self.train_result = None
        self.upload_result = None
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

    def show_test(self, model, epochs):
        self.clear()
        TestScreen(self, model, epochs)

# ─────────────────────────────────────────
#  LOGIN SCREEN
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
#  TERMS SCREEN
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
#  MAIN SCREEN
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

        self.status = tk.Label(self, text="", font=("Helvetica", 10),
                               bg=BG, fg=GRAY)

        self.status.config(text="Loading models from server...", fg=GRAY)
        self.update()
        models = get_models()
        self.status.config(text="")

        self.model_data = {}

        for key, title, desc in models:
            card = self._make_card(cards_frame, key, title, desc)
            self.model_data[key] = {
                "title": title.lower(),
                "desc": desc.lower(),
                "card": card
    }

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

    def do_search(self):
        query = self.search_var.get().strip().lower()
        if not query:
            for data in self.model_data.values():
                data["card"].pack_forget()
                data["card"].pack(side="left", expand=True, fill="x", padx=(0, 12))
            self.status.config(text="")
            return

        found = False
        for key, data in self.model_data.items():
            card = data["card"]
            if query in data["title"] or query in data["desc"]:
                card.pack_forget()
                card.pack(side="left", expand=True, fill="x", padx=(0, 12))
                found = True
            else:
                card.pack_forget()

        if found:
            self.status.config(text=f'Results for "{query}"', fg=GREEN_DARK)
        else:
            self.status.config(text="No matching models found.", fg="red")

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

        self.status.config(text=f'Adding "{name}" to server...', fg=GRAY)
        self.update()
        success, message = add_model_to_server(name, model_type="tabular")

        if not success:
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

        tk.Label(card, text="Dataset File",
                 font=("Helvetica", 11, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")

        if self.model in ("tumor", "xray"):
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
        if self.model in ("tumor", "xray"):
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
            self.bar_fill.place(x=0, y=0, relheight=1, width=400)
            self.pct_label.config(text="100%")
            self.step_label.config(text="Complete!")
            self.after(300, lambda: self.master.show_result(
                self.model, self.filepath, self.epochs, self._train_result))
            return

        elapsed = time.time() - self._anim_start
        pct = min(int((elapsed / 30) * 95), 95)
        self.bar_fill.place(x=0, y=0, relheight=1, width=int(400 * pct / 100))
        self.pct_label.config(text=f"{pct}%")
        self.step_label.config(text=self._steps(pct))
        self.after(200, self._animate)

    def _process(self):
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
        self._train_done   = True

# ─────────────────────────────────────────
#  TRAINING CHART
# ─────────────────────────────────────────
class TrainingChart(tk.Frame):
    W = 700
    H = 220
    PAD_L = 54
    PAD_R = 20
    PAD_T = 16
    PAD_B = 40

    def __init__(self, parent, history: dict):
        super().__init__(parent, bg=WHITE)

        acc_key  = "accuracy" if "accuracy" in history else "acc"
        loss_key = "loss"

        acc_vals  = history.get(acc_key, [])
        loss_vals = history.get(loss_key, [])
        n = max(len(acc_vals), len(loss_vals), 1)

        legend = tk.Frame(self, bg=WHITE)
        legend.pack(anchor="w", padx=8, pady=(8, 2))
        self._legend_dot(legend, "#185FA5", "Accuracy (left axis)")
        tk.Label(legend, text="   ", bg=WHITE).pack(side="left")
        self._legend_dash(legend, "#D85A30", "Loss (right axis)")

        self.cv = tk.Canvas(self, width=self.W, height=self.H,
                            bg=WHITE, highlightthickness=0)
        self.cv.pack(padx=8, pady=(0, 8))

        self._draw(acc_vals, loss_vals, n)

    def _legend_dot(self, parent, color, text):
        c = tk.Canvas(parent, width=14, height=14,
                      bg=WHITE, highlightthickness=0)
        c.pack(side="left")
        c.create_oval(2, 4, 12, 14, fill=color, outline="")
        tk.Label(parent, text=text, font=("Helvetica", 9),
                 bg=WHITE, fg=GRAY).pack(side="left")

    def _legend_dash(self, parent, color, text):
        c = tk.Canvas(parent, width=20, height=14,
                      bg=WHITE, highlightthickness=0)
        c.pack(side="left")
        c.create_line(0, 9, 20, 9, fill=color, width=2, dash=(5, 3))
        tk.Label(parent, text=text, font=("Helvetica", 9),
                 bg=WHITE, fg=GRAY).pack(side="left")

    def _px(self, i, n):
        plot_w = self.W - self.PAD_L - self.PAD_R
        return self.PAD_L + (i / max(n - 1, 1)) * plot_w

    def _py_acc(self, v):
        plot_h = self.H - self.PAD_T - self.PAD_B
        return self.PAD_T + (1.0 - v) * plot_h

    def _py_loss(self, v, loss_max):
        plot_h = self.H - self.PAD_T - self.PAD_B
        return self.PAD_T + (1.0 - v / max(loss_max, 1e-6)) * plot_h

    def _draw(self, acc_vals, loss_vals, n):
        cv = self.cv
        plot_h = self.H - self.PAD_T - self.PAD_B
        plot_w = self.W - self.PAD_L - self.PAD_R

        for frac, lbl in [(0.0, "100%"), (0.25, "75%"),
                          (0.5, "50%"),  (0.75, "25%"), (1.0, "0%")]:
            y = self.PAD_T + frac * plot_h
            cv.create_line(self.PAD_L, y, self.W - self.PAD_R, y,
                           fill="#E5E7EB", dash=(4, 4))
            cv.create_text(self.PAD_L - 6, y,
                           text=lbl, anchor="e",
                           font=("Helvetica", 8), fill="#185FA5")

        tick_every = max(1, n // 8)
        for i in range(0, n, tick_every):
            x = self._px(i, n)
            cv.create_text(x, self.H - self.PAD_B + 8,
                           text=str(i + 1),
                           font=("Helvetica", 8), fill=GRAY)
        cv.create_text(self._px(n - 1, n), self.H - self.PAD_B + 8,
                       text=str(n), font=("Helvetica", 8), fill=GRAY)

        cv.create_text(self.PAD_L + plot_w / 2, self.H - 6,
                       text="Epoch", font=("Helvetica", 9), fill=GRAY)

        cv.create_rectangle(self.PAD_L, self.PAD_T,
                            self.W - self.PAD_R, self.H - self.PAD_B,
                            outline="#D1D5DB", width=1)

        loss_max = max(loss_vals) if loss_vals else 1.0
        loss_max = max(loss_max, 0.01)
        for frac, val in [(0.0, loss_max), (0.5, loss_max / 2), (1.0, 0.0)]:
            y = self.PAD_T + frac * plot_h
            cv.create_text(self.W - self.PAD_R + 6, y,
                           text=f"{val:.2f}", anchor="w",
                           font=("Helvetica", 8), fill="#D85A30")
        cv.create_text(self.W - 10, self.PAD_T + plot_h / 2,
                       text="Loss", font=("Helvetica", 8),
                       fill="#D85A30", angle=270)

        if len(acc_vals) >= 2:
            pts = []
            for i, v in enumerate(acc_vals):
                pts += [self._px(i, len(acc_vals)), self._py_acc(min(max(v, 0), 1))]
            cv.create_line(*pts, fill="#185FA5", width=2, smooth=True)
            for i, v in enumerate(acc_vals):
                x = self._px(i, len(acc_vals))
                y = self._py_acc(min(max(v, 0), 1))
                cv.create_oval(x - 3, y - 3, x + 3, y + 3,
                               fill="#185FA5", outline="")

        if len(loss_vals) >= 2:
            pts = []
            for i, v in enumerate(loss_vals):
                pts += [self._px(i, len(loss_vals)),
                        self._py_loss(max(v, 0), loss_max)]
            cv.create_line(*pts, fill="#D85A30", width=2,
                           dash=(6, 3), smooth=True)

        if acc_vals:
            fin_acc = acc_vals[-1]
            cv.create_text(self._px(len(acc_vals) - 1, len(acc_vals)) - 4,
                           self._py_acc(min(max(fin_acc, 0), 1)) - 10,
                           text=f"{fin_acc*100:.1f}%",
                           font=("Helvetica", 8, "bold"), fill="#185FA5")
        if loss_vals:
            fin_loss = loss_vals[-1]
            cv.create_text(self._px(len(loss_vals) - 1, len(loss_vals)) - 4,
                           self._py_loss(max(fin_loss, 0), loss_max) - 10,
                           text=f"{fin_loss:.4f}",
                           font=("Helvetica", 8, "bold"), fill="#D85A30")


# ─────────────────────────────────────────
#  RESULT SCREEN
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

        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(outer)
        scrollbar.pack(side="right", fill="y")

        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0,
                           yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=canvas.yview)

        body = tk.Frame(canvas, bg=BG)
        body_win = canvas.create_window((0, 0), window=body, anchor="nw")

        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        body.bind("<Configure>", _on_configure)

        def _on_canvas_resize(e):
            canvas.itemconfig(body_win, width=e.width)
        canvas.bind("<Configure>", _on_canvas_resize)

        def _on_mousewheel(e):
            if e.num == 4:
                canvas.yview_scroll(-1, "units")
            elif e.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>",   _on_mousewheel)
        canvas.bind("<Button-5>",   _on_mousewheel)

        def _bind_children(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>",   _on_mousewheel)
            widget.bind("<Button-5>",   _on_mousewheel)
            for child in widget.winfo_children():
                _bind_children(child)

        body.bind("<Configure>", lambda e: (_on_configure(e), _bind_children(body)))

        top = tk.Frame(body, bg=BG)
        top.pack(fill="x", padx=120, pady=(20, 4))
        tk.Label(top, text="Training Complete",
                 font=("Helvetica", 16, "bold"), bg=BG, fg=TEXT).pack(side="left")
        styled_button(top, "⟵ Run Another", self.master.show_main,
                      secondary=True).pack(side="right")

        fname = os.path.basename(filepath) if filepath else "—"
        tk.Label(body,
                 text=f"Model: {model.title()}  •  File: {fname}  •  Epochs: {epochs}",
                 font=("Helvetica", 10), bg=BG, fg=GRAY).pack(anchor="w", padx=120)

        result_text  = train_result if train_result else "No result returned."
        result_color = GREEN_DARK if "completed" in str(result_text).lower() else "#B91C1C"

        result_banner = tk.Frame(body, bg=WHITE, padx=20, pady=12,
                                 highlightthickness=1,
                                 highlightbackground=BORDER)
        result_banner.pack(fill="x", padx=120, pady=(12, 8))
        tk.Label(result_banner, text="Training Result",
                 font=("Helvetica", 11, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(result_banner, text=result_text,
                 font=("Helvetica", 11), bg=WHITE, fg=result_color).pack(anchor="w", pady=(4, 0))

        tk.Frame(body, height=1, bg=BORDER).pack(fill="x", padx=120, pady=8)

        history = _train_module.last_history

        chart_card = tk.Frame(body, bg=WHITE, padx=20, pady=16,
                              highlightthickness=1,
                              highlightbackground=BORDER)
        chart_card.pack(fill="x", padx=120, pady=(0, 12))

        tk.Label(chart_card, text="Training Performance",
                 font=("Helvetica", 12, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(chart_card,
                 text="Accuracy and loss recorded over each training epoch.",
                 font=("Helvetica", 9), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(2, 12))

        if history:
            badge_row = tk.Frame(chart_card, bg=WHITE)
            badge_row.pack(anchor="w", pady=(0, 10))

            acc_key  = "accuracy" if "accuracy" in history else "acc"
            acc_vals  = history.get(acc_key, [])
            loss_vals = history.get("loss", [])

            for lbl, val, color in [
                ("Final Accuracy",
                 f"{acc_vals[-1]*100:.1f}%" if acc_vals else "—",
                 "#185FA5"),
                ("Final Loss",
                 f"{loss_vals[-1]:.4f}" if loss_vals else "—",
                 "#D85A30"),
                ("Best Accuracy",
                 f"{max(acc_vals)*100:.1f}%" if acc_vals else "—",
                 GREEN_DARK),
                ("Epochs Run",
                 str(len(acc_vals) or len(loss_vals)),
                 GRAY),
            ]:
                b = tk.Frame(badge_row, bg=GRAY_LITE,
                             highlightthickness=1,
                             highlightbackground=BORDER,
                             padx=12, pady=6)
                b.pack(side="left", padx=(0, 8))
                tk.Label(b, text=lbl, font=("Helvetica", 8),
                         bg=GRAY_LITE, fg=GRAY).pack(anchor="w")
                tk.Label(b, text=val, font=("Helvetica", 12, "bold"),
                         bg=GRAY_LITE, fg=color).pack(anchor="w")

            TrainingChart(chart_card, history).pack(fill="x")
        else:
            tk.Label(chart_card,
                     text="No training history available.\n"
                          "Make sure training.py returns history from model.fit().",
                     font=("Helvetica", 10), bg=WHITE, fg=GRAY,
                     justify="left").pack(anchor="w", pady=16)

        tk.Frame(body, height=1, bg=BORDER).pack(fill="x", padx=120, pady=8)

        preview_card = tk.Frame(body, bg=WHITE, padx=20, pady=16,
                                highlightthickness=1,
                                highlightbackground=BORDER)
        preview_card.pack(fill="x", padx=120, pady=(0, 16))

        tk.Label(preview_card, text="Model Weights Output",
                 font=("Helvetica", 12, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(preview_card,
                 text="Preview of the trained model weights (structure summary).",
                 font=("Helvetica", 9), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(2, 12))

        preview_text = self._build_weights_preview()

        text_widget = tk.Text(preview_card, font=("Courier", 10),
                              bg=GRAY_LITE, fg=TEXT,
                              relief="flat", height=14,
                              padx=12, pady=12)
        text_widget.insert("1.0", preview_text)
        text_widget.config(state="disabled")
        text_widget.pack(fill="x")

        btn_row = tk.Frame(body, bg=BG)
        btn_row.pack(pady=16)

        styled_button(btn_row, "⬇  Download Weights as JSON",
                      self._download, secondary=True).pack(side="left", padx=(0, 12))
        styled_button(btn_row, "🧪  Test on New Data",
                      self._test, secondary=True).pack(side="left", padx=(0, 12))
        styled_button(btn_row, "☁  Upload to Server →",
                      self._upload_to_server).pack(side="left")

    def _build_weights_preview(self):
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

    def _test(self):
        self.master.show_test(self.model, self.epochs)

    def _upload_to_server(self):
        self.master.show_upload_server(self.model, self.epochs)

# ─────────────────────────────────────────
#  TEST SCREEN  — FIXED scroll + chart
# ─────────────────────────────────────────
class TestScreen(tk.Frame):
    def __init__(self, master, model, epochs):
        super().__init__(master, bg=BG)
        self.master   = master
        self.model    = model
        self.epochs   = epochs
        self.filepath = None
        self._results = []
        self.pack(fill="both", expand=True)

        tk.Frame(self, height=5, bg=GREEN_DARK).pack(fill="x")
        header = tk.Frame(self, bg=GREEN_DARK)
        header.pack(fill="x")
        tk.Label(header, text="✚  MediCare Portal",
                 font=("Helvetica", 15, "bold"),
                 bg=GREEN_DARK, fg=WHITE, pady=14).pack()

        # ── Scrollable body ──────────────────────────────────────────────
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True)

        sb = tk.Scrollbar(outer)
        sb.pack(side="right", fill="y")

        # Store canvas as instance variable so _bind_scroll can reach it
        self._scroll_cv = tk.Canvas(outer, bg=BG, highlightthickness=0,
                                    yscrollcommand=sb.set)
        self._scroll_cv.pack(side="left", fill="both", expand=True)
        sb.config(command=self._scroll_cv.yview)

        body = tk.Frame(self._scroll_cv, bg=BG)
        body_win = self._scroll_cv.create_window((0, 0), window=body, anchor="nw")

        # FIX: define callbacks as proper methods at the right scope level
        def _on_cfg(e):
            self._scroll_cv.configure(scrollregion=self._scroll_cv.bbox("all"))

        def _on_rsz(e):
            self._scroll_cv.itemconfig(body_win, width=e.width)

        # FIX: _mw defined cleanly at class level via instance method
        body.bind("<Configure>", _on_cfg)
        self._scroll_cv.bind("<Configure>", _on_rsz)
        self._scroll_cv.bind("<MouseWheel>", self._mw)
        self._scroll_cv.bind("<Button-4>",   self._mw)
        self._scroll_cv.bind("<Button-5>",   self._mw)

        # ── Title ──
        top = tk.Frame(body, bg=BG)
        top.pack(fill="x", padx=120, pady=(20, 4))
        tk.Label(top, text="Test on New Data",
                 font=("Helvetica", 16, "bold"), bg=BG, fg=TEXT).pack(side="left")
        styled_button(top, "⟵ Back to Results",
                      lambda: master.show_result(model, master.filepath, epochs),
                      secondary=True).pack(side="right")

        tk.Label(body,
                 text=f"Model: {model.title()}  •  Trained for {epochs} epoch(s)",
                 font=("Helvetica", 10), bg=BG, fg=GRAY).pack(anchor="w", padx=120)

        # ── File upload card ──
        card = tk.Frame(body, bg=WHITE, padx=30, pady=24,
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", padx=120, pady=(16, 8))

        tk.Label(card, text="Select Test Dataset",
                 font=("Helvetica", 12, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")

        is_image = model in ("tumor", "xray")
        hint = ("Select the image folder to test on." if is_image
                else "Select a CSV file. The last column is treated as the label (ground truth).")
        tk.Label(card, text=hint,
                 font=("Helvetica", 9), bg=WHITE, fg=GRAY,
                 wraplength=600, justify="left").pack(anchor="w", pady=(2, 12))

        drop_zone = tk.Frame(card, bg=GREEN_LITE,
                             highlightthickness=1, highlightbackground=BORDER,
                             pady=18, padx=20)
        drop_zone.pack(fill="x", pady=(0, 16))

        tk.Label(drop_zone, text="📂", font=("Helvetica", 22), bg=GREEN_LITE).pack()
        self.file_label = tk.Label(drop_zone, text="No file selected",
                                   font=("Helvetica", 10), bg=GREEN_LITE, fg=GRAY)
        self.file_label.pack(pady=(4, 8))
        styled_button(drop_zone, "Browse", self._browse).pack()

        run_row = tk.Frame(card, bg=WHITE)
        run_row.pack(fill="x", pady=(8, 0))
        self.run_btn = styled_button(run_row, "▶  Run Predictions", self._run)
        self.run_btn.pack(side="right")

        tk.Frame(body, height=1, bg=BORDER).pack(fill="x", padx=120, pady=8)

        # ── Results area ──
        self.results_card = tk.Frame(body, bg=WHITE, padx=30, pady=24,
                                     highlightthickness=1, highlightbackground=BORDER)
        self.results_card.pack(fill="x", padx=120, pady=(0, 24))

        tk.Label(self.results_card, text="Prediction Results",
                 font=("Helvetica", 12, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(self.results_card,
                 text="Results will appear here after running predictions.",
                 font=("Helvetica", 9), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(2, 0))

        self.results_body = tk.Frame(self.results_card, bg=WHITE)
        self.results_body.pack(fill="x", pady=(12, 0))

    # ── FIX: _mw is now a proper instance method, always available ──
    def _mw(self, e):
        if e.num == 4:
            self._scroll_cv.yview_scroll(-1, "units")
        elif e.num == 5:
            self._scroll_cv.yview_scroll(1, "units")
        else:
            self._scroll_cv.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def _bind_scroll(self, widget):
        """Recursively bind mousewheel scroll to all child widgets."""
        widget.bind("<MouseWheel>", self._mw)
        widget.bind("<Button-4>",   self._mw)
        widget.bind("<Button-5>",   self._mw)
        for child in widget.winfo_children():
            self._bind_scroll(child)

    def _browse(self):
        is_image = self.model in ("tumor", "xray")
        if is_image:
            path = filedialog.askdirectory(title="Select Test Image Folder")
        else:
            path = filedialog.askopenfilename(
                title="Select Test CSV",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
        if path:
            self.filepath = path
            self.file_label.config(text=f"✔  {os.path.basename(path)}", fg=GREEN_DARK)

    def _run(self):
        if _train_module.trained_model is None:
            messagebox.showwarning("No Model",
                                   "No trained model found.\nPlease train a model first.")
            return
        if not self.filepath:
            messagebox.showwarning("No File", "Please select a test dataset first.")
            return

        self.run_btn.config(state="disabled", text="Running…")
        self.update()

        for w in self.results_body.winfo_children():
            w.destroy()

        threading.Thread(target=self._predict_thread, daemon=True).start()

    def _predict_thread(self):
        try:
            results = _train_module.predict_from_file(self.filepath)
        except Exception as exc:
            results = [("Error", str(exc), "")]
        self.after(0, lambda: self._show_results(results))

    def _show_results(self, results):
        self.run_btn.config(state="normal", text="▶  Run Predictions")

        for w in self.results_body.winfo_children():
            w.destroy()

        if not results:
            tk.Label(self.results_body, text="No predictions returned.",
                     font=("Helvetica", 10), bg=WHITE, fg=GRAY).pack(anchor="w")
            return

        # ── Summary badges ──
        total = len(results)
        pos   = sum(1 for _, pred, _ in results if "detected" in pred.lower()
                    or "yes" in pred.lower() or "positive" in pred.lower()
                    or (pred.strip().lstrip("-").replace(".", "", 1).isdigit()
                        and float(pred.strip()) > 0.5))
        neg   = total - pos

        badge_row = tk.Frame(self.results_body, bg=WHITE)
        badge_row.pack(anchor="w", pady=(0, 12))
        for lbl, val, color in [
            ("Total Samples",        str(total), GRAY),
            ("Positive / Detected",  str(pos),   "#B91C1C"),
            ("Negative / Clear",     str(neg),   GREEN_DARK),
        ]:
            b = tk.Frame(badge_row, bg=GRAY_LITE,
                         highlightthickness=1, highlightbackground=BORDER,
                         padx=12, pady=6)
            b.pack(side="left", padx=(0, 8))
            tk.Label(b, text=lbl,  font=("Helvetica", 8),
                     bg=GRAY_LITE, fg=GRAY).pack(anchor="w")
            tk.Label(b, text=val, font=("Helvetica", 12, "bold"),
                     bg=GRAY_LITE, fg=color).pack(anchor="w")

        tk.Frame(self.results_body, height=1, bg=BORDER).pack(fill="x", pady=(0, 8))

        # ── Column headers ──
        hdr = tk.Frame(self.results_body, bg=GRAY_LITE)
        hdr.pack(fill="x", pady=(0, 2))
        for txt, w in [("#", 4), ("Sample / Row", 24), ("Prediction", 22), ("Confidence", 12)]:
            tk.Label(hdr, text=txt, font=("Helvetica", 9, "bold"),
                     bg=GRAY_LITE, fg=TEXT, width=w, anchor="w",
                     padx=6, pady=4).pack(side="left")

        # ── Table ──
        table_frame = tk.Frame(self.results_body, bg=WHITE,
                               highlightthickness=1, highlightbackground=BORDER)
        table_frame.pack(fill="x")

        max_rows = min(len(results), 200)
        for idx, (sample_lbl, pred, conf) in enumerate(results[:max_rows]):
            row_bg = WHITE if idx % 2 == 0 else GRAY_LITE
            row = tk.Frame(table_frame, bg=row_bg)
            row.pack(fill="x")

            is_pos = ("detected" in pred.lower() or "yes" in pred.lower()
                      or "positive" in pred.lower()
                      or (pred.strip().lstrip("-").replace(".", "", 1).isdigit()
                          and float(pred.strip()) > 0.5))
            pred_color = "#B91C1C" if is_pos else GREEN_DARK

            for txt, w, color in [
                (str(idx + 1),    4,  GRAY),
                (str(sample_lbl), 24, TEXT),
                (pred,            22, pred_color),
                (conf,            12, GRAY),
            ]:
                tk.Label(row, text=txt, font=("Helvetica", 9),
                         bg=row_bg, fg=color, width=w, anchor="w",
                         padx=6, pady=3).pack(side="left")

        if len(results) > 200:
            tk.Label(self.results_body,
                     text=f"Showing first 200 of {len(results)} rows.",
                     font=("Helvetica", 9), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(6, 0))

        # ── Export button ──
        styled_button(self.results_body, "⬇  Export Results as CSV",
                      lambda: self._export(results), secondary=True).pack(anchor="w", pady=(12, 0))

        # FIX: draw chart BEFORE rebinding scroll so chart widgets also get bound
        self._draw_accuracy_chart(results)

        # FIX: rebind scroll after all widgets are created
        self.after(50, lambda: self._bind_scroll(self.results_body))

    def _draw_accuracy_chart(self, results):
        import re

        chart_frame = tk.Frame(self.results_body, bg=WHITE,
                               highlightthickness=1, highlightbackground=BORDER,
                               padx=20, pady=16)
        chart_frame.pack(fill="x", pady=(16, 0))

        tk.Label(chart_frame, text="Prediction Analysis",
                 font=("Helvetica", 12, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(chart_frame,
                 text="Accuracy and confidence distribution across all predictions.",
                 font=("Helvetica", 9), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(2, 12))

        # ── Accuracy from GT labels ──
        correct = 0
        incorrect = 0
        has_gt = False

        for sample_lbl, pred, conf in results:
            match = re.search(r"GT:\s*(\S+)", sample_lbl)
            if match:
                has_gt = True
                gt     = match.group(1).strip().lower()
                pred_l = pred.strip().lower()

                pred_positive = any(k in pred_l for k in ("detected", "yes", "positive", "1"))
                pred_negative = any(k in pred_l for k in ("no disease", "not detected", "no", "negative", "0", "clear"))

                gt_positive = gt in ("1", "yes", "positive", "detected")
                gt_negative = gt in ("0", "no", "negative", "clear", "no disease")

                if pred_positive and gt_positive:
                    correct += 1
                elif pred_negative and gt_negative:
                    correct += 1
                else:
                    incorrect += 1

        total = len(results)

        badge_row = tk.Frame(chart_frame, bg=WHITE)
        badge_row.pack(anchor="w", pady=(0, 14))

        if has_gt and (correct + incorrect) > 0:
            acc_pct = correct / (correct + incorrect) * 100
            for lbl, val, color in [
                ("Accuracy",  f"{acc_pct:.1f}%", GREEN_DARK),
                ("Correct",   str(correct),       GREEN_DARK),
                ("Incorrect", str(incorrect),     "#B91C1C"),
                ("Total",     str(total),         GRAY),
            ]:
                b = tk.Frame(badge_row, bg=GRAY_LITE,
                             highlightthickness=1, highlightbackground=BORDER,
                             padx=12, pady=6)
                b.pack(side="left", padx=(0, 8))
                tk.Label(b, text=lbl, font=("Helvetica", 8),
                         bg=GRAY_LITE, fg=GRAY).pack(anchor="w")
                tk.Label(b, text=val, font=("Helvetica", 12, "bold"),
                         bg=GRAY_LITE, fg=color).pack(anchor="w")
        else:
            tk.Label(badge_row,
                     text="Ground-truth labels not detected — showing confidence distribution only.",
                     font=("Helvetica", 9), bg=WHITE, fg=GRAY).pack(anchor="w")

        # ── Confidence distribution ──
        conf_bins    = [0] * 10
        parsed_confs = []
        for _, _, conf_str in results:
            try:
                val = float(conf_str.replace("%", "").strip())
                parsed_confs.append(val)
                bucket = min(int(val // 10), 9)
                conf_bins[bucket] += 1
            except (ValueError, AttributeError):
                pass

        if not parsed_confs:
            tk.Label(chart_frame, text="No confidence data available.",
                     font=("Helvetica", 9), bg=WHITE, fg=GRAY).pack(anchor="w")
            return

        avg_conf = sum(parsed_confs) / len(parsed_confs)

        b = tk.Frame(badge_row, bg=GRAY_LITE,
                     highlightthickness=1, highlightbackground=BORDER,
                     padx=12, pady=6)
        b.pack(side="left", padx=(0, 8))
        tk.Label(b, text="Avg Confidence", font=("Helvetica", 8),
                 bg=GRAY_LITE, fg=GRAY).pack(anchor="w")
        tk.Label(b, text=f"{avg_conf:.1f}%", font=("Helvetica", 12, "bold"),
                 bg=GRAY_LITE, fg="#185FA5").pack(anchor="w")

        # ── Confidence bar chart ──
        W, H = 680, 180
        PAD_L, PAD_R, PAD_T, PAD_B = 44, 16, 12, 36

        tk.Label(chart_frame, text="Confidence distribution",
                 font=("Helvetica", 9, "bold"), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(8, 4))

        cv = tk.Canvas(chart_frame, width=W, height=H,
                       bg=WHITE, highlightthickness=0)
        cv.pack(anchor="w")

        plot_w = W - PAD_L - PAD_R
        plot_h = H - PAD_T - PAD_B
        max_bin = max(conf_bins) if max(conf_bins) > 0 else 1
        bar_w   = plot_w / 10

        bin_labels = ["0-10", "10-20", "20-30", "30-40", "40-50",
                      "50-60", "60-70", "70-80", "80-90", "90-100"]

        for i, count in enumerate(conf_bins):
            x0 = PAD_L + i * bar_w + 3
            x1 = PAD_L + (i + 1) * bar_w - 3
            bar_h = (count / max_bin) * plot_h
            y0 = PAD_T + plot_h - bar_h
            y1 = PAD_T + plot_h

            color = "#185FA5" if i >= 5 else "#D85A30"
            cv.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

            if count > 0:
                cv.create_text((x0 + x1) / 2, y0 - 4,
                               text=str(count), font=("Helvetica", 8), fill=TEXT)

            if i % 2 == 0:
                cv.create_text(PAD_L + (i + 0.5) * bar_w, H - PAD_B + 12,
                               text=bin_labels[i] + "%",
                               font=("Helvetica", 7), fill=GRAY)

        for frac in [0.25, 0.5, 0.75, 1.0]:
            y = PAD_T + plot_h * (1 - frac)
            cv.create_line(PAD_L, y, W - PAD_R, y, fill="#E5E7EB", dash=(3, 3))
            cv.create_text(PAD_L - 4, y,
                           text=str(int(max_bin * frac)),
                           font=("Helvetica", 7), fill=GRAY, anchor="e")

        cv.create_rectangle(PAD_L, PAD_T, W - PAD_R, PAD_T + plot_h,
                            outline="#D1D5DB", width=1)

        legend_x = PAD_L
        for lbl, color in [("High confidence (≥50%)", "#185FA5"),
                            ("Low confidence (<50%)",  "#D85A30")]:
            cv.create_rectangle(legend_x, H - 8,
                                legend_x + 10, H,
                                fill=color, outline="")
            cv.create_text(legend_x + 14, H - 4,
                           text=lbl, font=("Helvetica", 7),
                           fill=GRAY, anchor="w")
            legend_x += 160

        # ── Accuracy bar (GT only) ──
        if has_gt and (correct + incorrect) > 0:
            tk.Label(chart_frame, text="Correct vs incorrect predictions",
                     font=("Helvetica", 9, "bold"), bg=WHITE, fg=GRAY).pack(anchor="w", pady=(14, 4))

            bar_canvas = tk.Canvas(chart_frame, width=680, height=36,
                                   bg=WHITE, highlightthickness=0)
            bar_canvas.pack(anchor="w")

            total_gt     = correct + incorrect
            correct_w    = int(640 * correct / total_gt)
            incorrect_w  = 640 - correct_w

            bar_canvas.create_rectangle(20, 8, 20 + correct_w, 28,
                                        fill=GREEN_DARK, outline="")
            bar_canvas.create_rectangle(20 + correct_w, 8,
                                        20 + correct_w + incorrect_w, 28,
                                        fill="#B91C1C", outline="")
            bar_canvas.create_text(20 + correct_w // 2, 18,
                                   text=f"Correct {correct} ({acc_pct:.0f}%)",
                                   font=("Helvetica", 8, "bold"), fill=WHITE)
            if incorrect_w > 60:
                bar_canvas.create_text(20 + correct_w + incorrect_w // 2, 18,
                                       text=f"Wrong {incorrect}",
                                       font=("Helvetica", 8, "bold"), fill=WHITE)

    def _export(self, results):
        import csv
        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"{self.model}_test_results.csv",
            title="Save Test Results"
        )
        if not save_path:
            return
        try:
            with open(save_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["#", "Sample", "Prediction", "Confidence"])
                for i, (lbl, pred, conf) in enumerate(results, 1):
                    writer.writerow([i, lbl, pred, conf])
            messagebox.showinfo("Saved", f"Results saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save:\n{e}")


# ─────────────────────────────────────────
#  SERVER UPLOAD SCREEN
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

        is_error = (
            isinstance(server_response, dict) and "error" in server_response
        ) or (
            isinstance(server_response, str) and (
                server_response.startswith("❌") or "failed" in server_response.lower()
            )
        ) or server_response is None

        icon_color  = "#FEE2E2" if is_error else GREEN_LITE
        icon_border = "#F87171" if is_error else GREEN_MID
        icon_text   = "✗" if is_error else "✔"
        icon_fg     = "#B91C1C" if is_error else GREEN_DARK
        title_text  = "Upload Failed" if is_error else "Upload Successful!"
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
            detail  = err_msg
        else:
            detail = (f"Model weights for {model.title()} ({epochs} epochs)\n"
                      f"have been successfully uploaded to the server.")
        tk.Label(center, text=detail,
                 font=("Helvetica", 11), bg=BG, fg=GRAY, justify="center").pack(pady=(0, 12))

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
