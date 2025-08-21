# modes/pop_rock_mode.py
import random
from rich.table import Table
from rich.prompt import Prompt

from .chord_mode_base import ChordModeBase
from data.chords import pop_rock_progressions


class PopRockMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.progression_selection_mode = progression_selection_mode  # conservé pour compat
        self.play_progression_before_start = play_progression_before_start
        self.use_voice_leading = True

    def run(self):
        while not self.exit_flag:
            # Afficher l'entête et le tableau des progressions disponibles
            self.display_header("Progressions Pop/Rock", "Mode Pop/Rock", "cyan")

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

            # Demander un choix à l'utilisateur
            choices = list(pop_rock_progressions.keys()) + ["q"]
            choice = Prompt.ask("Choisissez une progression (numéro) ou 'q' pour quitter", choices=choices)
            if choice.lower() == "q":
                break

            selected_data = pop_rock_progressions.get(choice)
            if not selected_data:
                continue

            progression_accords = selected_data.get("progression", [])
            progression_str = " -> ".join(progression_accords)
            examples_str = "\n".join(selected_data.get("examples", []))

            def pre_display():
                play_mode = getattr(self, "play_progression_before_start", "NONE")
                if play_mode != 'PLAY_ONLY':
                    self.console.print(f"Progression sélectionnée: [bold yellow]{progression_str}[/bold yellow]")
                if examples_str:
                    self.console.print("Exemples:")
                    self.console.print(examples_str)

            # Boucle interne pour gérer la répétition de la même progression
            while not self.exit_flag:
                result = self.run_progression(
                    progression_accords=progression_accords,
                    header_title="Progressions Pop/Rock",
                    header_name="Mode Pop/Rock",
                    border_style="cyan",
                    pre_display=pre_display,
                )

                if result == 'repeat':
                    continue  # Rejoue la même progression

                # Pour 'exit', 'continue', ou 'skipped', on sort de la boucle interne
                if result == 'exit':
                    self.exit_flag = True # S'assurer que la boucle externe se termine aussi
                break # Retourne au menu de sélection

        # Fin de session : afficher les stats globales
        self.show_overall_stats_and_wait()



def pop_rock_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    mode = PopRockMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set)
    mode.run()
