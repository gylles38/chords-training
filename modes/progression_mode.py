# modes/progression_mode.py
import time
import random

from rich.live import Live
from rich.prompt import Prompt
from rich.panel import Panel

from .chord_mode_base import ChordModeBase

from midi_handler import play_progression_sequence
from ui import get_colored_notes_string, display_stats_fixed
from screen_handler import clear_screen
from keyboard_handler import wait_for_any_key, wait_for_input

class ProgressionMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.progression_selection_mode = progression_selection_mode  # Not used in provided code, kept for completeness
        self.play_progression_before_start = play_progression_before_start
        self.session_correct_count = 0
        self.session_total_count = 0
        self.session_total_attempts = 0
        self.elapsed_time = 0.0

    def handle_keyboard_input(self, char):
        if super().handle_keyboard_input(char):
            return True
        if char and char.lower() == 'r':
            return 'repeat'
        if char and char.lower() == 'n':
            return 'next'
        return False

    def create_live_display(self, chord_name, prog_index, total_chords, time_info=""):
        content = f"Accord à jouer ({prog_index + 1}/{total_chords}): [bold yellow]{chord_name}[/bold yellow]"
        if time_info:
            content += f"\n{time_info}"
        return Panel(content, title="Progression en cours", border_style="green")

    def run(self):
        last_progression = []
        while not self.exit_flag:
            self.clear_midi_buffer()
            self.display_header("Progressions d'Accords", "Mode Progressions d'Accords", "blue")
            self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer à la suivante.")

            prog_len = random.randint(3, 5)
            progression = random.sample(list(self.chord_set.keys()), prog_len)
            while progression == last_progression:
                progression = random.sample(list(self.chord_set.keys()), prog_len)
            last_progression = progression

            self.console.print(f"\nProgression à jouer : [bold yellow]{' -> '.join(progression)}[/bold yellow]")

            if self.play_progression_before_start:
                play_progression_sequence(self.outport, progression, self.chord_set)

            progression_correct_count = 0
            progression_total_attempts = 0
            is_progression_started = False
            start_time = None
            skip_progression = False

            with Live(console=self.console, screen=False, auto_refresh=False) as live:
                prog_index = 0
                while prog_index < len(progression) and not self.exit_flag and not skip_progression:
                    chord_name = progression[prog_index]
                    target_notes = self.chord_set[chord_name]
                    chord_attempts = 0

                    time_info = ""
                    if self.use_timer and is_progression_started:
                        remaining_time = self.timer_duration - (time.time() - start_time)
                        time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"

                    live.update(self.create_live_display(chord_name, prog_index, len(progression), time_info), refresh=True)

                    notes_currently_on = set()
                    attempt_notes = set()

                    while not self.exit_flag and not skip_progression:
                        if self.use_timer and is_progression_started:
                            remaining_time = self.timer_duration - (time.time() - start_time)
                            time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"
                            live.update(self.create_live_display(chord_name, prog_index, len(progression), time_info), refresh=True)

                            if remaining_time <= 0:
                                live.update("[bold red]Temps écoulé ! Session terminée.[/bold red]", refresh=True)
                                time.sleep(2)
                                self.exit_flag = True
                                break

                        char = wait_for_input(timeout=0.01)
                        if char:
                            action = self.handle_keyboard_input(char)
                            if action == 'repeat':
                                while wait_for_input(timeout=0.001):
                                    pass
                                live.update("[bold cyan]Lecture de la progression...[/bold cyan]", refresh=True)
                                original_print = print
                                original_console_print = self.console.print
                                import builtins
                                builtins.print = lambda *args, **kwargs: None
                                self.console.print = lambda *args, **kwargs: None
                                try:
                                    play_progression_sequence(self.outport, progression, self.chord_set)
                                finally:
                                    builtins.print = original_print
                                    self.console.print = original_console_print
                                while wait_for_input(timeout=0.001):
                                    pass
                                # Clear the "Lecture de la progression..." message and return to the first chord
                                prog_index = 0
                                chord_name = progression[prog_index]
                                target_notes = self.chord_set[chord_name]
                                live.update(self.create_live_display(chord_name, prog_index, len(progression)), refresh=True)
                                break
                            elif action == 'next':
                                skip_progression = True
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

                            if self.use_timer and not is_progression_started:
                                is_progression_started = True
                                start_time = time.time()

                            is_correct, recognized_name, recognized_inversion = self.check_chord(attempt_notes, chord_name, target_notes)

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
                                live.update(self.create_live_display(chord_name, prog_index, len(progression)), refresh=True)
                                attempt_notes.clear()

                        time.sleep(0.01)

                if self.exit_flag:
                    break

            if not self.exit_flag and not skip_progression:
                self.session_correct_count += progression_correct_count
                self.session_total_attempts += progression_total_attempts
                self.session_total_count += len(progression)

                self.console.print(f"\n--- Statistiques de cette progression ---")
                self.console.print(f"Accords à jouer : [bold cyan]{len(progression)}[/bold cyan]")
                self.console.print(f"Tentatives totales : [bold yellow]{progression_total_attempts}[/bold yellow]")
                self.console.print(f"Réussis du premier coup : [bold green]{progression_correct_count}[/bold green]")

                if progression_total_attempts > 0:
                    accuracy = (progression_correct_count / progression_total_attempts) * 100
                    self.console.print(f"Précision : [bold cyan]{accuracy:.1f}%[/bold cyan]")

                if self.use_timer and is_progression_started:
                    end_time = time.time()
                    self.elapsed_time = end_time - start_time
                    self.console.print(f"\nTemps pour la progression : [bold cyan]{self.elapsed_time:.2f} secondes[/bold cyan]")

                choice = Prompt.ask("\nProgression terminée ! Appuyez sur Entrée pour la suivante ou 'q' pour revenir au menu principal...", console=self.console, choices=["", "q"], show_choices=False)
                if choice == 'q':
                    self.exit_flag = True
                clear_screen()

            elif skip_progression:
                self.console.print("\n[bold yellow]Passage à la progression suivante.[/bold yellow]")
                time.sleep(1)

        if self.use_timer:
            display_stats_fixed(self.session_correct_count, self.session_total_attempts, self.session_total_count, self.elapsed_time)
        else:
            display_stats_fixed(self.session_correct_count, self.session_total_attempts, self.session_total_count)

        self.console.print("\nAppuyez sur Entrée pour retourner au menu principal.")
        self.clear_midi_buffer()
        wait_for_any_key(self.inport)

def progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    mode = ProgressionMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set)
    mode.run()