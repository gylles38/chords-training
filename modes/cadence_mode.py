# modes/cadence_mode.py
import random
from rich.table import Table

from .chord_mode_base import ChordModeBase
from stats_manager import get_chord_errors
from screen_handler import int_to_roman
from data.chords import gammes_majeures, cadences, DEGREE_MAP
from ui import create_degrees_table

class CadenceMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set, use_voice_leading):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.progression_selection_mode = progression_selection_mode  # conservé pour compat
        self.play_progression_before_start = play_progression_before_start
        self.use_voice_leading = use_voice_leading

        self.current_tonalite = None
        self.current_cadence_name = None
        self.current_degres = None
        self.current_progression = None
        self.gammes_filtrees = None
        self.last_cadence_info = None

    # ---------- Spécifique Cadence ----------
    def display_degrees_table(self, tonalite, gammes_filtrees):
        """Affiche le tableau des degrés pour la tonalité donnée en utilisant la fonction centralisée."""
        table = create_degrees_table(tonalite, gammes_filtrees)
        self.console.print(table)

    def run(self):
        # Pre-calculate all valid cadences once
        valid_cadences = []
        for tonalite, accords_de_la_gamme in gammes_majeures.items():
            for nom_cadence, degres_cadence in cadences.items():
                try:
                    progression_accords = [accords_de_la_gamme[DEGREE_MAP[d]] for d in degres_cadence]
                    if all(accord in self.chord_set for accord in progression_accords):
                        gammes_filtrees = [g for g in accords_de_la_gamme if g in self.chord_set]
                        valid_cadences.append({
                            "tonalite": tonalite,
                            "nom_cadence": nom_cadence,
                            "degres": degres_cadence,
                            "progression": progression_accords,
                            "gammes_filtrees": gammes_filtrees,
                            # Weight will be calculated in the loop
                        })
                except (KeyError, IndexError):
                    continue

        if not valid_cadences:
            self.console.print("[bold red]Aucune cadence valide trouvée pour le set d'accords sélectionné.[/bold red]")
            return

        last_cadence_info = None
        current_progression = None
        debug_info = None

        while not self.exit_flag:
            if current_progression is None:
                chord_errors = get_chord_errors()

                # Recalculate weights in each iteration
                for cadence in valid_cadences:
                    cadence['weight'] = 1 + sum(chord_errors.get(chord, 0) ** 2 for chord in cadence['progression'])

                # Select a weighted random cadence
                cadence_weights = [c['weight'] for c in valid_cadences]

                # --- DEBUG DISPLAY ---
                debug_info = "\n[bold dim]-- Debug: Top 5 Weighted Cadences --[/bold dim]\n"
                weighted_cadences = sorted(valid_cadences, key=lambda x: x['weight'], reverse=True)
                for c in weighted_cadences[:5]:
                    if c['weight'] > 1:
                        debug_info += f"[dim] - {c['tonalite']} {c['nom_cadence']}: {c['weight']}[/dim]\n"
                # --- END DEBUG ---

                selected_cadence = random.choices(valid_cadences, weights=cadence_weights, k=1)[0]

                while (selected_cadence['tonalite'], selected_cadence['nom_cadence']) == last_cadence_info:
                    selected_cadence = random.choices(valid_cadences, weights=cadence_weights, k=1)[0]

                last_cadence_info = (selected_cadence['tonalite'], selected_cadence['nom_cadence'])

                self.current_tonalite = selected_cadence['tonalite']
                self.current_cadence_name = selected_cadence['nom_cadence']
                self.current_degres = selected_cadence['degres']
                current_progression = selected_cadence['progression']
                self.gammes_filtrees = selected_cadence['gammes_filtrees']

            degres_str = ' -> '.join(self.current_degres)
            progression_str = ' -> '.join(current_progression)

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
                progression_accords=current_progression,
                header_title="Cadences",
                header_name="Mode Cadences Musicales",
                border_style="magenta",
                pre_display=pre_display,
                debug_info=debug_info,
                key_name=self.current_tonalite
            )

            if result == 'exit':
                break
            elif result == 'repeat':
                pass # Rejoue la même cadence
            elif result == 'continue' or result == 'skipped':
                current_progression = None # Force la sélection d'une nouvelle cadence

        # Fin de session : afficher les stats globales
        self.show_overall_stats_and_wait()

def cadence_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set, use_voice_leading):
    mode = CadenceMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set, use_voice_leading)
    mode.run()
