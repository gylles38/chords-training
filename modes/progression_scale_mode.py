# modes/progression_scale_mode.py
import time
import random
from typing import Literal

from .chord_mode_base import ChordModeBase
from midi_handler import play_note_sequence
from screen_handler import clear_screen
from music_theory import get_note_name, generate_scale
from stats_manager import get_scale_errors, update_scale_error, update_scale_success

# MIDI note values for roots
NOTE_MIDI_MAP = {
    'Do': 60, 'Do#': 61, 'Re': 62, 'Re#': 63, 'Mi': 64, 'Fa': 65,
    'Fa#': 66, 'Sol': 67, 'Sol#': 68, 'La': 69, 'La#': 70, 'Si': 71
}

# Scale types mapping internal name to display name
SCALE_TYPES = {
    'major': 'Majeur',
    'natural_minor': 'Mineur Naturel',
    'harmonic_minor': 'Mineur Harmonique',
    'melodic_minor_asc': 'Mineur Mélodique Ascendant',
    'melodic_minor_desc': 'Mineur Mélodique Descendant',
}

class ProgressionScaleMode(ChordModeBase):
    def __init__(self, inport, outport, play_progression_before_start, chord_set=None):
        super().__init__(inport, outport, chord_set)
        self.play_progression_before_start = play_progression_before_start
        self.current_scale_name = None
        self.current_scale_notes = None
        self.last_scale_name = None

        # Define the pool of scales to practice
        self.scale_pool = []
        for note_name, midi_val in NOTE_MIDI_MAP.items():
            for scale_type_key, scale_type_name in SCALE_TYPES.items():
                self.scale_pool.append({
                    'root_note_name': note_name,
                    'root_note_midi': midi_val,
                    'scale_type_key': scale_type_key,
                    'display_name': f"{note_name} {scale_type_name}"
                })

    def _handle_repeat(self) -> Literal['repeat', False]:
        # The repeat logic is now handled in the run loop,
        # so this method just needs to signal that a repeat was requested.
        return 'repeat'

    def select_weighted_scale(self):
        scale_errors = get_scale_errors()
        weights = [1 + scale_errors.get(s['display_name'], 0) ** 2 for s in self.scale_pool]

        selected_scale = random.choices(self.scale_pool, weights=weights, k=1)[0]
        while selected_scale['display_name'] == self.last_scale_name:
            selected_scale = random.choices(self.scale_pool, weights=weights, k=1)[0]

        return selected_scale

    def _display_top_scale_errors(self):
        scale_errors = get_scale_errors()
        if not scale_errors:
            return

        sorted_errors = sorted(scale_errors.items(), key=lambda item: item[1], reverse=True)

        self.console.print("\n[bold]Gammes à travailler :[/bold]")
        for scale_name, count in sorted_errors[:5]: # Show top 5
            self.console.print(f"- [bold cyan]{scale_name}[/bold cyan]: {count} erreur{'s' if count > 1 else ''}")

    def _wait_for_end_choice(self):
        """Waits for the user to press 'n', 'r', or 'q' after a scale is played."""
        from keyboard_handler import wait_for_input, enable_raw_mode, disable_raw_mode
        self.console.print("\nAppuyez sur [bold]n[/bold] pour la gamme suivante, [bold]r[/bold] pour répéter, ou [bold]q[/bold] pour quitter.")

        enable_raw_mode()
        try:
            while True:
                char = wait_for_input(timeout=0.1)
                if char:
                    if char.lower() == 'n':
                        return 'next'
                    if char.lower() == 'r':
                        return 'repeat'
                    if char.lower() == 'q':
                        self.exit_flag = True
                        return 'quit'
        finally:
            disable_raw_mode()

    def run(self):
        self.display_header("Les Gammes", "Mode Gammes", "green")
        self.console.print("Le nom d'une gamme va s'afficher. Jouez la note attendue pour avancer.")
        self.console.print("Appuyez sur 'q' pour quitter, 'r' pour ré-écouter la gamme, 'n' pour passer à la suivante.")

        select_new_scale = True
        while not self.exit_flag:
            self.clear_midi_buffer()

            if select_new_scale:
                selected_scale = self.select_weighted_scale()
                self.current_scale_name = selected_scale['display_name']
                self.last_scale_name = self.current_scale_name
                self.current_scale_notes = generate_scale(selected_scale['root_note_midi'], selected_scale['scale_type_key'])

            if not self.current_scale_notes:
                self.console.print(f"[bold red]Erreur: Impossible de générer la gamme {self.current_scale_name}[/bold red]")
                time.sleep(2)
                select_new_scale = True
                continue

            # --- Start of a scale attempt ---
            clear_screen()
            self.display_header("Les Gammes", "Mode Gammes", "green")
            self.console.print("Le nom d'une gamme va s'afficher. Jouez la note attendue pour avancer.")
            self.console.print("Appuyez sur 'q' pour quitter, 'r' pour ré-écouter la gamme, 'n' pour passer à la suivante.")
            self.console.print(f"\nÉcoutez la gamme de: [bold yellow]{self.current_scale_name}[/bold yellow]")

            if self.play_progression_before_start != 'PLAY_ONLY':
                note_names = [get_note_name(n) for n in self.current_scale_notes]
                scale_display = " -> ".join(note_names)
                self.console.print(f"[cyan]{scale_display}[/cyan]")

            if self.play_progression_before_start != 'NONE':
                play_note_sequence(self.outport, self.current_scale_notes)

            self.console.print("À vous de jouer !")

            scale_was_perfect = True
            skip_to_next = False
            restart_scale_attempt = False

            i = 0
            while i < len(self.current_scale_notes):
                correct_note_for_step = self.current_scale_notes[i]

                prompt = f"Jouez la note {i+1}/{len(self.current_scale_notes)}"
                if self.play_progression_before_start != 'PLAY_ONLY':
                    prompt += f" ({get_note_name(correct_note_for_step)})"
                prompt += "..."
                self.console.print(prompt)

                while True: # Inner loop to wait for the correct note
                    attempt_note, status = self.collect_user_input(collection_mode='single', release_timeout=0.1)

                    if status == 'repeat':
                        restart_scale_attempt = True
                        break

                    if status == 'next':
                        skip_to_next = True
                        break

                    if status is not True: # 'q' or other issue
                        skip_to_next = True
                        break

                    if attempt_note is None:
                        continue

                    if (attempt_note % 12) == (correct_note_for_step % 12):
                        self.console.print(f"[green]Correct ![/green]")
                        time.sleep(0.5)
                        break # Correct note played, exit inner loop
                    else:
                        scale_was_perfect = False
                        self.console.print(f"[red]Incorrect. Vous avez joué {get_note_name(attempt_note)}. Réessayez.[/red]")

                if skip_to_next or restart_scale_attempt:
                    break

                i += 1

            if restart_scale_attempt:
                select_new_scale = False # To repeat the same scale
                continue

            # --- End of scale playing ---
            self.session_total_count += 1
            choice = 'next' # Default action unless 'n' or 'q' was pressed mid-scale

            if skip_to_next and self.exit_flag:
                choice = 'quit'
            elif skip_to_next:
                choice = 'next'
            else:
                # This block runs only if the user completed the whole scale
                self.session_total_attempts += 1 # An attempt is a full, completed scale
                if scale_was_perfect:
                    self.session_correct_count += 1
                    update_scale_success(self.current_scale_name)
                    self.console.print(f"\n[bold green]Parfait ! Gamme de {self.current_scale_name} terminée.[/bold green]")
                else:
                    update_scale_error(self.current_scale_name)
                    self.console.print(f"\n[bold yellow]Gamme de {self.current_scale_name} terminée.[/bold yellow]")

                choice = self._wait_for_end_choice()

            if choice == 'quit':
                break

            if choice == 'repeat':
                select_new_scale = False
            elif choice == 'next':
                select_new_scale = True

        self.show_overall_stats_and_wait(extra_stats_callback=self._display_top_scale_errors)

def progression_scale_mode(inport, outport, play_progression_before_start):
    """Entry point for the Progression Scale Mode."""
    mode = ProgressionScaleMode(inport, outport, play_progression_before_start)
    mode.run()
