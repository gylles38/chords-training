# modes/listen_and_reveal_mode.py
import time
import random
from rich.prompt import Prompt

from .chord_mode_base import ChordModeBase

from midi_handler import play_chord
from screen_handler import clear_screen
from music_theory import get_note_name, get_chord_type_from_name


class ListenAndRevealMode(ChordModeBase):
    def handle_keyboard_input(self, char):
        # Quitter si 'q'
        if super().handle_keyboard_input(char):
            return True
        # Répéter uniquement si un accord est en cours — NE PAS retourner True pour 'r'
        if char and char.lower() == 'r' and getattr(self, "current_chord_notes", None) is not None:
            play_chord(self.outport, self.current_chord_notes)
            # important : retourner False pour ne pas interrompre collect_notes()
            return False
        return False
    
    def run(self):
        # Affichage du header et des instructions une seule fois
        self.display_header("Écoute et Devine", "Mode Écoute et Devine", "orange3")
        self.console.print("Écoutez l'accord joué et essayez de le reproduire.")
        self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter l'accord.")

        while not self.exit_flag:
            self.clear_midi_buffer()
            # Tirage d'un accord pour ce cycle
            self.current_chord_name, self.current_chord_notes = random.choice(list(self.chord_set.items()))
            self.console.print(f"\n[bold yellow]Lecture de l'accord...[/bold yellow]")
            play_chord(self.outport, self.current_chord_notes)
            self.console.print("Jouez l'accord que vous venez d'entendre.")

            incorrect_attempts = 0

            while not self.exit_flag:
                attempt_notes, ready = self.collect_notes()
                if not ready:
                    break

                self.total_attempts += 1
                is_correct, recognized_name, recognized_inversion = self.check_chord(
                    attempt_notes, self.current_chord_name, self.current_chord_notes
                )

                if is_correct:
                    self.display_feedback(True, attempt_notes, self.current_chord_notes, recognized_name, recognized_inversion)
                    self.correct_count += 1
                    time.sleep(1.5)
                    break
                else:
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
                        Prompt.ask("\nAppuyez sur Entrée pour continuer...", console=self.console)
                        break

            # Passer à l'accord suivant : effacer l'écran et réafficher les instructions minimales
            clear_screen()
            self.display_header("Écoute et Devine", "Mode Écoute et Devine", "orange3")
            self.console.print("Écoutez l'accord joué et essayez de le reproduire.")
            self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter l'accord.")

            # Accord terminé → on supprime la référence pour éviter répétition hors cycle
            self.current_chord_notes = None
            self.current_chord_name = None

        self.display_final_stats()


def listen_and_reveal_mode(inport, outport, chord_set):
    mode = ListenAndRevealMode(inport, outport, chord_set)
    mode.run()