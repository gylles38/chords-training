# modes/single_note_mode.py
import time
import random
from typing import Literal

from .chord_mode_base import ChordModeBase
from midi_handler import play_chord
from screen_handler import clear_screen
from music_theory import get_note_name
from keyboard_handler import wait_for_input, enable_raw_mode, disable_raw_mode
from stats_manager import get_note_errors, update_note_error, update_note_success


class SingleNoteMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set=None):
        super().__init__(inport, outport, chord_set)
        self.current_note = None
        self.last_note = None
        # Pool de notes C3 (48) à C5 (72)
        self.note_pool = list(range(48, 73))

    def _handle_repeat(self) -> Literal['repeat', False]:
        if self.current_note is not None:
            play_chord(self.outport, [self.current_note])
            return False
        return 'repeat'

    def select_weighted_note(self):
        note_errors = get_note_errors()
        weights = [1 + note_errors.get(get_note_name(n), 0) ** 2 for n in self.note_pool]

        new_note = random.choices(self.note_pool, weights=weights, k=1)[0]
        while new_note == self.last_note:
            new_note = random.choices(self.note_pool, weights=weights, k=1)[0]
        return new_note

    def collect_note_listen_mode(self):
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
                        if not notes_currently_on: # Première note jouée
                            self.session_stopwatch_start_time = self.session_stopwatch_start_time or time.time()
                        notes_currently_on.add(msg.note)
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

    def _display_top_note_errors(self):
        """Affiche les 3 notes avec le plus d'erreurs."""
        note_errors = get_note_errors()
        if not note_errors:
            return

        sorted_errors = sorted(note_errors.items(), key=lambda item: item[1], reverse=True)

        self.console.print("\n[bold]Notes à travailler :[/bold]")
        for note, count in sorted_errors[:3]:
            self.console.print(f"- [bold cyan]{note}[/bold cyan]: {count} erreur{'s' if count > 1 else ''}")

    def run(self):
        self.display_header("Écoute et Devine la note", "Mode Note Unique", "bright_blue")
        self.console.print("Écoutez la note jouée et essayez de la reproduire.")
        self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer à la suivante.")

        while not self.exit_flag:
            self.clear_midi_buffer()
            self.current_note = self.select_weighted_note()
            self.last_note = self.current_note
            correct_note_name = get_note_name(self.current_note)

            self.console.print(f"\n[bold yellow]Lecture de la note...[/bold yellow]")
            play_chord(self.outport, [self.current_note])
            self.console.print("Jouez la note que vous venez d'entendre.")

            first_attempt = True
            skip_to_next = False

            while not self.exit_flag and not skip_to_next:
                attempt_note, ready = self.collect_note_listen_mode()

                if not ready:
                    if self.exit_flag or (attempt_note is None and not self.exit_flag):
                        skip_to_next = True
                    continue

                if attempt_note is None:
                    continue

                self.session_total_attempts += 1
                is_correct = (attempt_note % 12 == self.current_note % 12)

                if is_correct:
                    if first_attempt:
                        self.session_correct_count += 1
                    update_note_success(correct_note_name)
                    self.console.print(f"[bold green]Correct ! C'était bien un {correct_note_name}.[/bold green]")
                    time.sleep(1.5)
                    break
                else:
                    first_attempt = False
                    update_note_error(correct_note_name)
                    played_note_name = get_note_name(attempt_note)
                    self.console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué un {played_note_name}.")

            self.session_total_count += 1
            self.current_note = None
            if not self.exit_flag:
                clear_screen()
                self.display_header("Écoute et Devine la note", "Mode Note Unique", "bright_blue")
                self.console.print("Écoutez la note jouée et essayez de la reproduire.")
                self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter la note, 'n' pour passer à la suivante.")

        # Afficher les stats spécifiques à ce mode, puis les stats générales
        self._display_top_note_errors()
        self.show_overall_stats_and_wait()


def single_note_mode(inport, outport):
    mode = SingleNoteMode(inport, outport)
    mode.run()
