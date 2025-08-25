# modes/degrees_mode.py
import random

from rich.table import Table

from .chord_mode_base import ChordModeBase
from stats_manager import get_chord_errors
from data.chords import gammes_majeures
from screen_handler import int_to_roman, clear_screen

class DegreesMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.progression_selection_mode = progression_selection_mode
        self.play_progression_before_start = play_progression_before_start
        self.suppress_progression_summary = False
        self.last_chord_name = None

    def display_degrees_table(self, tonalite, gammes_filtrees):
        table = Table(border_style="green")
        table.add_column("Degré", justify="center", style="bold cyan")
        table.add_column("Accord", justify="center", style="bold yellow")

        for i, chord_name in enumerate(gammes_filtrees, 1):
            roman_degree = int_to_roman(i)
            table.add_row(roman_degree, chord_name)

        self.console.print(table)

    def run(self):
        active_degree_pos = None  # 0-based dans la liste filtrée
        last_tonalite = None

        while not self.exit_flag:
            # --- Outer loop: Generate a new progression ---
            chord_errors = get_chord_errors()
            # Choisir une tonalité de manière pondérée
            tonalites = list(gammes_majeures.keys())
            weights = [1 + sum(chord_errors.get(chord, 0) ** 2 for chord in gammes_majeures[t]) for t in tonalites]

            debug_info = "\n[bold dim]-- Debug: Top 5 Weighted Tonalites --[/bold dim]\n"
            weighted_tonalites = sorted(zip(tonalites, weights), key=lambda x: x[1], reverse=True)
            for t, w in weighted_tonalites[:5]:
                if w > 1:
                    debug_info += f"[dim] - {t}: {w}[/dim]\n"

            tonalite = random.choices(tonalites, weights=weights, k=1)[0]
            while tonalite == last_tonalite:
                tonalite = random.choices(tonalites, weights=weights, k=1)[0]
            last_tonalite = tonalite

            gammes = gammes_majeures[tonalite]
            gammes_filtrees = [g for g in gammes if g in self.chord_set]

            if len(gammes_filtrees) < 3:
                continue

            if active_degree_pos is None or active_degree_pos >= len(gammes_filtrees):
                active_degree_pos = random.randint(0, len(gammes_filtrees) - 1)

            if active_degree_pos >= len(gammes_filtrees):
                continue

            chord_name = gammes_filtrees[active_degree_pos]

            if len(gammes_filtrees) > 1:
                while chord_name == self.last_chord_name:
                    active_degree_pos = random.randint(0, len(gammes_filtrees) - 1)
                    chord_name = gammes_filtrees[active_degree_pos]

            self.last_chord_name = chord_name
            degree_number = int_to_roman(active_degree_pos + 1)

            def pre_display():
                self.console.print(
                    f"Dans la tonalité de [bold yellow]{tonalite}[/bold yellow], jouez le degré actif [bold cyan]{degree_number}[/bold cyan] :"
                )
                play_mode = getattr(self, "play_progression_before_start", "NONE")
                if play_mode != 'PLAY_ONLY':
                    self.console.print(f"[bold yellow]{chord_name}[/bold yellow]")
                    self.display_degrees_table(tonalite, gammes_filtrees)

            # --- Inner loop: Play and repeat the same progression ---
            while not self.exit_flag:
                result = self.run_progression(
                    progression_accords=[chord_name],
                    header_title="Entraînement par Degrés",
                    header_name="Mode Degrés",
                    border_style="green",
                    pre_display=pre_display,
                    debug_info=debug_info
                )

                if result == 'repeat':
                    clear_screen()
                    continue
                else:
                    break

            if self.exit_flag:
                break

        self.show_overall_stats_and_wait()

def degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    mode = DegreesMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set)
    mode.run()