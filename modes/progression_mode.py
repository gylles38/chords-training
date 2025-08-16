# modes/progression_mode.py
import random
from .chord_mode_base import ChordModeBase
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

class ProgressionMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.progression_selection_mode = progression_selection_mode  # conservé pour compat
        self.play_progression_before_start = play_progression_before_start

    def run(self):
        last_progression = []
        chord_errors = get_chord_errors()

        while not self.exit_flag:
            # Générer une progression aléatoire, différente de la précédente
            prog_len = random.randint(3, 5)

            all_chords = list(self.chord_set.keys())
            # Poids de base de 1 pour chaque accord, plus le carré du nombre d'erreurs
            weights = [1 + (chord_errors.get(chord, 0) ** 2) for chord in all_chords]

            # --- DEBUG DISPLAY ---
            self.console.print("\n[bold dim]-- Debug: Top 5 Weighted Chords --[/bold dim]")
            weighted_chords = sorted(zip(all_chords, weights), key=lambda x: x[1], reverse=True)
            for chord, weight in weighted_chords[:5]:
                self.console.print(f"[dim] - {chord}: {weight}[/dim]")
            # --- END DEBUG ---

            progression_accords = weighted_sample_without_replacement(all_chords, weights, k=prog_len)

            while progression_accords == last_progression:
                progression_accords = weighted_sample_without_replacement(all_chords, weights, k=prog_len)

            last_progression = progression_accords

            result = self.run_progression(
                progression_accords=progression_accords,
                header_title="Progressions d'Accords",
                header_name="Mode Progressions d'Accords",
                border_style="blue",
                pre_display=None,  # Rien de spécifique avant l'affichage pour ce mode
            )

            if result == 'exit':
                break

        # Fin de session : afficher les stats globales
        self.show_overall_stats_and_wait()

def progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    mode = ProgressionMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set)
    mode.run()
