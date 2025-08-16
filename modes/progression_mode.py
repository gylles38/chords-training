# modes/progression_mode.py
import random
from .chord_mode_base import ChordModeBase

class ProgressionMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.progression_selection_mode = progression_selection_mode  # conservé pour compat
        self.play_progression_before_start = play_progression_before_start

    def run(self):
        last_progression = []
        while not self.exit_flag:
            # Générer une progression aléatoire, différente de la précédente
            prog_len = random.randint(3, 5)
            progression_accords = random.sample(list(self.chord_set.keys()), prog_len)
            while progression_accords == last_progression:
                progression_accords = random.sample(list(self.chord_set.keys()), prog_len)
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
