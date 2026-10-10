"""
Task 3 - Random Password Generator (Advanced Tier, GUI)
Uses: secrets (via pwgen_core), tkinter, pyperclip

Install:  pip install pyperclip
Run:      python password_generator_gui.py
"""

import tkinter as tk
from collections import deque
from tkinter import messagebox, ttk

try:
    import pyperclip
except ImportError:          # fall back to tkinter's own clipboard if pyperclip is missing
    pyperclip = None

import pwgen_core as core

STRENGTH_COLORS = {"Weak": "#d9534f", "Medium": "#f0ad4e", "Strong": "#5cb85c"}


class PasswordApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Secure Password Generator")
        self.resizable(False, False)

        self.length = tk.IntVar(value=16)
        self.opts = {name: tk.BooleanVar(value=True) for name in core.CHAR_SETS}
        self.exclude_ambiguous = tk.BooleanVar(value=False)
        self.password = tk.StringVar()
        self.status = tk.StringVar()
        self.history = deque(maxlen=5)          # in memory only - never written to disk

        self._build_ui()
        self.generate()

    # ---------- UI ----------
    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}
        frame = ttk.Frame(self, padding=8)
        frame.grid()

        # Password display + copy
        ttk.Entry(frame, textvariable=self.password, state="readonly", width=36,
                  font=("Consolas", 14), justify="center").grid(row=0, column=0, columnspan=2, **pad)

        # Strength indicator
        self.bar = tk.Canvas(frame, width=300, height=14, bg="#e0e0e0", highlightthickness=0)
        self.bar.grid(row=1, column=0, columnspan=2, **pad)
        self.bar_fill = self.bar.create_rectangle(0, 0, 0, 14, width=0)
        self.strength_label = ttk.Label(frame, text="", font=("Segoe UI", 10, "bold"))
        self.strength_label.grid(row=2, column=0, columnspan=2)

        # Length: slider + spinbox kept in sync through one IntVar
        ttk.Label(frame, text="Length:").grid(row=3, column=0, sticky="w", **pad)
        ttk.Spinbox(frame, from_=core.MIN_LENGTH, to=core.MAX_LENGTH, width=5,
                    textvariable=self.length, command=self.generate).grid(row=3, column=1, sticky="e", **pad)
        ttk.Scale(frame, from_=core.MIN_LENGTH, to=core.MAX_LENGTH, orient="horizontal", length=300,
                  command=lambda v: (self.length.set(round(float(v))), self.generate())
                  ).grid(row=4, column=0, columnspan=2, **pad)

        # Character-type checkboxes
        labels = {"upper": "Uppercase (A-Z)", "lower": "Lowercase (a-z)",
                  "digits": "Numbers (0-9)", "symbols": "Symbols (!@#$...)"}
        box = ttk.LabelFrame(frame, text="Include")
        box.grid(row=5, column=0, columnspan=2, sticky="ew", **pad)
        for i, (name, text) in enumerate(labels.items()):
            ttk.Checkbutton(box, text=text, variable=self.opts[name],
                            command=self.generate).grid(row=i // 2, column=i % 2, sticky="w", padx=8, pady=2)

        ttk.Checkbutton(frame, text="Exclude ambiguous characters (0 O o 1 l I |)",
                        variable=self.exclude_ambiguous, command=self.generate
                        ).grid(row=6, column=0, columnspan=2, sticky="w", **pad)

        # Buttons
        btns = ttk.Frame(frame)
        btns.grid(row=7, column=0, columnspan=2, **pad)
        ttk.Button(btns, text="Generate", command=self.generate).pack(side="left", padx=4)
        ttk.Button(btns, text="Copy to Clipboard", command=self.copy).pack(side="left", padx=4)

        ttk.Label(frame, textvariable=self.status, foreground="#2e7d32").grid(row=8, column=0, columnspan=2)

        # History (last 5)
        hist = ttk.LabelFrame(frame, text="Recent passwords (this session only)")
        hist.grid(row=9, column=0, columnspan=2, sticky="ew", **pad)
        self.hist_list = tk.Listbox(hist, height=5, width=44, font=("Consolas", 10))
        self.hist_list.pack(padx=6, pady=6)

    # ---------- Actions ----------
    def selected_types(self):
        return [name for name, var in self.opts.items() if var.get()]

    def generate(self):
        selected = self.selected_types()
        try:
            length = int(self.length.get())
            pw = core.generate_password(length, selected, self.exclude_ambiguous.get())
        except (ValueError, tk.TclError) as exc:
            self.status.set("")
            if len(selected) < 2:
                messagebox.showwarning("Check settings", "Please select at least 2 character types.")
            else:
                messagebox.showwarning("Check settings", str(exc))
            return

        self.password.set(pw)
        self.history.appendleft(pw)
        self.hist_list.delete(0, tk.END)
        for item in self.history:
            self.hist_list.insert(tk.END, item)
        self._update_strength(length, selected)
        self.copy(auto=True)

    def _update_strength(self, length, selected):
        label, frac = core.strength(length, selected, self.exclude_ambiguous.get())
        color = STRENGTH_COLORS[label]
        self.bar.coords(self.bar_fill, 0, 0, 300 * frac, 14)
        self.bar.itemconfigure(self.bar_fill, fill=color)
        self.strength_label.config(text=f"Strength: {label}", foreground=color)

    def copy(self, auto=False):
        pw = self.password.get()
        if not pw:
            return
        try:
            if pyperclip:
                pyperclip.copy(pw)
            else:
                self.clipboard_clear()
                self.clipboard_append(pw)
            self.status.set("Copied to clipboard" if not auto else "Generated and copied to clipboard")
        except Exception:
            self.status.set("Could not access clipboard")


if __name__ == "__main__":
    PasswordApp().mainloop()
