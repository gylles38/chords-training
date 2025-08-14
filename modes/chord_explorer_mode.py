# modes/chord_explorer_mode.py
from rich.text import Text
from rich.panel import Panel
from rich.prompt import Prompt

from .chord_mode_base import ChordModeBase
from data.chords import all_chords, chord_aliases
from music_theory import get_note_name
from midi_handler import play_chord


class ChordExplorerMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set):
        super().__init__(inport, outport, chord_set)

    def run(self):
        # En-tête via la classe mère
        self.display_header("Dictionnaire d'accords", "Mode Explorateur d'Accords", "bright_blue")
        self.console.print("Entrez un nom d'accord pour voir ses notes et l'entendre.")
        self.console.print("Exemples : [cyan]C, F#m, Gm7, Bb, Ddim[/cyan]")

        while not self.exit_flag:
            try:
                user_input = Prompt.ask("\n[prompt.label]Accord à trouver (ou 'q' pour quitter)[/prompt.label]")
                if user_input is None:
                    continue
                if user_input.lower() == 'q':
                    self.exit_flag = True
                    break

                lookup_key = user_input.lower().replace(" ", "")
                full_chord_name = chord_aliases.get(lookup_key)

                if full_chord_name and full_chord_name in all_chords:
                    chord_notes_midi = all_chords[full_chord_name]
                    sorted_notes_midi = sorted(list(chord_notes_midi))
                    note_names = [get_note_name(n) for n in sorted_notes_midi]
                    notes_str = ", ".join(note_names)

                    self.console.print(f"L'accord [bold green]{full_chord_name}[/bold green] est composé des notes : [bold yellow]{notes_str}[/bold yellow]")
                    self.console.print("Lecture de l'accord...")
                    play_chord(self.outport, chord_notes_midi, duration=1.2)
                else:
                    self.console.print(f"[bold red]Accord '{user_input}' non reconnu.[/bold red] Veuillez réessayer.")
            except Exception as e:
                self.console.print(f"[bold red]Une erreur est survenue : {e}[/bold red]")

        self.console.print("\nRetour au menu principal.")


def chord_explorer_mode(outport):
    """Wrapper pour compatibilité avec l'appel existant dans chords-training.py"""
    mode = ChordExplorerMode(None, outport, all_chords)
    mode.run()