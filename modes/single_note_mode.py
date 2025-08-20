# modes/single_note_mode.py
import time
import random
from typing import Literal

from .chord_mode_base import ChordModeBase
from midi_handler import play_chord
from screen_handler import clear_screen
from music_theory import get_note_name
from keyboard_handler import wait_for_input
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
        self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter la note, 'n' pour passer à la suivante.")

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
                attempt_note, status = self.collect_user_input(collection_mode='single', release_timeout=0.1)

                if status == 'next':
                    skip_to_next = True
                    continue

                if status is not True:
                    # This handles exit_flag being set (status=False) or other issues.
                    # The main loop condition `while not self.exit_flag` will handle the exit.
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

        # Utiliser la méthode de la classe de base pour des stats cohérentes
        self.show_overall_stats_and_wait(extra_stats_callback=self._display_top_note_errors)


def single_note_mode(inport, outport):
    mode = SingleNoteMode(inport, outport)
    mode.run()
