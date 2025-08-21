# modes/reverse_chord_mode.py
import time
from rich.panel import Panel
from rich.live import Live

from .chord_mode_base import ChordModeBase
from music_theory import recognize_chord, get_note_name
from keyboard_handler import enable_raw_mode, disable_raw_mode
from data.chords import enharmonic_map
from music_theory import recognize_chord

class ReverseChordMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set):
        super().__init__(inport, outport, chord_set)

    def run(self):
        def pre_display():
            self.console.print("Jouez un accord sur votre clavier MIDI.")
            self.console.print("Appuyez sur 'q' pour quitter.")
            self.console.print(
                "\nCe mode reconnaît les accords à 3 ou 4 notes en position fondamentale "
                "ainsi qu'en 1er et 2ème (et 3ème) renversement, quelle que soit l'octave."
            )
            self.console.print("---")

        # Affiche l'entête une première fois
        self.display_header(
            "Reconnaissance d'accords",
            "Mode Reconnaissance d'accords (Tous les accords)",
            "cyan",
        )
        pre_display()

        enable_raw_mode()
        try:
            with Live(console=self.console, screen=False, auto_refresh=False) as live:
                while not self.exit_flag:
                    self.clear_midi_buffer()
                    attempt_notes, status = self._collect_input_logic(collection_mode='chord')
                    if status == 'next' or status == 'repeat':
                        continue
                    if status is not True: # Now only catches 'quit' (False)
                        break

                    # Met à jour l'affichage avec le résultat
                    recognized_name, recognized_inversion = recognize_chord(attempt_notes)

                    # Logique d'affichage locale pour ce mode
                    from ui import get_colored_notes_string
                    notes_str = get_colored_notes_string(attempt_notes, attempt_notes)
                    self.console.print(f"Notes jouées : [{notes_str}]")

                    if recognized_name:
                        inversion_text = f" ({recognized_inversion})" if recognized_inversion and recognized_inversion != "position fondamentale" else ""
                        self.console.print(f"[bold green]Accord reconnu : {recognized_name}{inversion_text}.[/bold green]")
                    else:
                        self.console.print("[bold red]Accord non reconnu ![/bold red]")

        finally:
            disable_raw_mode()

    def display_recognition_stats(self):
        pass


def reverse_chord_mode(inport, outport, chord_set):
    """Point d'entrée pour le mode reconnaissance d'accords"""
    mode = ReverseChordMode(inport, outport, chord_set)
    mode.run()
