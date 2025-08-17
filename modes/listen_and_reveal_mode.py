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
            try:
                enable_raw_mode()
                while not self.exit_flag:
                    self.clear_midi_buffer()

                    new_chord_name, new_chord_notes = random.choice(list(self.chord_set.items()))
                    while new_chord_name == self.last_chord_name:
                        new_chord_name, new_chord_notes = random.choice(list(self.chord_set.items()))

                    self.current_chord_name = new_chord_name
                    self.current_chord_notes = new_chord_notes
                    self.last_chord_name = new_chord_name

                    live.update(Panel("Lecture de l'accord...", title="Action", border_style="yellow"), refresh=True)
                    play_chord(self.outport, self.current_chord_notes)

                    incorrect_attempts = 0
                    first_attempt = True

                    main_display_text = "Jouez l'accord que vous venez d'entendre."
                    live.update(Panel(main_display_text, title="Action", border_style="green"), refresh=True)

                    while not self.exit_flag:
                        attempt_notes, ready = self.collect_notes()

                        if attempt_notes is None and ready is None:
                            if self.exit_flag: break
                            else: break

                        if not ready: continue

                        self.session_total_attempts += 1
                        is_correct, recognized_name, recognized_inversion = self.check_chord(
                            attempt_notes, self.current_chord_name, self.current_chord_notes
                        )

                        if is_correct:
                            if first_attempt: self.session_correct_count += 1
                            update_chord_success(self.current_chord_name)

                            feedback_text = Text.from_markup(f"[bold green]Correct ! C'était bien {self.current_chord_name}.[/bold green]")
                            live.update(Panel(feedback_text, title="Résultat", border_style="green"), refresh=True)
                            time.sleep(1.5)
                            break
                        else:
                            first_attempt = False
                            update_chord_error(self.current_chord_name)
                            incorrect_attempts += 1

                            feedback_text = Text.from_markup(f"[bold red]Incorrect.[/bold red] Vous avez joué : {recognized_name or 'Accord non reconnu'}")

                            if incorrect_attempts >= 3:
                                tonic_name = get_note_name(sorted(list(self.current_chord_notes))[0])
                                feedback_text.append(f"\nIndice : La tonique est [bold cyan]{tonic_name}[/bold cyan].")

                            live.update(Panel(feedback_text, title="Résultat", border_style="red"), refresh=True)
                            time.sleep(2)

                            if incorrect_attempts >= 7:
                                revealed_type = get_chord_type_from_name(self.current_chord_name)
                                final_text = Text.from_markup(f"Indice : C'est un accord de type [bold yellow]{revealed_type}[/bold yellow].\n[bold magenta]La réponse était : {self.current_chord_name}[/bold magenta]")
                                live.update(Panel(final_text, title="Réponse", border_style="magenta"), refresh=True)
                                time.sleep(2.5)
                                break

                            live.update(Panel(main_display_text, title="Action", border_style="green"), refresh=True)

                    self.session_total_count += 1
                    if self.exit_flag:
                        break

                    self.current_chord_notes = None
                    self.current_chord_name = None

                    # Instead of clearing the screen, we just go to the next loop iteration
                    # where the live display will be updated with the new chord.
            finally:
                disable_raw_mode()

        # Final cleanup before showing stats
        disable_raw_mode()
        clear_screen()
        self.display_header("Écoute et Devine", "Mode Écoute et Devine", "orange3")
        self.console.print("Fin de la session.")
        self.show_overall_stats_and_wait()


def listen_and_reveal_mode(inport, outport, chord_set):
    mode = ListenAndRevealMode(inport, outport, chord_set)
    mode.run()