"""
Task 3 - Random Password Generator (Beginner Tier, command line)
Uses: random, string

Note: the `random` module is fine for learning, but it is NOT cryptographically
secure. The advanced version in this project uses `secrets` instead.
"""

import random
import string

MIN_LENGTH = 8
MAX_LENGTH = 128

CHAR_TYPES = {
    "uppercase letters": string.ascii_uppercase,
    "lowercase letters": string.ascii_lowercase,
    "numbers": string.digits,
    "symbols": string.punctuation,
}


def ask_length():
    """Keep asking until the user enters a valid length."""
    while True:
        raw = input(f"Password length (min {MIN_LENGTH}, max {MAX_LENGTH}): ").strip()
        if not raw.isdigit():
            print("  Invalid input: please enter a whole number.")
            continue
        length = int(raw)
        if length < MIN_LENGTH:
            print(f"  Too short: minimum length is {MIN_LENGTH}.")
        elif length > MAX_LENGTH:
            print(f"  Too long: maximum length is {MAX_LENGTH}.")
        else:
            return length


def ask_yes_no(question):
    """Ask a y/n question; keep asking until the answer is y or n."""
    while True:
        answer = input(f"{question} (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please type y or n.")


def ask_char_types():
    """Keep asking until at least 2 character types are chosen."""
    while True:
        chosen = [name for name in CHAR_TYPES if ask_yes_no(f"Include {name}?")]
        if len(chosen) >= 2:
            return chosen
        print("  Please select at least 2 character types. Let's try again.\n")


def generate_password(length, chosen_types):
    """Build a password that contains at least one char of every chosen type."""
    # 1) guarantee one character from each selected type
    password_chars = [random.choice(CHAR_TYPES[name]) for name in chosen_types]

    # 2) fill the remaining length from the combined pool
    pool = "".join(CHAR_TYPES[name] for name in chosen_types)
    password_chars += [random.choice(pool) for _ in range(length - len(password_chars))]

    # 3) shuffle so the guaranteed characters aren't always at the start
    random.shuffle(password_chars)
    return "".join(password_chars)


def main():
    print("=== Random Password Generator ===\n")
    while True:
        length = ask_length()
        chosen = ask_char_types()
        print("\nYour password:", generate_password(length, chosen), "\n")
        if not ask_yes_no("Generate another password?"):
            print("Goodbye!")
            break
        print()


if __name__ == "__main__":
    main()
