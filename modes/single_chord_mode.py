# modes/single_chord_mode.py
import time
import random
from .chord_mode_base import ChordModeBase

from keyboard_handler import wait_for_input

class SingleChordMode(ChordModeBase):
    def run(self):
        # Affichage du header et des instructions une seule fois
        self.display_header("Accords Simples", "Mode Accords Simples", "yellow")
        self.console.print("Jouez l'accord affiché. Appuyez sur 'q' pour quitter.")

        last_chord_name = None
        while not self.exit_flag:
            self.clear_midi_buffer()

            # Choisir un nouvel accord différent du précédent
            chord_name, chord_notes = random.choice(list(self.chord_set.items()))
            while chord_name == last_chord_name:
                chord_name, chord_notes = random.choice(list(self.chord_set.items()))
            last_chord_name = chord_name

            # Effacer l'écran pour le nouvel accord
           # clear_screen()
            self.display_header("Accords Simples", "Mode Accords Simples", "yellow")
            self.console.print("Jouez l'accord affiché. Appuyez sur 'q' pour quitter.")
            self.console.print(f"\nJouez : [bold bright_yellow]{chord_name}[/bold bright_yellow]")

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

                # Un accord a été joué et toutes les notes ont été relâchées
                if not notes_currently_on and attempt_notes:
                    self.total_attempts += 1
                    is_correct, recognized_name, recognized_inversion = self.check_chord(
                        attempt_notes, chord_name, chord_notes
                    )

                    if is_correct:
                        self.display_feedback(True, attempt_notes, chord_notes, recognized_name, recognized_inversion)
                        self.correct_count += 1
                        time.sleep(2)  # Pause avant le prochain accord
                        break
                    else:
                        self.display_feedback(False, attempt_notes, chord_notes, recognized_name, recognized_inversion)
                        attempt_notes.clear()  # Réinitialiser pour le prochain essai

                time.sleep(0.01)

        self.display_final_stats()

def single_chord_mode(inport, outport, chord_set):
    mode = SingleChordMode(inport, outport, chord_set)
    mode.run()