# modes/all_degrees_mode.py
import time

from rich.live import Live
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel

from .chord_mode_base import ChordModeBase
from midi_handler import play_progression_sequence
from ui import get_colored_notes_string, display_stats_fixed
from keyboard_handler import wait_for_input
from screen_handler import clear_screen
from .degrees_mode import int_to_roman

class AllDegreesMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer  # Not used in current logic, kept for consistency
        self.timer_duration = timer_duration  # Not used in current logic, kept for consistency
        self.progression_selection_mode = progression_selection_mode  # Not used in current logic, kept for consistency
        self.play_progression_before_start = play_progression_before_start

    def handle_keyboard_input(self, char):
        if super().handle_keyboard_input(char):
            return True
        if char and char.lower() == 'r':
            return 'repeat'
        return False

    def create_degrees_display(self, chord_name, prog_index, total_chords, tonalite):
        return Panel(
            f"Accord à jouer ({prog_index + 1}/{total_chords}): [bold yellow]{chord_name}[/bold yellow]", 
            title="Gamme Complète", 
            border_style="purple"
        )

    def display_degrees_table(self, tonalite, gammes_filtrees):
        table = Table(title=f"\nTableau des degrés pour {tonalite}", border_style="purple")
        table.add_column("Degré", justify="center", style="bold cyan")
        table.add_column("Accord", justify="center", style="bold yellow")

        for i, chord_name in enumerate(gammes_filtrees, 1):
            roman_degree = int_to_roman(i)
            table.add_row(roman_degree, chord_name)

        self.console.print(table)

    def run(self):
        last_tonalite = None
        while not self.exit_flag:
            self.clear_midi_buffer()
            self.display_header("Gamme Complète", "Mode Tous les Degrés", "purple")
            self.console.print("Jouez tous les accords de la gamme dans l'ordre.")
            self.console.print("Appuyez sur 'q' pour quitter, 'r' pour entendre la gamme complète.")

            # Choisir une nouvelle tonalité
            from data.chords import gammes_majeures  # Assuming this is where gammes_majeures is defined
            import random
            tonalite, gammes = random.choice(list(gammes_majeures.items()))
            while tonalite == last_tonalite:
                tonalite, gammes = random.choice(list(gammes_majeures.items()))
            last_tonalite = tonalite

            gammes_filtrees = [g for g in gammes if g in self.chord_set]
            if len(gammes_filtrees) < 3:
                continue

            progression_accords = gammes_filtrees
            self.display_degrees_table(tonalite, gammes_filtrees)

            self.console.print(f"\nDans la tonalité de [bold yellow]{tonalite}[/bold yellow], jouez la gamme complète : [bold yellow]{' -> '.join(progression_accords)}[/bold yellow]")

            if self.play_progression_before_start:
                play_progression_sequence(self.outport, progression_accords, self.chord_set)

            progression_correct_count = 0
            progression_total_attempts = 0
            skip_progression = False

            with Live(console=self.console, screen=False, auto_refresh=False) as live:
                prog_index = 0
                while prog_index < len(progression_accords) and not self.exit_flag and not skip_progression:
                    chord_name = progression_accords[prog_index]
                    target_notes = self.chord_set[chord_name]
                    chord_attempts = 0

                    live.update(self.create_degrees_display(chord_name, prog_index, len(progression_accords), tonalite), refresh=True)

                    notes_currently_on = set()
                    attempt_notes = set()

                    while not self.exit_flag:
                        char = wait_for_input(timeout=0.01)
                        if char:
                            action = self.handle_keyboard_input(char)
                            if action == 'repeat':
                                while wait_for_input(timeout=0.001):
                                    pass
                                live.update("[bold cyan]Lecture de la gamme...[/bold cyan]", refresh=True)
                                original_print = print
                                original_console_print = self.console.print
                                import builtins
                                builtins.print = lambda *args, **kwargs: None
                                self.console.print = lambda *args, **kwargs: None
                                try:
                                    play_progression_sequence(self.outport, progression_accords, self.chord_set)
                                finally:
                                    builtins.print = original_print
                                    self.console.print = original_console_print
                                while wait_for_input(timeout=0.001):
                                    pass
                                prog_index = 0
                                chord_name = progression_accords[prog_index]
                                target_notes = self.chord_set[chord_name]
                                live.update(self.create_degrees_display(chord_name, prog_index, len(progression_accords), tonalite), refresh=True)
                                break

                        for msg in self.inport.iter_pending():
                            if msg.type == 'note_on' and msg.velocity > 0:
                                notes_currently_on.add(msg.note)
                                attempt_notes.add(msg.note)
                            elif msg.type == 'note_off':
                                notes_currently_on.discard(msg.note)

                        if not notes_currently_on and attempt_notes:
                            chord_attempts += 1
                            progression_total_attempts += 1

                            is_correct, recognized_name, recognized_inversion = self.check_chord(
                                attempt_notes, chord_name, target_notes
                            )

                            if is_correct:
                                success_msg = f"[bold green]Correct ! {chord_name}[/bold green]\nNotes jouées : [{get_colored_notes_string(attempt_notes, target_notes)}]"
                                live.update(success_msg, refresh=True)
                                time.sleep(2)
                                if chord_attempts == 1:
                                    progression_correct_count += 1
                                prog_index += 1
                                break
                            else:
                                error_msg = f"[bold red]Incorrect.[/bold red] Vous avez joué : {recognized_name if recognized_name else 'Accord non reconnu'}\nNotes jouées : [{get_colored_notes_string(attempt_notes, target_notes)}]"
                                live.update(error_msg, refresh=True)
                                time.sleep(2)
                                live.update(self.create_degrees_display(chord_name, prog_index, len(progression_accords), tonalite), refresh=True)
                                attempt_notes.clear()

                        time.sleep(0.01)

                if self.exit_flag:
                    break

            if not self.exit_flag and not skip_progression:
                self.correct_count += progression_correct_count
                self.total_attempts += progression_total_attempts  # Removed the extra len(progression_accords)

                self.console.print(f"\n--- Statistiques de cette progression ---")
                self.console.print(f"Accords à jouer : [bold cyan]{len(progression_accords)}[/bold cyan]")
                self.console.print(f"Tentatives totales : [bold yellow]{progression_total_attempts}[/bold yellow]")
                self.console.print(f"Réussis du premier coup : [bold green]{progression_correct_count}[/bold green]")

                if progression_total_attempts > 0:
                    accuracy = (progression_correct_count / progression_total_attempts) * 100
                    self.console.print(f"Précision : [bold cyan]{accuracy:.1f}%[/bold cyan]")

                choice = Prompt.ask("\nProgression terminée ! Appuyez sur Entrée pour la suivante ou 'q' pour revenir au menu principal...", console=self.console, choices=["", "q"], show_choices=False)
                if choice == 'q':
                    self.exit_flag = True
                clear_screen()

        self.display_final_stats()

def all_degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    mode = AllDegreesMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set)
    mode.run()
