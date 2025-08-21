# modes/chord_transitions_mode.py
import random
import time
from typing import List, Tuple

from .chord_mode_base import ChordModeBase
from data.chords import three_note_chords, gammes_majeures
from stats_manager import get_chord_errors
from keyboard_handler import wait_for_input, enable_raw_mode, disable_raw_mode
from screen_handler import clear_screen

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

class ChordTransitionsMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set, use_timer, timer_duration, play_progression_before_start):
        super().__init__(inport, outport, chord_set)
        self.progression_length = (2, 4)
        self.use_voice_leading = True  # Enable voice leading in base class
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.play_progression_before_start = play_progression_before_start

    def _generate_progression(self) -> Tuple[List[str], str]:
        """Generates a musically coherent, weighted random progression."""
        # 1. Pick a random key and its diatonic chords
        random_key = random.choice(list(gammes_majeures.keys()))
        diatonic_chords = gammes_majeures[random_key]

        # 2. Get user stats and calculate weights for these chords
        chord_errors = get_chord_errors()
        weights = [1 + (chord_errors.get(chord, 0) ** 2) for chord in diatonic_chords]

        # 3. Generate a weighted random progression from the diatonic chords
        prog_len = random.randint(self.progression_length[0], self.progression_length[1])
        progression_names = weighted_sample_without_replacement(diatonic_chords, weights, k=prog_len)

        # 4. Ensure the generated chords exist in the current chord set
        progression_names = [name for name in progression_names if name in self.chord_set]

        return progression_names, random_key

    def run(self):
        """Main loop for the chord transitions mode."""
        while not self.exit_flag:
            # Generate a new progression for the outer loop
            progression_names, key_name = self._generate_progression()

            if len(progression_names) < 2:
                continue

            # Inner loop for replaying the same progression
            while not self.exit_flag:
                result = self.run_progression(
                    progression_accords=progression_names,
                    header_title="Passage d'Accords",
                    header_name="Mode Passage d'Accords",
                    border_style="purple",
                    key_name=key_name,
                )

                if result == 'repeat':
                    clear_screen()
                    continue # Repeat the inner loop
                else: # 'continue', 'quit', or 'skipped'
                    break # Break the inner loop to generate a new progression

            if self.exit_flag: # Handles the 'q' case from wait_for_end_choice
                break

        self.show_overall_stats_and_wait()


def chord_transitions_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    # This mode works best with three_note_chords
    mode_chord_set = three_note_chords
    mode = ChordTransitionsMode(inport, outport, mode_chord_set, use_timer, timer_duration, play_progression_before_start)
    mode.run()
