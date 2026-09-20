"""
beginner_bmi.py
----------------
Command-line BMI calculator.

Checklist covered:
  [x] Prompt user for weight (kg) and height (m) via command line
  [x] Calculate BMI using BMI = weight / (height^2)
  [x] Classify into Underweight / Normal / Overweight / Obese
  [x] Display BMI rounded to 2 decimal places, plus the category
  [x] Input validation: reject non-numeric input and negative/zero values,
      with a helpful error message, and let the user retry

Run with:
    python beginner_bmi.py
"""


def get_positive_float(prompt: str) -> float:
    """
    Keep asking `prompt` until the user enters a valid, positive number.
    Rejects non-numeric text and zero/negative values with a clear message,
    instead of crashing.
    """
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
        except ValueError:
            print(f"  '{raw}' isn't a valid number. Please enter digits only, e.g. 65.5")
            continue

        if value <= 0:
            print("  Please enter a positive number greater than zero.")
            continue

        return value


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


def main() -> None:
    print("=== BMI Calculator ===")
    weight = get_positive_float("Enter your weight in kg: ")
    height = get_positive_float("Enter your height in m (e.g. 1.75): ")

    bmi = calculate_bmi(weight, height)
    category = classify_bmi(bmi)

    print()
    print(f"Your BMI is: {bmi:.2f}")
    print(f"Category:    {category}")


if __name__ == "__main__":
    main()
