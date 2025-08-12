# modes/degrees_mode.py
import time

from rich.live import Live
from rich.table import Table
from rich.panel import Panel

from .chord_mode_base import ChordModeBase

from ui import get_colored_notes_string
from keyboard_handler import wait_for_input
from screen_handler import int_to_roman

class DegreesMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer  # Not used in current logic, kept for consistency
        self.timer_duration = timer_duration  # Not used in current logic, kept for consistency
        self.progression_selection_mode = progression_selection_mode  # Not used in current logic, kept for consistency
        self.play_progression_before_start = play_progression_before_start  # Not used in current logic, kept for consistency

    def create_degree_display(self, degree_num, tonalite, chord_name):
        return Panel(
            f"Jouez le degré [bold cyan]{degree_num}[/bold cyan]: [bold yellow]{chord_name}[/bold yellow]", 
            title="Degré à jouer", 
            border_style="green"
        )

    def display_degrees_table(self, tonalite, gammes_filtrees):
        table = Table(title=f"\nTableau des degrés pour \n[bold yellow]{tonalite}[/bold yellow]", border_style="green")
        table.add_column("Degré", justify="center", style="bold cyan")
        table.add_column("Accord", justify="center", style="bold yellow")

        for i, chord_name in enumerate(gammes_filtrees, 1):
            roman_degree = int_to_roman(i)
            table.add_row(roman_degree, chord_name)

        self.console.print(table)

    def run(self):
        while not self.exit_flag:
            self.clear_midi_buffer()
            self.display_header("Entraînement par Degrés", "Mode Degrés", "green")
            self.console.print("Jouez l'accord correspondant au degré affiché.")
            self.console.print("Appuyez sur 'q' pour quitter.")

            # Choisir une tonalité aléatoire
            from data.chords import gammes_majeures  # Assuming this is where gammes_majeures is defined
            import random
            tonalite, gammes = random.choice(list(gammes_majeures.items()))
            gammes_filtrees = [g for g in gammes if g in self.chord_set]

            if len(gammes_filtrees) < 3:
                continue

            self.display_degrees_table(tonalite, gammes_filtrees)

            # Choisir un accord aléatoire dans la gamme
            chord_name = random.choice(gammes_filtrees)
            target_notes = self.chord_set[chord_name]
            degree_number = int_to_roman(gammes_filtrees.index(chord_name) + 1)

            chord_attempts = 0

            # Boucle avec Live display
            with Live(console=self.console, screen=False, auto_refresh=False) as live:
                live.update(self.create_degree_display(degree_number, tonalite, chord_name), refresh=True)

                notes_currently_on = set()
                attempt_notes = set()

                while not self.exit_flag:
                    char = wait_for_input(timeout=0.01)
                    if char and self.handle_keyboard_input(char):
                        break

                    for msg in self.inport.iter_pending():
                        if msg.type == 'note_on' and msg.velocity > 0:
                            notes_currently_on.add(msg.note)
                            attempt_notes.add(msg.note)
                        elif msg.type == 'note_off':
                            notes_currently_on.discard(msg.note)

                    if not notes_currently_on and attempt_notes:
                        chord_attempts += 1
                        self.total_attempts += 1

                        is_correct, recognized_name, recognized_inversion = self.check_chord(
                            attempt_notes, chord_name, target_notes
                        )

                        if is_correct:
                            colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                            success_msg = f"[bold green]Correct ! Degré {degree_number}: {chord_name}[/bold green]\nNotes jouées : [{colored_notes}]"
                            live.update(success_msg, refresh=True)
                            time.sleep(2)
                            if chord_attempts == 1:
                                self.correct_count += 1
                            self.total_attempts += 1  # Adjusted to align with session_total_count
                            break
                        else:
                            colored_string = get_colored_notes_string(attempt_notes, target_notes)
                            error_msg = f"[bold red]Incorrect.[/bold red] Vous avez joué : {recognized_name if recognized_name else 'Accord non reconnu'}\nNotes jouées : [{colored_string}]"
                            live.update(error_msg, refresh=True)
                            time.sleep(2)
                            live.update(self.create_degree_display(degree_number, tonalite, chord_name), refresh=True)
                            attempt_notes.clear()

                    time.sleep(0.01)

        self.display_final_stats()

def degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    mode = DegreesMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set)
    mode.run()