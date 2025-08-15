# modes/tonal_progression_mode.py
import random
from .chord_mode_base import ChordModeBase
from data.chords import gammes_majeures, tonal_progressions, DEGREE_MAP

class TonalProgressionMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.progression_selection_mode = progression_selection_mode  # conservé pour compat
        self.play_progression_before_start = play_progression_before_start
        
        # État de la progression courante
        self.current_tonalite = None
        self.current_progression_name = None
        self.current_progression_accords = None

    def generate_new_tonal_progression(self):
        """Génère une nouvelle progression tonale aléatoire."""
        # Choisir une tonalité aléatoire
        self.current_tonalite, gammes = random.choice(list(gammes_majeures.items()))
        
        # Filtrer les gammes pour ne garder que les accords disponibles
        gammes_filtrees = [g for g in gammes if g in self.chord_set]
        
        # Choisir une progression aléatoire
        self.current_progression_name, degres_progression = random.choice(list(tonal_progressions.items()))
        
        # Construire la liste des accords à partir des degrés
        self.current_progression_accords = []
        for degre in degres_progression:
            index = DEGREE_MAP.get(degre)
            if index is not None and index < len(gammes_filtrees):
                self.current_progression_accords.append(gammes_filtrees[index])

    def display_tonal_info(self):
        """Affiche les informations tonales spécifiques."""
        self.console.print(f"Tonalité : [bold yellow]{self.current_tonalite}[/bold yellow]")
        self.console.print(f"Progression : [bold cyan]{self.current_progression_name}[/bold cyan]")

    def run(self):
        """Boucle principale du mode progression tonale."""
        while not self.exit_flag:
            # Générer une nouvelle progression si nécessaire
            if self.current_progression_accords is None:
                self.generate_new_tonal_progression()

            # Exécuter la progression avec la méthode commune
            result = self.run_progression(
                progression_accords=self.current_progression_accords,
                header_title="Progression Tonale",
                header_name="Mode Progression Tonale",
                border_style="bright_magenta",
                pre_display=self.display_tonal_info,  # Affichage des infos tonales
            )

            if result == 'exit':
                break
            elif result in ['done', 'skipped']:
                # Préparer une nouvelle progression pour la prochaine itération
                self.generate_new_tonal_progression()

        # Fin de session : afficher les stats globales
        self.show_overall_stats_and_wait()

def tonal_progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    mode = TonalProgressionMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set)
    mode.run()