# modes/cadence_mode.py
import random
from rich.table import Table

from .progression_mode_base import ProgressionModeBase
from stats_manager import get_chord_errors
from screen_handler import int_to_roman
from data.chords import gammes_majeures, cadences, DEGREE_MAP

class CadenceMode(ProgressionModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions):
        super().__init__(inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions)
        self.valid_cadences = []
        self.last_cadence_info = None
        # These will be set in _get_next_progression_info
        self.current_tonalite = None
        self.current_cadence_name = None
        self.current_degres = None
        self.gammes_filtrees = None

    def _setup_progressions(self):
        """
        Pre-calculates all valid cadences based on the selected chord set.
        """
        for tonalite, accords_de_la_gamme in gammes_majeures.items():
            for nom_cadence, degres_cadence in cadences.items():
                try:
                    progression_accords = [accords_de_la_gamme[DEGREE_MAP[d]] for d in degres_cadence]
                    if all(accord in self.chord_set for accord in progression_accords):
                        gammes_filtrees = [g for g in accords_de_la_gamme if g in self.chord_set]
                        self.valid_cadences.append({
                            "tonalite": tonalite,
                            "nom_cadence": nom_cadence,
                            "degres": degres_cadence,
                            "progression": progression_accords,
                            "gammes_filtrees": gammes_filtrees,
                        })
                except (KeyError, IndexError):
                    continue

        if not self.valid_cadences:
            self.console.print("[bold red]Aucune cadence valide trouvée pour le set d'accords sélectionné.[/bold red]")

    def display_degrees_table(self, tonalite, gammes_filtrees):
        """Affiche le tableau des degrés pour la tonalité donnée"""
        table = Table(title=f"\nTableau des degrés pour \n[bold yellow]{tonalite}[/bold yellow]", border_style="magenta")
        table.add_column("Degré", justify="center", style="bold cyan")
        table.add_column("Accord", justify="center", style="bold yellow")

        for i, chord_name in enumerate(gammes_filtrees, 1):
            roman_degree = int_to_roman(i)
            table.add_row(roman_degree, chord_name)
        self.console.print(table)

    def _get_next_progression_info(self):
        """
        Selects a weighted random cadence and returns its details.
        """
        if not self.valid_cadences:
            return None

        chord_errors = get_chord_errors()

        for cadence in self.valid_cadences:
            cadence['weight'] = 1 + sum(chord_errors.get(chord, 0) ** 2 for chord in cadence['progression'])

        cadence_weights = [c['weight'] for c in self.valid_cadences]

        debug_info = "\n[bold dim]-- Debug: Top 5 Weighted Cadences --[/bold dim]\n"
        weighted_cadences = sorted(self.valid_cadences, key=lambda x: x['weight'], reverse=True)
        for c in weighted_cadences[:5]:
            if c['weight'] > 1:
                debug_info += f"[dim] - {c['tonalite']} {c['nom_cadence']}: {c['weight']}[/dim]\n"

        selected_cadence = random.choices(self.valid_cadences, weights=cadence_weights, k=1)[0]

        while (selected_cadence['tonalite'], selected_cadence['nom_cadence']) == self.last_cadence_info:
            selected_cadence = random.choices(self.valid_cadences, weights=cadence_weights, k=1)[0]

        self.last_cadence_info = (selected_cadence['tonalite'], selected_cadence['nom_cadence'])
        self.current_tonalite = selected_cadence['tonalite']
        self.current_cadence_name = selected_cadence['nom_cadence']
        self.current_degres = selected_cadence['degres']
        self.gammes_filtrees = selected_cadence['gammes_filtrees']

        def pre_display():
            degres_str = ' -> '.join(self.current_degres)
            progression_str = ' -> '.join(selected_cadence['progression'])
            self.console.print(f"Dans la tonalité de [bold yellow]{self.current_tonalite}[/bold yellow], "
                               f"jouez la [bold cyan]{self.current_cadence_name}[/bold cyan] "
                               f"([bold cyan]{degres_str}[/bold cyan]) :")

            play_mode = getattr(self, "play_progression_before_start", "NONE")
            if play_mode != 'PLAY_ONLY':
                self.console.print(f"[bold yellow]{progression_str}[/bold yellow]")
                self.display_degrees_table(self.current_tonalite, self.gammes_filtrees)

        return {
            "progression_accords": selected_cadence['progression'],
            "header_title": "Cadences",
            "header_name": "Mode Cadences Musicales",
            "border_style": "magenta",
            "pre_display": pre_display,
            "debug_info": debug_info,
            "key_name": self.current_tonalite
        }

def cadence_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set, use_transitions=False):
    mode = CadenceMode(inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions)
    mode.run()
