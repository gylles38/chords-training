from music_theory import recognize_chord
from data.chords import all_chords

def test_recognition():
    test_cases = [
        "Fa dièse 7ème",
        "Do dièse Majeur 7ème",
        "La bémol Mineur 7ème",
        "Si bémol 7ème"
    ]

    for name in test_cases:
        notes = all_chords.get(name)
        if notes is None:
            print(f"FAILED: {name} not found in all_chords")
            continue

        recognized_name, inversion = recognize_chord(notes)
        if recognized_name == name:
            print(f"PASSED: {name} recognized correctly")
        else:
            print(f"FAILED: {name} recognized as {recognized_name} ({inversion})")

if __name__ == "__main__":
    test_recognition()
