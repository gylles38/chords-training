# modes/degrees_mode.py
import random

from rich.table import Table

from .chord_mode_base import ChordModeBase
from data.chords import gammes_majeures
from screen_handler import int_to_roman

class DegreesMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer  # conservé pour compat
        self.timer_duration = timer_duration  # conservé pour compat
        self.progression_selection_mode = progression_selection_mode  # conservé pour compat
        self.play_progression_before_start = play_progression_before_start
        # Supprime l'affichage/pause de fin de progression (un seul accord)
        self.suppress_progression_summary = True

    def display_degrees_table(self, tonalite, gammes_filtrees):
        table = Table(title=f"\nTableau des degrés pour \n[bold yellow]{tonalite}[/bold yellow]", border_style="green")
        table.add_column("Degré", justify="center", style="bold cyan")
        table.add_column("Accord", justify="center", style="bold yellow")

        for i, chord_name in enumerate(gammes_filtrees, 1):
            roman_degree = int_to_roman(i)
            table.add_row(roman_degree, chord_name)

        self.console.print(table)

    def run(self):
        active_degree_pos = None  # 0-based dans la liste filtrée
        while not self.exit_flag:
            # Choisir une tonalité aléatoire et filtrer selon les accords disponibles
            tonalite, gammes = random.choice(list(gammes_majeures.items()))
            gammes_filtrees = [g for g in gammes if g in self.chord_set]

            # Besoin d'au moins quelques accords pour que le tableau soit pertinent
            if len(gammes_filtrees) < 3:
                continue

            # Initialiser ou valider la position de degré active selon la gamme filtrée
            if active_degree_pos is None or active_degree_pos >= len(gammes_filtrees):
                active_degree_pos = random.randint(0, len(gammes_filtrees) - 1)

            # Si la tonalité choisie ne possède pas ce degré (après filtre), chercher une autre tonalité
            if active_degree_pos >= len(gammes_filtrees):
                continue

            chord_name = gammes_filtrees[active_degree_pos]
            degree_number = int_to_roman(active_degree_pos + 1)

            # Affichage spécifique avant la progression
            def pre_display():
                self.console.print(
                    f"Dans la tonalité de [bold yellow]{tonalite}[/bold yellow], jouez le degré actif [bold cyan]{degree_number}[/bold cyan] :"
                )
                self.console.print(f"[bold yellow]{chord_name}[/bold yellow]")
                self.display_degrees_table(tonalite, gammes_filtrees)

            result = self.run_progression(
                progression_accords=[chord_name],
                header_title="Entraînement par Degrés",
                header_name="Mode Degrés",
                border_style="green",
                pre_display=pre_display,
            )

            if result == 'exit':
                break
            # Sinon, on continue la boucle pour demander un nouvel accord du même degré actif dans une nouvelle tonalité

        # Fin de session : afficher les stats globales uniquement à la sortie
        self.show_overall_stats_and_wait()

def degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    mode = DegreesMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set)
    mode.run()