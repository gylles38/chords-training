# modes/chord_transitions_mode.py
import random
import time
from typing import List, Tuple

from .progression_mode_base import ProgressionModeBase
from data.chords import three_note_chords, gammes_majeures
from stats_manager import get_chord_errors
from keyboard_handler import wait_for_input, enable_raw_mode, disable_raw_mode

def weighted_sample_without_replacement(population, weights, k=1):
    """
    Performs weighted sampling without replacement.
    """
    population = list(population)
    weights = list(weights)
    if len(population) < k:
        return random.sample(population, k)
    result = []
    for _ in range(k):
        if not population:
            break
        chosen_element = random.choices(population, weights=weights, k=1)[0]
        chosen_index = population.index(chosen_element)
        population.pop(chosen_index)
        weights.pop(chosen_index)
        result.append(chosen_element)
    return result

class ChordTransitionsMode(ProgressionModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions, use_voice_leading_display=False):
        super().__init__(inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions, use_voice_leading_display)
        self.progression_length = (2, 4)
        # This mode inherently uses voice leading for validation
        self.use_voice_leading = True

    def _setup_progressions(self):
        """ No setup needed for this mode. """
        pass

    def wait_for_end_choice(self) -> str:
        """Overrides base method to add a 'replay' option."""
        self.console.print("\n[bold green]Progression terminée ![/bold green] Appuyez sur 'r' pour rejouer, 'q' pour quitter, ou une autre touche pour continuer...")
        enable_raw_mode()
        try:
            while not self.exit_flag:
                char = wait_for_input(timeout=0.05)
                if char:
                    if char.lower() == 'q':
                        self.exit_flag = True
                        return 'quit'
                    elif char.lower() == 'r':
                        return 'repeat'
                    else:
                        return 'continue'
                time.sleep(0.01)
        finally:
            disable_raw_mode()
        return 'continue'

    def _get_next_progression_info(self):
        """
        Generates a new musically coherent, weighted random progression.
        """
        random_key = random.choice(list(gammes_majeures.keys()))
        diatonic_chords = gammes_majeures[random_key]
        chord_errors = get_chord_errors()
        weights = [1 + (chord_errors.get(chord, 0) ** 2) for chord in diatonic_chords]
        prog_len = random.randint(self.progression_length[0], self.progression_length[1])
        progression_names = weighted_sample_without_replacement(diatonic_chords, weights, k=prog_len)
        progression_names = [name for name in progression_names if name in self.chord_set]

        if len(progression_names) < 2:
            return self._get_next_progression_info()

        return {
            "progression_accords": progression_names,
            "header_title": "Passage d'Accords",
            "header_name": "Mode Passage d'Accords",
            "border_style": "purple",
            "key_name": random_key,
            "pre_display": None,
            "debug_info": None,
        }

def chord_transitions_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set, use_voice_leading_display=False):
    # This mode works best with three_note_chords
    mode_chord_set = three_note_chords
    # This mode uses transitions by default, so we pass True for use_transitions, and False for display
    mode = ChordTransitionsMode(inport, outport, use_timer, timer_duration, play_progression_before_start, mode_chord_set, True, False)
    mode.run()
