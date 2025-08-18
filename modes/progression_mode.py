# modes/progression_mode.py
import random
from .progression_mode_base import ProgressionModeBase
from stats_manager import get_chord_errors

def weighted_sample_without_replacement(population, weights, k=1):
    """
    Performs weighted sampling without replacement.
    """
    population = list(population)
    weights = list(weights)

    if len(population) < k:
        # Not enough unique items to sample from. Return a simple random sample.
        return random.sample(population, k)

    result = []
    for _ in range(k):
        if not population: # Should not happen if len(population) >= k
            break

        # random.choices returns a list of size 1
        chosen_element = random.choices(population, weights=weights, k=1)[0]

        # find the index to remove
        chosen_index = population.index(chosen_element)

        # remove from population and weights
        population.pop(chosen_index)
        weights.pop(chosen_index)

        result.append(chosen_element)

    return result

class ProgressionMode(ProgressionModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions):
        # progression_selection_mode is not used, so it's removed.
        super().__init__(inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions)
        self.last_progression = []

    def _setup_progressions(self):
        """
        No setup needed for this mode as progressions are generated on the fly.
        """
        pass

    def _get_next_progression_info(self):
        """
        Generates a new random chord progression and returns its details.
        """
        chord_errors = get_chord_errors()
        prog_len = random.randint(3, 5)

        all_chords = list(self.chord_set.keys())
        weights = [1 + (chord_errors.get(chord, 0) ** 2) for chord in all_chords]

        debug_info = "\n[bold dim]-- Debug: Top 5 Weighted Chords --[/bold dim]\n"
        weighted_chords = sorted(zip(all_chords, weights), key=lambda x: x[1], reverse=True)
        for chord, weight in weighted_chords[:5]:
            if weight > 1:
                debug_info += f"[dim] - {chord}: {weight}[/dim]\n"

        progression_accords = weighted_sample_without_replacement(all_chords, weights, k=prog_len)

        while progression_accords == self.last_progression:
            progression_accords = weighted_sample_without_replacement(all_chords, weights, k=prog_len)

        self.last_progression = progression_accords

        return {
            "progression_accords": progression_accords,
            "header_title": "Progressions d'Accords",
            "header_name": "Mode Progressions d'Accords",
            "border_style": "blue",
            "pre_display": None,
            "debug_info": debug_info,
            "key_name": None
        }

def progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set, use_transitions=False):
    # The progression_selection_mode is kept here for compatibility with main.py, but it's not used in the class.
    mode = ProgressionMode(inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions)
    mode.run()
