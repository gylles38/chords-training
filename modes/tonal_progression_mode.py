# modes/tonal_progression_mode.py
import random
from .progression_mode_base import ProgressionModeBase
from stats_manager import get_chord_errors
from data.chords import gammes_majeures, tonal_progressions, DEGREE_MAP

class TonalProgressionMode(ProgressionModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions, use_voice_leading_display=False):
        super().__init__(inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions, use_voice_leading_display)
        self.valid_progressions = []
        self.last_prog_info = None
        # These will be set in _get_next_progression_info
        self.current_tonalite = None
        self.current_progression_name = None
        self.current_progression_description = None

    def _setup_progressions(self):
        """
        Calculates all valid tonal progressions based on the selected chord set.
        """
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
                    self.valid_progressions.append({
                        "tonalite": tonalite,
                        "prog_name": prog_name,
                        "description": prog_data["description"],
                        "progression": prog_accords,
                    })

        if not self.valid_progressions:
            self.console.print("[bold red]Aucune progression tonale valide trouvée pour le set d'accords.[/bold red]")
            # Returning None from _get_next_progression_info will stop the loop

    def display_tonal_info(self):
        """Affiche les informations tonales spécifiques."""
        self.console.print(f"Tonalité : [bold yellow]{self.current_tonalite}[/bold yellow]")
        self.console.print(f"Progression : [bold cyan]{self.current_progression_name}[/bold cyan]")
        if self.current_progression_description:
            self.console.print(f"[italic]{self.current_progression_description}[/italic]")

    def _get_next_progression_info(self):
        """
        Selects a weighted random tonal progression and returns its details.
        """
        if not self.valid_progressions:
            return None

        chord_errors = get_chord_errors()

        for prog in self.valid_progressions:
            prog['weight'] = 1 + sum(chord_errors.get(chord, 0) ** 2 for chord in prog['progression'])

        prog_weights = [p['weight'] for p in self.valid_progressions]

        debug_info = "\n[bold dim]-- Debug: Top 5 Weighted Tonal Progressions --[/bold dim]\n"
        weighted_progs = sorted(self.valid_progressions, key=lambda x: x['weight'], reverse=True)
        for p in weighted_progs[:5]:
            if p['weight'] > 1:
                debug_info += f"[dim] - {p['tonalite']} {p['prog_name']}: {p['weight']}[/dim]\n"

        selected_prog = random.choices(self.valid_progressions, weights=prog_weights, k=1)[0]

        while (selected_prog['tonalite'], selected_prog['prog_name']) == self.last_prog_info:
            selected_prog = random.choices(self.valid_progressions, weights=prog_weights, k=1)[0]

        self.last_prog_info = (selected_prog['tonalite'], selected_prog['prog_name'])
        self.current_tonalite = selected_prog['tonalite']
        self.current_progression_name = selected_prog['prog_name']
        self.current_progression_description = selected_prog['description']

        return {
            "progression_accords": selected_prog['progression'],
            "header_title": "Progression Tonale",
            "header_name": "Mode Progression Tonale",
            "border_style": "bright_magenta",
            "pre_display": self.display_tonal_info,
            "debug_info": debug_info,
            "key_name": self.current_tonalite
        }

def tonal_progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set, use_transitions=False, use_voice_leading_display=False):
    # The progression_selection_mode is kept here for compatibility with main.py, but it's not used in the class.
    mode = TonalProgressionMode(inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions, use_voice_leading_display)
    mode.run()