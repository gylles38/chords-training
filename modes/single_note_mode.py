# modes/single_note_mode.py
import time
import random
from typing import Literal
from rich.prompt import Prompt

from .chord_mode_base import ChordModeBase
from midi_handler import play_chord
from screen_handler import clear_screen
from music_theory import get_note_name
from keyboard_handler import wait_for_input, enable_raw_mode, disable_raw_mode, wait_for_any_key

class SingleNoteMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set=None):
        # Le chord_set n'est pas utilisé ici, mais est gardé pour la compatibilité
        super().__init__(inport, outport, chord_set)
        self.current_note = None
        self.last_note = None

    def _handle_repeat(self) -> Literal['repeat', False]:
        """Redéfinition pour rejouer la note en cours dans ce mode"""
        if self.current_note is not None:
            play_chord(self.outport, [self.current_note])
            return False  # ne pas interrompre collect_notes
        return 'repeat'

    def collect_note_listen_mode(self):
        """Version spécialisée pour collecter une seule note."""
        notes_currently_on = set()
        attempt_note = None
        last_note_off_time = None

        enable_raw_mode()
        try:
            while not self.exit_flag:
                char = wait_for_input(timeout=0.01)
                if char:
                    if char.lower() == 'q':
                        self.exit_flag = True
                        return None, None
                    elif char.lower() == 'n':
                        return None, None
                    elif char.lower() == 'r' and self.current_note is not None:
                        disable_raw_mode()
                        play_chord(self.outport, [self.current_note])
                        enable_raw_mode()
                        continue

                for msg in self.inport.iter_pending():
                    if msg.type == 'note_on' and msg.velocity > 0:
                        notes_currently_on.add(msg.note)
                        # On ne prend que la première note jouée pour ce mode
                        if attempt_note is None:
                            attempt_note = msg.note
                        last_note_off_time = None
                    elif msg.type == 'note_off':
                        notes_currently_on.discard(msg.note)
                        if not notes_currently_on and not last_note_off_time:
                            last_note_off_time = time.time()

                if last_note_off_time and time.time() - last_note_off_time > 0.1:
                    return attempt_note, True

                time.sleep(0.01)
        finally:
            disable_raw_mode()

        return None, None

    def run(self):
        self.display_header("Écoute et Devine la note", "Mode Note Unique", "bright_blue")
        self.console.print("Écoutez la note jouée et essayez de la reproduire.")
        self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter la note, 'n' pour passer à la suivante.")

        while not self.exit_flag:
            self.clear_midi_buffer()
            # On choisit une note aléatoire entre C3 (48) et C5 (72)
            new_note = random.randint(48, 72)
            while new_note == self.last_note:
                new_note = random.randint(48, 72)
            self.current_note = new_note
            self.last_note = new_note

            self.console.print(f"\n[bold yellow]Lecture de la note...[/bold yellow]")
            play_chord(self.outport, [self.current_note])
            self.console.print("Jouez la note que vous venez d'entendre.")

            incorrect_attempts = 0
            skip_to_next = False

            while not self.exit_flag and not skip_to_next:
                attempt_note, ready = self.collect_note_listen_mode()

                if not ready:
                    if attempt_note is None:
                        if self.exit_flag:
                            return
                        else:
                            skip_to_next = True
                            break
                    break

                if attempt_note is None:
                    continue

                self.total_attempts += 1

                # Comparaison des classes de hauteur (note % 12)
                is_correct = (attempt_note % 12 == self.current_note % 12)

                if is_correct:
                    self.correct_count += 1
                    correct_note_name = get_note_name(self.current_note)
                    self.console.print(f"[bold green]Correct ! C'était bien un {correct_note_name}.[/bold green]")
                    time.sleep(1.5)
                    break
                else:
                    incorrect_attempts += 1
                    played_note_name = get_note_name(attempt_note)
                    self.console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué un {played_note_name}.")

                    if incorrect_attempts == 5:
                        correct_note_name = get_note_name(self.current_note)
                        hint = ""
                        if "#" in correct_note_name or "b" in correct_note_name:
                            hint = "C'est une note altérée (dièse ou bémol)."
                        else:
                            hint = "C'est une note naturelle (sans dièse ni bémol)."
                        self.console.print(f"Indice : {hint}")

            # Réinitialisation pour le prochain tour
            self.current_note = None
            if not self.exit_flag:
                clear_screen()
                self.display_header("Écoute et Devine la note", "Mode Note Unique", "bright_blue")
                self.console.print("Écoutez la note jouée et essayez de la reproduire.")
                self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter la note, 'n' pour passer à la suivante.")


        self.display_final_stats()

def single_note_mode(inport, outport):
    mode = SingleNoteMode(inport, outport)
    mode.run()
