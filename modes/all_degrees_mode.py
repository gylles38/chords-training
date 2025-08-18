# modes/all_degrees_mode.py
import random
from rich.table import Table

from .progression_mode_base import ProgressionModeBase
from data.chords import gammes_majeures
from screen_handler import int_to_roman

class AllDegreesMode(ProgressionModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions):
        super().__init__(inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions)
        self.last_tonalite = None
        self.show_vl_summary_at_end = True

    def _setup_progressions(self):
        """ No setup needed for this mode. """
        pass

    def display_degrees_table(self, tonalite, gammes_filtrees):
        table = Table(title=f"\nTableau des degrés pour {tonalite}", border_style="purple")
        table.add_column("Degré", justify="center", style="bold cyan")
        table.add_column("Accord", justify="center", style="bold yellow")

        for i, chord_name in enumerate(gammes_filtrees, 1):
            roman_degree = int_to_roman(i)
            table.add_row(roman_degree, chord_name)
        self.console.print(table)

    def _get_next_progression_info(self):
        """
        Selects a new key and builds a progression with all its degrees.
        """
        tonalite, gammes = random.choice(list(gammes_majeures.items()))
        while tonalite == self.last_tonalite:
            tonalite, gammes = random.choice(list(gammes_majeures.items()))
        self.last_tonalite = tonalite

        gammes_filtrees = [g for g in gammes if g in self.chord_set]
        if len(gammes_filtrees) < 3:
            # Not enough chords to form a meaningful progression, try another key
            return self._get_next_progression_info()

        progression_accords = gammes_filtrees

        def pre_display():
            self.console.print(f"Dans la tonalité de [bold yellow]{tonalite}[/bold yellow], jouez la gamme complète :")
            play_mode = getattr(self, "play_progression_before_start", "NONE")
            if play_mode != 'PLAY_ONLY':
                self.console.print(f"[bold yellow]{' -> '.join(progression_accords)}[/bold yellow]")
                self.display_degrees_table(tonalite, gammes_filtrees)

        return {
            "progression_accords": progression_accords,
            "header_title": "Gamme Complète",
            "header_name": "Mode Tous les Degrés",
            "border_style": "purple",
            "pre_display": pre_display,
            "key_name": tonalite,
            "debug_info": None
        }

def all_degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set, use_transitions=False):
    mode = AllDegreesMode(inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions)
    mode.run()