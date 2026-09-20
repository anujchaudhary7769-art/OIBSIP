# Python BMI Calculator

Two tiers:

- **Beginner** (`beginner_bmi.py`): command-line BMI calculator with input
  validation.
- **Advanced** (`advanced_bmi_gui.py`): a tkinter GUI with colour-coded
  results, multi-user SQLite history, and a matplotlib BMI trend graph.

## Project layout

```
bmi_calculator/
├── beginner_bmi.py        # CLI tool
├── advanced_bmi_gui.py     # GUI app (tkinter + matplotlib + sqlite3)
├── db.py                   # SQLite persistence layer used by the GUI
├── requirements.txt
└── README.md
```

Running the advanced app creates `bmi_records.db` (SQLite) in this same
folder the first time you save a record.

## Setup

1. **Beginner tier** needs nothing beyond a standard Python install:

   ```bash
   python beginner_bmi.py
   ```

2. **Advanced tier**:

   ```bash
   pip install -r requirements.txt
   python advanced_bmi_gui.py
   ```

   - `tkinter` and `sqlite3` are part of the Python standard library, so
     they usually don't need `pip install` on Windows or macOS.
   - On **Linux**, `tkinter` is sometimes packaged separately by your
     distro. If you get `ModuleNotFoundError: No module named 'tkinter'`,
     install it with e.g. `sudo apt-get install python3-tk` (Debian/Ubuntu)
     and re-run the app.

## Using the beginner CLI tool

```
=== BMI Calculator ===
Enter your weight in kg: 70
Enter your height in m (e.g. 1.75): 1.75

Your BMI is: 22.86
Category:    Normal
```

Non-numeric or non-positive input (e.g. `abc`, `-5`, `0`) is rejected with a
message, and the tool asks again instead of crashing.

## Using the advanced GUI app

1. Type a **Username** (or pick an existing one from the dropdown - it
   fills in automatically once you've saved at least one record).
2. Enter **Weight (kg)** and **Height (m)**.
3. Click **Calculate** — the BMI value and category appear colour-coded:
   - Blue = Underweight
   - Green = Normal
   - Orange = Overweight
   - Red = Obese
4. Click **Save Record** to store this result under that username in
   `bmi_records.db`.
5. Click **View Trend Graph** to open a window with a matplotlib line
   chart of that user's BMI over their saved history (with the healthy
   18.5–25 range lightly shaded for reference).

Invalid input (non-numeric, blank, zero/negative) shows an error pop-up
instead of crashing. Any database problem (e.g. the `.db` file is locked
or unreadable) shows an error pop-up too, and the app keeps running.

## BMI categories used

| BMI            | Category    |
|----------------|-------------|
| < 18.5         | Underweight |
| 18.5 – 24.9    | Normal      |
| 25 – 29.9      | Overweight  |
| ≥ 30           | Obese       |

## Extending further

- Swap `db.py`'s SQLite calls for a CSV-based store if you'd rather avoid
  a database file — `save_record`/`get_usernames`/`get_history` are the
  only three functions the GUI depends on, so that's the only file to
  change.
- Add a "Delete record" or "Export to CSV" button using the same
  try/except-around-db pattern already used for save/load.
- Add weight-trend or height-trend charts alongside the BMI trend chart by
  extending `get_history()` to also return weight/height per record.
