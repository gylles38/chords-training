# modes/tonal_progression_mode.py
import random
from .chord_mode_base import ChordModeBase
from stats_manager import get_chord_errors
from data.chords import gammes_majeures, tonal_progressions, DEGREE_MAP

class TonalProgressionMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.progression_selection_mode = progression_selection_mode
        self.play_progression_before_start = play_progression_before_start

    def display_tonal_info(self):
        """Affiche les informations tonales spécifiques."""
        self.console.print(f"Tonalité : [bold yellow]{self.current_tonalite}[/bold yellow]")
        self.console.print(f"Progression : [bold cyan]{self.current_progression_name}[/bold cyan]")
        if self.current_progression_description:
            self.console.print(f"[italic]{self.current_progression_description}[/italic]")

    def run(self):
        """Boucle principale du mode progression tonale."""
        chord_errors = get_chord_errors()

        valid_progressions = []
        for tonalite, gammes in gammes_majeures.items():
            gammes_filtrees = [g for g in gammes if g in self.chord_set]
            for prog_name, prog_data in tonal_progressions.items():
                degres = prog_data["progression"]
                prog_accords = []
                is_valid = True
                for degre in degres:
                    index = DEGREE_MAP.get(degre)
                    if index is not None and index < len(gammes_filtrees):
                        prog_accords.append(gammes_filtrees[index])
                    else:
                        is_valid = False
                        break
                if is_valid:
                    weight = 1 + sum(chord_errors.get(chord, 0) for chord in prog_accords)
                    valid_progressions.append({
                        "tonalite": tonalite,
                        "prog_name": prog_name,
                        "description": prog_data["description"],
                        "progression": prog_accords,
                        "weight": weight
                    })

        if not valid_progressions:
            self.console.print("[bold red]Aucune progression tonale valide trouvée pour le set d'accords.[/bold red]")
            return

        last_prog_info = None
        while not self.exit_flag:
            prog_weights = [p['weight'] for p in valid_progressions]

            # --- DEBUG DISPLAY ---
            self.console.print("\n[bold dim]-- Debug: Top 5 Weighted Tonal Progressions --[/bold dim]")
            weighted_progs = sorted(valid_progressions, key=lambda x: x['weight'], reverse=True)
            for p in weighted_progs[:5]:
                if p['weight'] > 1:
                    self.console.print(f"[dim] - {p['tonalite']} {p['prog_name']}: {p['weight']}[/dim]")
            # --- END DEBUG ---

            selected_prog = random.choices(valid_progressions, weights=prog_weights, k=1)[0]

            while (selected_prog['tonalite'], selected_prog['prog_name']) == last_prog_info:
                selected_prog = random.choices(valid_progressions, weights=prog_weights, k=1)[0]

            last_prog_info = (selected_prog['tonalite'], selected_prog['prog_name'])

            self.current_tonalite = selected_prog['tonalite']
            self.current_progression_name = selected_prog['prog_name']
            self.current_progression_accords = selected_prog['progression']
            self.current_progression_description = selected_prog['description']

            result = self.run_progression(
                progression_accords=self.current_progression_accords,
                header_title="Progression Tonale",
                header_name="Mode Progression Tonale",
                border_style="bright_magenta",
                pre_display=self.display_tonal_info,
            )

            if result == 'exit':
                break

        # Fin de session : afficher les stats globales
        self.show_overall_stats_and_wait()

def tonal_progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    mode = TonalProgressionMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set)
    mode.run()