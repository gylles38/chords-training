from rich.console import Console

console = Console()

# --- Fonctions utilitaires ---
def clear_screen():
    """Efface l'écran du terminal."""
    console.clear()

def int_to_roman(num):
    """Convert an integer to a Roman numeral (1-7 for degrees)."""
    if not 0 < num <= 7:
        return str(num)
    roman_values = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")
    ]
    result = ""
    for value, symbol in roman_values:
        while num >= value:
            result += symbol
            num -= value
    return result.lower() if num <= 3 else result  # Lowercase for i, ii, iii; uppercase for IV, V, etc.

