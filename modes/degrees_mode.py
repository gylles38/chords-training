# modes/degrees_mode.py
import random
from rich.table import Table

from .progression_mode_base import ProgressionModeBase
from stats_manager import get_chord_errors
from data.chords import gammes_majeures
from screen_handler import int_to_roman

class DegreesMode(ProgressionModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions):
        super().__init__(inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions)
        self.suppress_progression_summary = True
        self.active_degree_pos = None
        self.last_tonalite = None

    def _setup_progressions(self):
        """ No setup needed for this mode. """
        pass

    def display_degrees_table(self, tonalite, gammes_filtrees):
        table = Table(title=f"\nTableau des degrés pour \n[bold yellow]{tonalite}[/bold yellow]", border_style="green")
        table.add_column("Degré", justify="center", style="bold cyan")
        table.add_column("Accord", justify="center", style="bold yellow")
        for i, chord_name in enumerate(gammes_filtrees, 1):
            roman_degree = int_to_roman(i)
            table.add_row(roman_degree, chord_name)
        self.console.print(table)

    def _get_next_progression_info(self):
        """
        Selects a new key and asks for the currently active degree in that key.
        """
        chord_errors = get_chord_errors()
        tonalites = list(gammes_majeures.keys())
        weights = [1 + sum(chord_errors.get(chord, 0) ** 2 for chord in gammes_majeures[t]) for t in tonalites]

        debug_info = "\n[bold dim]-- Debug: Top 5 Weighted Tonalites --[/bold dim]\n"
        weighted_tonalites = sorted(zip(tonalites, weights), key=lambda x: x[1], reverse=True)
        for t, w in weighted_tonalites[:5]:
            if w > 1:
                debug_info += f"[dim] - {t}: {w}[/dim]\n"

        tonalite = random.choices(tonalites, weights=weights, k=1)[0]
        while tonalite == self.last_tonalite:
            tonalite = random.choices(tonalites, weights=weights, k=1)[0]
        self.last_tonalite = tonalite

        gammes = gammes_majeures[tonalite]
        gammes_filtrees = [g for g in gammes if g in self.chord_set]

        if len(gammes_filtrees) < 3:
            return self._get_next_progression_info()

        if self.active_degree_pos is None or self.active_degree_pos >= len(gammes_filtrees):
            self.active_degree_pos = random.randint(0, len(gammes_filtrees) - 1)

        if self.active_degree_pos >= len(gammes_filtrees):
            return self._get_next_progression_info()

        chord_name = gammes_filtrees[self.active_degree_pos]
        degree_number = int_to_roman(self.active_degree_pos + 1)

        def pre_display():
            self.console.print(
                f"Dans la tonalité de [bold yellow]{tonalite}[/bold yellow], jouez le degré actif [bold cyan]{degree_number}[/bold cyan] :"
            )
            play_mode = getattr(self, "play_progression_before_start", "NONE")
            if play_mode != 'PLAY_ONLY':
                self.console.print(f"[bold yellow]{chord_name}[/bold yellow]")
                self.display_degrees_table(tonalite, gammes_filtrees)

        return {
            "progression_accords": [chord_name],
            "header_title": "Entraînement par Degrés",
            "header_name": "Mode Degrés",
            "border_style": "green",
            "pre_display": pre_display,
            "debug_info": debug_info,
            "key_name": tonalite
        }

def degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set, use_transitions=False):
    mode = DegreesMode(inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions)
    mode.run()