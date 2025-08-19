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
    def __init__(self, inport, outport, chord_set=None):
        super().__init__(inport, outport, chord_set)
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
        if self.current_scale_notes:
            self.console.print(f"\nRépétition de la gamme [bold cyan]{self.current_scale_name}[/bold cyan]")
            play_note_sequence(self.outport, self.current_scale_notes)
            self.console.print("À vous de jouer !")
        return False # We handled it, don't bubble up.

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

    def run(self):
        self.display_header("Les Gammes", "Mode Gammes", "green")
        self.console.print("Le nom d'une gamme va s'afficher. Jouez la gamme correspondante, note par note.")
        self.console.print("Appuyez sur 'q' pour quitter, 'r' pour ré-écouter la gamme, 'n' pour passer à la suivante.")

        while not self.exit_flag:
            self.clear_midi_buffer()

            selected_scale = self.select_weighted_scale()
            self.current_scale_name = selected_scale['display_name']
            self.last_scale_name = self.current_scale_name

            self.current_scale_notes = generate_scale(selected_scale['root_note_midi'], selected_scale['scale_type_key'])

            if not self.current_scale_notes:
                self.console.print(f"[bold red]Erreur: Impossible de générer la gamme {self.current_scale_name}[/bold red]")
                time.sleep(2)
                continue

            self.console.print(f"\nÉcoutez la gamme de: [bold yellow]{self.current_scale_name}[/bold yellow]")
            play_note_sequence(self.outport, self.current_scale_notes)
            self.console.print("À vous de jouer !")

            first_attempt = True
            skip_to_next = False
            played_scale = []

            # Loop to collect each note of the scale
            for i in range(len(self.current_scale_notes)):
                self.console.print(f"En attente de la note {i+1}/{len(self.current_scale_notes)}...")

                attempt_note, status = self.collect_user_input(collection_mode='single', release_timeout=0.1)

                if status == 'next':
                    skip_to_next = True
                    break

                if status is not True:
                    skip_to_next = True # Exit the note collection loop because 'q' was pressed
                    break

                if attempt_note is None:
                    continue

                played_scale.append(attempt_note)

            if skip_to_next:
                if not self.exit_flag:
                    clear_screen()
                    self.display_header("Les Gammes", "Mode Gammes", "green")
                    self.console.print("Le nom d'une gamme va s'afficher. Jouez la gamme correspondante, note par note.")
                    self.console.print("Appuyez sur 'q' pour quitter, 'r' pour ré-écouter la gamme, 'n' pour passer à la suivante.")
                continue

            # Check the played scale
            is_correct = (played_scale == self.current_scale_notes)

            self.session_total_attempts += 1

            if is_correct:
                if first_attempt:
                    self.session_correct_count += 1
                update_scale_success(self.current_scale_name)
                self.console.print(f"[bold green]Correct ! C'était bien la gamme de {self.current_scale_name}.[/bold green]")
                time.sleep(1.5)
            else:
                first_attempt = False
                update_scale_error(self.current_scale_name)
                played_note_names = [get_note_name(n) for n in played_scale] if played_scale else ["Rien"]
                correct_note_names = [get_note_name(n) for n in self.current_scale_notes]
                self.console.print(f"[bold red]Incorrect.[/bold red]")
                self.console.print(f"Attendu: {' - '.join(correct_note_names)}")
                self.console.print(f"Joué:    {' - '.join(played_note_names)}")
                time.sleep(3)

            self.session_total_count += 1
            self.current_scale_name = None
            self.current_scale_notes = None

            if not self.exit_flag:
                clear_screen()
                self.display_header("Les Gammes", "Mode Gammes", "green")
                self.console.print("Le nom d'une gamme va s'afficher. Jouez la gamme correspondante, note par note.")
                self.console.print("Appuyez sur 'q' pour quitter, 'r' pour ré-écouter la gamme, 'n' pour passer à la suivante.")

        self.show_overall_stats_and_wait(extra_stats_callback=self._display_top_scale_errors)

def progression_scale_mode(inport, outport):
    """Entry point for the Progression Scale Mode."""
    mode = ProgressionScaleMode(inport, outport)
    mode.run()
