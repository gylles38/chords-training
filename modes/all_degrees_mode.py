# modes/all_degrees_mode.py
import random

from rich.table import Table

from .chord_mode_base import ChordModeBase
from data.chords import gammes_majeures
from screen_handler import int_to_roman

class AllDegreesMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.progression_selection_mode = progression_selection_mode
        self.play_progression_before_start = play_progression_before_start

    def display_degrees_table(self, tonalite, gammes_filtrees):
        table = Table(title=f"\nTableau des degrés pour {tonalite}", border_style="purple")
        table.add_column("Degré", justify="center", style="bold cyan")
        table.add_column("Accord", justify="center", style="bold yellow")

        for i, chord_name in enumerate(gammes_filtrees, 1):
            roman_degree = int_to_roman(i)
            table.add_row(roman_degree, chord_name)

        self.console.print(table)

    def run(self):
        last_tonalite = None
        while not self.exit_flag:
            tonalite, gammes = random.choice(list(gammes_majeures.items()))
            if tonalite == last_tonalite:
                tonalite, gammes = random.choice(list(gammes_majeures.items()))
            last_tonalite = tonalite

            gammes_filtrees = [g for g in gammes if g in self.chord_set]
            if len(gammes_filtrees) < 3:
                continue

            progression_accords = gammes_filtrees

            def pre_display():
                self.console.print(f"Dans la tonalité de [bold yellow]{tonalite}[/bold yellow], jouez la gamme complète :")
                play_mode = getattr(self, "play_progression_before_start", "NONE")
                if play_mode != 'PLAY_ONLY':
                    self.console.print(f"[bold yellow]{' -> '.join(progression_accords)}[/bold yellow]")
                self.display_degrees_table(tonalite, gammes_filtrees)

            result = self.run_progression(
                progression_accords=progression_accords,
                header_title="Gamme Complète",
                header_name="Mode Tous les Degrés",
                border_style="purple",
                pre_display=pre_display,
            )

            if result == 'exit':
                break
            # 'skipped' ou 'done' → on enchaîne sur une nouvelle tonalité

        # Fin de session : afficher les stats globales
        self.show_overall_stats_and_wait()


def all_degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    mode = AllDegreesMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set)
    mode.run()