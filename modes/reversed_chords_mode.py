# modes/reversed_chords_mode.py
import random
import time
from .chord_mode_base import ChordModeBase
from stats_manager import update_chord_error, update_chord_success
from data.chords import three_note_chords, all_chords
from music_theory import recognize_chord, are_chord_names_enharmonically_equivalent
from ui import get_colored_notes_string
from screen_handler import clear_screen
from keyboard_handler import wait_for_any_key

class ReversedChordsMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set):
        # The mode now accepts the user-selected chord set
        super().__init__(inport, outport, chord_set)
        self.mode_name = "Renversements d'accords (aléatoires)"
        self.exit_flag = False

    def check_chord_with_inversion(self, attempt_notes, target_chord_name, target_inversion):
        """
        Checks if the played notes match the target chord AND its specific inversion.
        """
        if not attempt_notes:
            return False, None, None

        try:
            recognized_name, recognized_inversion = recognize_chord(attempt_notes)

            # Check if the chord name is correct (including enharmonic equivalents)
            is_chord_correct = (recognized_name and
                                are_chord_names_enharmonically_equivalent(recognized_name, target_chord_name))

            # Check if the inversion is correct
            is_inversion_correct = (recognized_inversion == target_inversion)

            target_notes = self.chord_set.get(target_chord_name)
            is_note_count_correct = len(attempt_notes) == len(target_notes) if target_notes else False

            is_correct = is_chord_correct and is_inversion_correct and is_note_count_correct

            return is_correct, recognized_name, recognized_inversion
        except Exception as e:
            self.console.print(f"[bold red]Une erreur s'est produite lors de la reconnaissance : {e}[/bold red]")
            return False, None, None

    def run(self):
        """
        Main loop for the chord inversions mode.
        """
        self.display_header("Renversements d'accords", self.mode_name, "magenta")
        self.console.print("Jouez l'accord demandé dans toutes ses formes (renversements).")
        self.console.print("Appuyez sur 'q' pour quitter à tout moment.")
        time.sleep(2)

        last_chord_name = None

        while not self.exit_flag:
            clear_screen()
            self.display_header("Renversements d'accords", self.mode_name, "magenta")

            # --- Chord Selection ---
            chord_name = random.choice(list(self.chord_set.keys()))
            if len(self.chord_set) > 1:
                while chord_name == last_chord_name:
                    chord_name = random.choice(list(self.chord_set.keys()))
            last_chord_name = chord_name

            target_notes = self.chord_set[chord_name]
            num_notes = len(target_notes)

            # --- Determine inversions based on number of notes ---
            if num_notes == 3:
                inversions_to_play = ["position fondamentale", "1er renversement", "2ème renversement"]
            elif num_notes == 4:
                inversions_to_play = ["position fondamentale", "1er renversement", "2ème renversement", "3ème renversement"]
            else:
                self.console.print(f"L'accord [bold yellow]{chord_name}[/bold yellow] a {num_notes} notes et ne sera pas utilisé dans ce mode. Passage au suivant.")
                time.sleep(2)
                continue

            self.console.print(f"\nProchain accord : [bold yellow]{chord_name}[/bold yellow] ({num_notes} notes)")

            # --- Inversions Loop ---
            skip_to_next_chord = False
            for i, expected_inversion in enumerate(inversions_to_play):
                self.console.print(f"  ({i+1}/{num_notes}) Prêt à jouer [bold cyan]{expected_inversion}[/bold cyan]...")

                inversion_attempts = 0
                while not self.exit_flag:
                    # Get user input (MIDI notes)
                    attempt_notes, status = self.collect_user_input(collection_mode='chord')

                    if status == 'next':
                        skip_to_next_chord = True
                        break

                    if self.exit_flag: # User pressed 'q'
                        break

                    if not attempt_notes: # User pressed 'r'
                        continue

                    inversion_attempts += 1
                    self.session_total_attempts += 1

                    is_correct, rec_name, rec_inv = self.check_chord_with_inversion(
                        attempt_notes, chord_name, expected_inversion
                    )

                    # Display feedback
                    colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                    self.console.print(f"Notes jouées : [{colored_notes}]")

                    if is_correct:
                        update_chord_success(chord_name)
                        self.console.print(f"[bold green]Correct ! ({rec_name} - {rec_inv})[/bold green]\n")
                        if inversion_attempts == 1:
                            self.session_correct_count += 1
                        time.sleep(1.5)
                        break # Move to the next inversion
                    else:
                        update_chord_error(chord_name)
                        feedback = f"[bold red]Incorrect.[/bold red]"
                        if rec_name and are_chord_names_enharmonically_equivalent(rec_name, chord_name):
                             feedback += f" Bon accord ([bold yellow]{rec_name}[/bold yellow]), mais mauvais renversement."
                             feedback += f" Joué : [bold red]{rec_inv}[/bold red], Attendu : [bold green]{expected_inversion}[/bold green]."
                        elif rec_name:
                            feedback += f" Mauvais accord. Vous avez joué : [bold red]{rec_name}[/bold red]."
                        else:
                            feedback += " Accord non reconnu."

                        self.console.print(feedback)
                        self.console.print("Réessayez...")

                if self.exit_flag or skip_to_next_chord:
                    break # Exit the inversions loop

            if skip_to_next_chord:
                continue

            if not self.exit_flag:
                self.console.print(f"\n[bold green]Série de renversements pour [bold yellow]{chord_name}[/bold yellow] terminée ![/bold green]")
                choice = self.wait_for_end_choice()
                if choice == 'quit':
                    self.exit_flag = True
                # Pour 'repeat' ou 'continue', on passe simplement à l'accord suivant,
                # ce qui est le comportement par défaut de la boucle while.

        # --- End of session ---
        self.show_overall_stats_and_wait()

def reversed_chords_mode(inport, outport, chord_set):
    mode = ReversedChordsMode(inport, outport, chord_set)
    mode.run()
