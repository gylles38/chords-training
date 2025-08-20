# modes/listen_and_reveal_mode.py
import time
import random
from typing import Literal
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .chord_mode_base import ChordModeBase
from stats_manager import update_chord_error, update_chord_success
from midi_handler import play_chord
from screen_handler import clear_screen
from music_theory import get_note_name, get_chord_type_from_name
from keyboard_handler import enable_raw_mode, disable_raw_mode

class ListenAndRevealMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set):
        super().__init__(inport, outport, chord_set)
        self.last_chord_name = None

    def _handle_repeat(self) -> Literal['repeat', False]:
        if hasattr(self, "current_chord_notes") and self.current_chord_notes is not None:
            play_chord(self.outport, self.current_chord_notes)
            return False
        return 'repeat'

    def run(self):
        self.display_header("Écoute et Devine", "Mode Écoute et Devine", "orange3")
        self.console.print("Écoutez l'accord joué et essayez de le reproduire.")
        self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer au suivant.")

        with Live(console=self.console, screen=False, auto_refresh=False) as live:
            while not self.exit_flag:
                self.clear_midi_buffer()

                new_chord_name, new_chord_notes = random.choice(list(self.chord_set.items()))
                while new_chord_name == self.last_chord_name:
                    new_chord_name, new_chord_notes = random.choice(list(self.chord_set.items()))

                self.current_chord_name = new_chord_name
                # The "correct" answer is always based on the root position notes
                self.current_chord_notes = new_chord_notes
                self.last_chord_name = new_chord_name

                # --- NEW: Play a random inversion ---
                # Generate all possible inversions for the chord
                all_inversions = self._get_inversions(new_chord_notes)
                # Randomly select one of the inversions to play
                notes_to_play = random.choice(all_inversions) if all_inversions else new_chord_notes

                live.update(Panel("Lecture de l'accord...", title="Action", border_style="yellow"), refresh=True)
                play_chord(self.outport, notes_to_play)

                incorrect_attempts = 0
                first_attempt = True
                feedback_text = Text()

                while not self.exit_flag:
                    prompt_text = Text("Jouez l'accord que vous venez d'entendre.")
                    if feedback_text.plain:
                        prompt_text.append("\n\n")
                        prompt_text.append(feedback_text)
                    live.update(Panel(prompt_text, title="Action", border_style="green"), refresh=True)

                    enable_raw_mode()
                    attempt_notes, status = self._collect_input_logic(collection_mode='chord')
                    disable_raw_mode()

                    if status == 'next':
                        break
                    if status is not True:
                        if self.exit_flag: break
                        else: continue # This will now only handle 'repeat'

                    self.session_total_attempts += 1
                    is_correct, recognized_name, recognized_inversion = self.check_chord(
                        attempt_notes, self.current_chord_name, self.current_chord_notes
                    )

                    if is_correct:
                        if first_attempt: self.session_correct_count += 1
                        update_chord_success(self.current_chord_name)
                        played_chord_info = f"{recognized_name} ({recognized_inversion})" if recognized_name else self.current_chord_name
                        success_feedback = Text.from_markup(f"[bold green]Correct ! Vous avez joué {played_chord_info}.[/bold green]")
                        live.update(Panel(success_feedback, title="Résultat", border_style="green"), refresh=True)
                        time.sleep(1.5)
                        break
                    else:
                        first_attempt = False
                        update_chord_error(self.current_chord_name)
                        incorrect_attempts += 1

                        played_chord_info = f"{recognized_name} ({recognized_inversion})" if recognized_name else "Accord non reconnu"
                        feedback_text = Text.from_markup(f"[bold red]Incorrect.[/bold red] Vous avez joué : {played_chord_info}")

                        if incorrect_attempts >= 3:
                            tonic_name = get_note_name(sorted(list(self.current_chord_notes))[0])
                            feedback_text.append(Text.from_markup(f"\nIndice : La tonique est [bold cyan]{tonic_name}[/bold cyan]."))

                        if incorrect_attempts >= 7:
                            revealed_type = get_chord_type_from_name(self.current_chord_name)
                            feedback_text.append(Text.from_markup(f"\n[bold magenta]La réponse était : {self.current_chord_name}[/bold magenta]"))
                            live.update(Panel(feedback_text, title="Réponse", border_style="magenta"), refresh=True)
                            time.sleep(2.5)
                            break

                self.session_total_count += 1
                if self.exit_flag: break

                self.current_chord_notes = None
                self.current_chord_name = None

        clear_screen()
        self.display_header("Écoute et Devine", "Mode Écoute et Devine", "orange3")
        self.console.print("Fin de la session.")
        self.show_overall_stats_and_wait()


def listen_and_reveal_mode(inport, outport, chord_set):
    mode = ListenAndRevealMode(inport, outport, chord_set)
    mode.run()