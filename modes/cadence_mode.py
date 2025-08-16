# modes/cadence_mode.py
import random
from rich.table import Table

from .chord_mode_base import ChordModeBase
from screen_handler import int_to_roman
from data.chords import gammes_majeures, cadences, DEGREE_MAP

class CadenceMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.progression_selection_mode = progression_selection_mode  # conservé pour compat
        self.play_progression_before_start = play_progression_before_start

        self.current_tonalite = None
        self.current_cadence_name = None
        self.current_degres = None
        self.current_progression = None
        self.gammes_filtrees = None

    # ---------- Spécifique Cadence ----------
    def display_degrees_table(self, tonalite, gammes_filtrees):
        """Affiche le tableau des degrés pour la tonalité donnée"""
        table = Table(title=f"\nTableau des degrés pour \n[bold yellow]{tonalite}[/bold yellow]", border_style="magenta")
        table.add_column("Degré", justify="center", style="bold cyan")
        table.add_column("Accord", justify="center", style="bold yellow")

        for i, chord_name in enumerate(gammes_filtrees, 1):
            roman_degree = int_to_roman(i)
            table.add_row(roman_degree, chord_name)

        self.console.print(table)

    def select_valid_cadence(self):
        """Sélectionne une cadence valide avec les accords disponibles"""
        while True:
            tonalite, accords_de_la_gamme = random.choice(list(gammes_majeures.items()))
            nom_cadence, degres_cadence = random.choice(list(cadences.items()))
            try:
                progression_accords = [accords_de_la_gamme[DEGREE_MAP[d]] for d in degres_cadence]
            except (KeyError, IndexError):
                continue

            if all(accord in self.chord_set for accord in progression_accords):
                gammes_filtrees = [g for g in accords_de_la_gamme if g in self.chord_set]
                return tonalite, nom_cadence, degres_cadence, progression_accords, gammes_filtrees

    def run(self):
        while not self.exit_flag:
            # Choisir une cadence valide
            (self.current_tonalite,
             self.current_cadence_name,
             self.current_degres,
             self.current_progression,
             self.gammes_filtrees) = self.select_valid_cadence()

            degres_str = ' -> '.join(self.current_degres)
            progression_str = ' -> '.join(self.current_progression)

            # Pré-affichage spécifique (tableau des degrés + descriptif)
            def pre_display():
                self.console.print(f"Dans la tonalité de [bold yellow]{self.current_tonalite}[/bold yellow], "
                                   f"jouez la [bold cyan]{self.current_cadence_name}[/bold cyan] "
                                   f"([bold cyan]{degres_str}[/bold cyan]) :")

                play_mode = getattr(self, "play_progression_before_start", "NONE")
                if play_mode != 'PLAY_ONLY':
                    self.console.print(f"[bold yellow]{progression_str}[/bold yellow]")
                    self.display_degrees_table(self.current_tonalite, self.gammes_filtrees)

            result = self.run_progression(
                progression_accords=self.current_progression,
                header_title="Cadences",
                header_name="Mode Cadences Musicales",
                border_style="magenta",
                pre_display=pre_display,
            )

            if result == 'exit':
                break
            # 'skipped' ou 'done' → simplement boucler vers une nouvelle cadence

        # Fin de session : afficher les stats globales
        self.show_overall_stats_and_wait()

def cadence_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    mode = CadenceMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set)
    mode.run()
