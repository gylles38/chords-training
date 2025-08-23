# modes/modulation_mode.py
import random
from rich.text import Text
from .chord_mode_base import ChordModeBase
from data.modulations import modulations
from data.chords import all_scales, DEGREE_MAP

# Map degree names to their index in the all_scales list
# Note: This is simplified. 'V/V' will be handled specially.
# We add roman numerals for secondary dominants and other cases.
DEGREE_INDEX_MAP = {
    'I': 0, 'i': 0,
    'II': 1, 'ii': 1,
    'III': 2, 'iii': 2,
    'IV': 3, 'iv': 3,
    'V': 4, 'v': 4,
    'VI': 5, 'vi': 5,
    'VII': 6, 'vii': 6, 'vii°': 6
}

class ModulationMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.progression_selection_mode = progression_selection_mode
        self.play_progression_before_start = play_progression_before_start
        self.use_voice_leading = True
        self.modulations = modulations
        self.all_keys = list(all_scales.keys())

    def _get_key_from_degree(self, original_key, degree):
        """Finds the key name for a given degree relative to an original key."""
        if original_key not in all_scales:
            return None

        degree_index = DEGREE_INDEX_MAP.get(degree)
        if degree_index is None:
            return None

        # The chord name at that degree (e.g., 'Sol Majeur' or 'La Mineur')
        target_chord_name = all_scales[original_key][degree_index]

        # This chord name IS the key name we're looking for, if it exists in all_scales
        if target_chord_name in all_scales:
            return target_chord_name

        return None # Fallback if the chord name isn't a valid key

    def _get_chord_from_degree(self, degree_str, start_key, target_key):
        """
        Parses a degree string and returns the corresponding chord name.
        Handles complex cases like 'V7/V' or 'IV_new_I'.
        """
        # Case 1: Chord from the new key (e.g., 'V_new_I')
        if '_new_' in degree_str:
            _, degree = degree_str.split('_new_')
            degree_index = DEGREE_INDEX_MAP.get(degree, 0)
            return all_scales[target_key][degree_index]

        # Case 2: Secondary Dominant (e.g., 'V7/V', 'V7/vi')
        if '/' in degree_str:
            dominant_degree, target_degree = degree_str.split('/')

            # Find the key of the target degree (e.g., for 'V/V' in C, find the key of G)
            temp_target_key = self._get_key_from_degree(start_key, target_degree)
            if not temp_target_key:
                 return None

            # Now find the dominant of that temporary target key
            # Note: The V of a minor key can be minor (v) or major (V).
            # We'll prefer the major V for a stronger pull (dominant function).
            dominant_chord = all_scales[temp_target_key][DEGREE_INDEX_MAP['V']]

            # Make it a 7th chord if specified (e.g., 'V7')
            if '7' in dominant_degree:
                # Ensure we are modifying a Major chord to a 7th, not a minor or diminished.
                if "Majeur" in dominant_chord:
                    return dominant_chord.replace(" Majeur", " 7ème")
                else: # Fallback for minor keys where V might be minor
                    return f"{dominant_chord.replace(' Mineur', '')} 7ème"

            return dominant_chord

        # Case 3: Simple degree from the start key (e.g., 'I', 'IV', 'vi')
        degree_index = DEGREE_INDEX_MAP.get(degree_str)
        if degree_index is not None:
             # Special case for I7
            if degree_str == "I7":
                return all_scales[start_key][0].replace(" Majeur", " 7ème")
            return all_scales[start_key][degree_index]

        return None

    def _generate_progression_and_info(self):
        """Selects a modulation and generates the chord progression and descriptive info."""

        start_key = random.choice(self.all_keys)
        modulation_info = random.choice(self.modulations)

        progression_degrees = modulation_info["progression_degrees"]

        # Determine the target key based on the modulation type
        if "Dominante" in modulation_info["name"]:
            target_key = self._get_key_from_degree(start_key, 'V')
        elif "Sous-dominante" in modulation_info["name"]:
            target_key = self._get_key_from_degree(start_key, 'IV')
        elif "Relatif Mineur" in modulation_info["name"]:
            target_key = self._get_key_from_degree(start_key, 'vi')
        elif "Homonyme" in modulation_info["name"]:
            target_key = start_key.replace(" Majeur", " Mineur")
        else: # For cases like Anatole where there isn't one single target key
            target_key = start_key

        if not target_key: # Could fail if _get_key_from_degree fails
             return None, None, None

        progression_chords = []
        for degree in progression_degrees:
            chord = self._get_chord_from_degree(degree, start_key, target_key)
            if chord:
                progression_chords.append(chord)
            else:
                # If a degree can't be resolved to a chord, this progression is invalid
                return None, None, None

        # After generating the progression, check if all its chords are in the allowed set
        if not all(chord in self.chord_set for chord in progression_chords):
            return None, None, None # Signal to retry

        # Get pivot chord for the explanation
        pivot_chord_degree = next((d for d in progression_degrees if '/' in d or '7' in d), None)
        pivot_chord_name = self._get_chord_from_degree(pivot_chord_degree, start_key, target_key) if pivot_chord_degree else ""

        explanation = modulation_info["explanation_template"].format(
            start_key=start_key,
            target_key=target_key,
            pivot_chord_name=pivot_chord_name
        )

        return progression_chords, explanation, modulation_info['name']


    def run(self):
        current_progression = None
        explanation = ""
        header_name = ""

        while not self.exit_flag:
            if current_progression is None:
                attempts = 0
                prog, expl, name = None, None, None
                while prog is None and attempts < 50:  # Safety break after 50 attempts
                    prog, expl, name = self._generate_progression_and_info()
                    attempts += 1

                if prog is None:
                    self.console.print("\n[bold red]Impossible de générer une modulation avec les réglages d'accords actuels.[/bold red]")
                    self.console.print("[bold yellow]Essayez de sélectionner 'Tous les accords' dans les options (menu principal -> 17).[/bold yellow]")
                    import time
                    time.sleep(5)
                    return # Exit the mode gracefully

                current_progression = prog
                explanation = expl
                header_name = name

            def pre_display():
                self.console.print(Text(f"Exercice : {header_name}", style="bold cyan", justify="center"))
                self.console.print(explanation)
                self.console.print("\nAppuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer à la suivante.\n")

            result = self.run_progression(
                progression_accords=current_progression,
                header_title="Modulations",
                header_name="[16] Les modulations",
                border_style="green",
                pre_display=pre_display
            )

            if result == 'exit':
                break
            elif result == 'repeat':
                pass
            elif result == 'continue' or result == 'skipped':
                current_progression = None

        self.show_overall_stats_and_wait()


def modulation_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    mode = ModulationMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set)
    mode.run()
