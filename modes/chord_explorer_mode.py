# modes/chord_explorer_mode.py
from rich.text import Text
from rich.panel import Panel
from rich.prompt import Prompt

from .chord_mode_base import ChordModeBase
from data.chords import all_chords, chord_aliases
from music_theory import get_note_name
from midi_handler import play_chord
from messages import ChordExplorerMode as ChordExplorerMessages

class ChordExplorerMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set):
        super().__init__(inport, outport, chord_set)

    def run(self):
        last_message = None
        last_chord_notes = None
        last_chord_name = None
        while not self.exit_flag:
            # Rafraîchit entièrement l'écran pour éviter le défilement
            self.display_header(ChordExplorerMessages.TITLE, ChordExplorerMessages.TITLE, "bright_blue")
            self.console.print(ChordExplorerMessages.SUBTITLE)
            self.console.print("Exemples : [cyan]C, F#m, Gm7, Bb, Ddim[/cyan]")
            if last_message:
                self.console.print("")
                self.console.print(last_message)

            try:
                user_input = Prompt.ask(f"\n[prompt.label]{ChordExplorerMessages.PROMPT} (ou 'q' pour quitter)[/prompt.label]")
                if user_input is None:
                    continue

                # Quitter
                if user_input.lower() == 'q':
                    self.exit_flag = True
                    break

                # Répéter la lecture du dernier accord
                if user_input.lower() == 'r' and last_chord_notes:
                    play_chord(self.outport, last_chord_notes, duration=1.2)
                    continue

                # Entrée vide → rejoue le dernier accord si disponible
                if user_input.strip() == '' and last_chord_notes:
                    play_chord(self.outport, last_chord_notes, duration=1.2)
                    continue

                lookup_key = user_input.lower().replace(" ", "")
                full_chord_name = chord_aliases.get(lookup_key)

                if full_chord_name and full_chord_name in all_chords:
                    chord_notes_midi = all_chords[full_chord_name]
                    sorted_notes_midi = sorted(list(chord_notes_midi))
                    note_names = [get_note_name(n) for n in sorted_notes_midi]
                    notes_str = ", ".join(note_names)

                    last_message = ChordExplorerMessages.PLAYING_CHORD.format(
                        chord_name=full_chord_name,
                        notes=notes_str
                    )
                    last_chord_notes = chord_notes_midi
                    last_chord_name = full_chord_name
                    play_chord(self.outport, chord_notes_midi, duration=1.2)
                else:
                    last_message = ChordExplorerMessages.INVALID_CHORD
            except Exception as e:
                last_message = f"[bold red]Une erreur est survenue : {e}[/bold red]"

        self.console.print(f"\n{ChordExplorerMessages.QUITTING}")


def chord_explorer_mode(outport):
    """Wrapper pour compatibilité avec l'appel existant dans chords-training.py"""
    mode = ChordExplorerMode(None, outport, all_chords)
    mode.run()