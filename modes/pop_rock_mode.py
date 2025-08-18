# modes/pop_rock_mode.py
import random
from rich.table import Table
from rich.prompt import Prompt

from .progression_mode_base import ProgressionModeBase
from data.chords import pop_rock_progressions


class PopRockMode(ProgressionModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions):
        super().__init__(inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions)

    def _setup_progressions(self):
        """
        No setup needed, the menu is displayed in the loop.
        """
        self.display_header("Progressions Pop/Rock", "Mode Pop/Rock", "cyan")

    def _get_next_progression_info(self):
        """
        Displays the menu of progressions and prompts the user for a choice.
        Returns the details of the chosen progression, or None to exit.
        """
        table = Table(title="Progressions Pop/Rock", border_style="cyan")
        table.add_column("Numéro", style="cyan", justify="center")
        table.add_column("Progression", style="magenta")
        table.add_column("Exemples de chansons", style="yellow")

        for num, data in pop_rock_progressions.items():
            prog_str = " -> ".join(data["progression"]) if isinstance(data.get("progression"), list) else str(data.get("progression", ""))
            examples = data.get("examples", [])
            examples_str = "\n".join(examples) if isinstance(examples, list) else str(examples)
            table.add_row(num, prog_str, examples_str)

        self.console.print(table)

        choices = list(pop_rock_progressions.keys()) + ["q"]
        choice = Prompt.ask("Choisissez une progression (numéro) ou 'q' pour quitter", choices=choices)
        if choice.lower() == "q":
            return None # Signal to exit the main loop

        selected_data = pop_rock_progressions.get(choice)
        if not selected_data:
            # Should not happen with Prompt's choices, but good practice
            return self._get_next_progression_info() # Re-prompt

        progression_accords = selected_data.get("progression", [])

        def pre_display():
            progression_str = " -> ".join(progression_accords)
            examples_str = "\n".join(selected_data.get("examples", []))
            play_mode = getattr(self, "play_progression_before_start", "NONE")
            if play_mode != 'PLAY_ONLY':
                self.console.print(f"Progression sélectionnée: [bold yellow]{progression_str}[/bold yellow]")
            if examples_str:
                self.console.print("Exemples:")
                self.console.print(examples_str)

        return {
            "progression_accords": progression_accords,
            "header_title": "Progressions Pop/Rock",
            "header_name": "Mode Pop/Rock",
            "border_style": "cyan",
            "pre_display": pre_display,
            "debug_info": None,
            "key_name": None
        }


def pop_rock_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set, use_transitions=False):
    mode = PopRockMode(inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions)
    mode.run()
