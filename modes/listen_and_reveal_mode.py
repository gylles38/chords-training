# modes/listen_and_reveal_mode.py
import time
import random
from typing import Literal
from rich.prompt import Prompt

from .chord_mode_base import ChordModeBase
from stats_manager import update_chord_error, update_chord_success

from midi_handler import play_chord
from screen_handler import clear_screen
from music_theory import get_note_name, get_chord_type_from_name
from keyboard_handler import wait_for_input, enable_raw_mode, disable_raw_mode

class ListenAndRevealMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set):
        super().__init__(inport, outport, chord_set)
        self.last_chord_name = None

    def _handle_repeat(self) -> Literal['repeat', False]:
        """Redéfinition pour rejouer l'accord en cours dans ce mode"""
        if hasattr(self, "current_chord_notes") and self.current_chord_notes is not None:
            play_chord(self.outport, self.current_chord_notes)
            return False
        return 'repeat'
    
    def run(self):
        self.display_header("Écoute et Devine", "Mode Écoute et Devine", "orange3")
        self.console.print("Écoutez l'accord joué et essayez de le reproduire.")
        self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer au suivant.")

        enable_raw_mode()
        try:
            while not self.exit_flag:
                self.clear_midi_buffer()

                new_chord_name, new_chord_notes = random.choice(list(self.chord_set.items()))
                while new_chord_name == self.last_chord_name:
                    new_chord_name, new_chord_notes = random.choice(list(self.chord_set.items()))

                self.current_chord_name = new_chord_name
                self.current_chord_notes = new_chord_notes
                self.last_chord_name = new_chord_name

                self.console.print(f"\n[bold yellow]Lecture de l'accord...[/bold yellow]")
                play_chord(self.outport, self.current_chord_notes)
                self.console.print("Jouez l'accord que vous venez d'entendre.")

                incorrect_attempts = 0
                first_attempt = True

                while not self.exit_flag:
                    attempt_notes, ready = self.collect_notes()

                    if attempt_notes is None and ready is None:
                        if self.exit_flag:
                            break
                        else: # 'n' key
                            break

                    if not ready:
                        continue

                    self.session_total_attempts += 1
                    is_correct, recognized_name, recognized_inversion = self.check_chord(
                        attempt_notes, self.current_chord_name, self.current_chord_notes
                    )

                    if is_correct:
                        if first_attempt:
                            self.session_correct_count += 1
                        update_chord_success(self.current_chord_name)
                        self.display_feedback(True, attempt_notes, self.current_chord_notes, recognized_name, recognized_inversion)
                        time.sleep(1.5)
                        break
                    else:
                        first_attempt = False
                        update_chord_error(self.current_chord_name)
                        incorrect_attempts += 1
                        self.display_feedback(False, attempt_notes, self.current_chord_notes, recognized_name, recognized_inversion)

                        if incorrect_attempts >= 3:
                            tonic_note = sorted(list(self.current_chord_notes))[0]
                            tonic_name = get_note_name(tonic_note)
                            self.console.print(f"Indice : La tonique est [bold cyan]{tonic_name}[/bold cyan].")

                        if incorrect_attempts >= 7:
                            revealed_type = get_chord_type_from_name(self.current_chord_name)
                            self.console.print(f"Indice : C'est un accord de type [bold yellow]{revealed_type}[/bold yellow].")
                            self.console.print(f"[bold magenta]La réponse était : {self.current_chord_name}[/bold magenta]")
                            time.sleep(2)
                            break

                self.session_total_count += 1
                if not self.exit_flag:
                    clear_screen()
                    self.display_header("Écoute et Devine", "Mode Écoute et Devine", "orange3")
                    self.console.print("Écoutez l'accord joué et essayez de la reproduire.")
                    self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer au suivant.")

                self.current_chord_notes = None
                self.current_chord_name = None
        finally:
            disable_raw_mode()

        self.show_overall_stats_and_wait()


def listen_and_reveal_mode(inport, outport, chord_set):
    mode = ListenAndRevealMode(inport, outport, chord_set)
    mode.run()