"""
advanced_bmi_gui.py
---------------------
Advanced-tier BMI calculator: a tkinter GUI (no command line) with:

  [x] GUI window with input fields + a "Calculate" button
  [x] Colour-coded result (green=normal, blue=underweight, orange=overweight,
      red=obese)
  [x] Multi-user support (username field + a dropdown of known users)
  [x] Historical records stored in an SQLite database (db.py)
  [x] Graph view: matplotlib line chart of a user's BMI trend over time
  [x] Error handling for database read/write failures (messagebox popups,
      the app never crashes on a DB problem)

Run with:
    python advanced_bmi_gui.py
"""

import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import db

CATEGORY_COLORS = {
    "Underweight": "#1565c0",  # blue
    "Normal": "#2e7d32",       # green
    "Overweight": "#ef6c00",   # orange
    "Obese": "#c62828",        # red
}


def calculate_bmi(weight_kg: float, height_m: float) -> float:
    return weight_kg / (height_m ** 2)


def classify_bmi(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


class BMIApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BMI Calculator")
        self.resizable(False, False)
        self.configure(padx=20, pady=20)

        self._last_result = None  # (username, weight, height, bmi, category)

        self._build_widgets()
        self._safe_refresh_users()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_widgets(self):
        pad = {"padx": 6, "pady": 6}

        ttk.Label(self, text="Username:").grid(row=0, column=0, sticky="e", **pad)
        self.username_var = tk.StringVar()
        self.username_combo = ttk.Combobox(self, textvariable=self.username_var, width=22)
        self.username_combo.grid(row=0, column=1, columnspan=2, sticky="w", **pad)

        ttk.Label(self, text="Weight (kg):").grid(row=1, column=0, sticky="e", **pad)
        self.weight_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.weight_var, width=24).grid(
            row=1, column=1, columnspan=2, sticky="w", **pad
        )

        ttk.Label(self, text="Height (m):").grid(row=2, column=0, sticky="e", **pad)
        self.height_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.height_var, width=24).grid(
            row=2, column=1, columnspan=2, sticky="w", **pad
        )

        ttk.Button(self, text="Calculate", command=self.on_calculate).grid(
            row=3, column=0, sticky="ew", **pad
        )
        ttk.Button(self, text="Save Record", command=self.on_save).grid(
            row=3, column=1, sticky="ew", **pad
        )
        ttk.Button(self, text="View Trend Graph", command=self.on_view_graph).grid(
            row=3, column=2, sticky="ew", **pad
        )

        self.result_var = tk.StringVar(value="Enter your details and click Calculate.")
        self.result_label = tk.Label(
            self,
            textvariable=self.result_var,
            font=("Segoe UI", 14, "bold"),
            fg="#333333",
            pady=12,
        )
        self.result_label.grid(row=4, column=0, columnspan=3, sticky="ew")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _parse_positive_float(self, raw: str, field_name: str):
        raw = raw.strip()
        try:
            value = float(raw)
        except ValueError:
            messagebox.showerror(
                "Invalid input", f"{field_name} must be a number (got '{raw}')."
            )
            return None
        if value <= 0:
            messagebox.showerror(
                "Invalid input", f"{field_name} must be greater than zero."
            )
            return None
        return value

    def on_calculate(self):
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("Invalid input", "Please enter a username.")
            return

        weight = self._parse_positive_float(self.weight_var.get(), "Weight")
        if weight is None:
            return
        height = self._parse_positive_float(self.height_var.get(), "Height")
        if height is None:
            return

        bmi = calculate_bmi(weight, height)
        category = classify_bmi(bmi)
        color = CATEGORY_COLORS[category]

        self.result_var.set(f"BMI: {bmi:.2f}  -  {category}")
        self.result_label.configure(fg=color)

        self._last_result = (username, weight, height, bmi, category)

    def on_save(self):
        if self._last_result is None:
            messagebox.showwarning(
                "Nothing to save", "Click Calculate first, then Save Record."
            )
            return

        username, weight, height, bmi, category = self._last_result
        try:
            db.save_record(username, weight, height, bmi, category)
        except db.DBError as exc:
            messagebox.showerror("Database error", str(exc))
            return

        messagebox.showinfo("Saved", f"Record saved for {username}.")
        self._safe_refresh_users()

    def on_view_graph(self):
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("Invalid input", "Enter or pick a username first.")
            return

        try:
            history = db.get_history(username)
        except db.DBError as exc:
            messagebox.showerror("Database error", str(exc))
            return

        if not history:
            messagebox.showinfo(
                "No data", f"No saved records for '{username}' yet. Save one first."
            )
            return

        self._show_graph_window(username, history)

    def _show_graph_window(self, username, history):
        timestamps = [row[0] for row in history]
        bmis = [row[1] for row in history]

        window = tk.Toplevel(self)
        window.title(f"BMI Trend - {username}")

        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(range(len(bmis)), bmis, marker="o", color="#1565c0")
        ax.set_title(f"BMI trend for {username}")
        ax.set_xlabel("Record #")
        ax.set_ylabel("BMI")
        ax.set_xticks(range(len(timestamps)))
        ax.set_xticklabels([t.split("T")[0] for t in timestamps], rotation=45, ha="right")
        ax.axhspan(18.5, 25, color="green", alpha=0.08)  # normal range shading
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _safe_refresh_users(self):
        """Populate the username dropdown; on DB failure, warn but keep the
        app usable (a fresh/missing DB simply means an empty list)."""
        try:
            db.init_db()
            users = db.get_usernames()
            self.username_combo["values"] = users
        except db.DBError as exc:
            messagebox.showerror("Database error", str(exc))


def main():
    app = BMIApp()
    app.mainloop()


if __name__ == "__main__":
    main()
