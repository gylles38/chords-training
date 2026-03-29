# modes/single_chord_mode.py
import random
from .chord_mode_base import ChordModeBase

class SingleChordMode(ChordModeBase):
    def __init__(self, inport, outport, current_chord_set):
        super().__init__(inport, outport, current_chord_set)
        # Pas de timer ni de lecture préalable pour ce mode
        self.use_timer = False
        self.timer_duration = 0.0
        self.play_progression_before_start = False
        # Ne pas afficher les stats par progression (un seul accord)
        self.suppress_progression_summary = True

    def run(self):
        from music_theory import get_chord_display_name
        last_chord_name = None
        while not self.exit_flag:
            # Choisir un nouvel accord différent du précédent si possible
            chord_name = random.choice(list(self.chord_set.keys()))
            if len(self.chord_set) > 1:
                while chord_name == last_chord_name:
                    chord_name = random.choice(list(self.chord_set.keys()))
            last_chord_name = chord_name

            def pre_display():
                display_name = get_chord_display_name(chord_name)
                self.console.print(f"\nJouez : [bold bright_yellow]{display_name}[/bold bright_yellow]")

            result = self.run_progression(
                progression_accords=[chord_name],
                header_title="Accords Simples",
                header_name="Mode Accords Simples",
                border_style="yellow",
                pre_display=pre_display,
            )

            if result == 'exit':
                break
            # 'skipped' ou 'done' → on enchaîne sur un nouvel accord

        # Fin de session : afficher les stats globales uniquement à la sortie
        self.show_overall_stats_and_wait()


def single_chord_mode(inport, outport, current_chord_set):
    mode = SingleChordMode(inport, outport, current_chord_set)
    mode.run()