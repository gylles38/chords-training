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
                    if status is not True:
                        break

                    # Met à jour l'affichage avec le résultat
                    recognized_name, recognized_inversion = recognize_chord(attempt_notes)  
                                      
                    self.display_feedback(True, attempt_notes, attempt_notes, recognized_name, recognized_inversion, True)
                    #live.update(Panel, refresh=True)

        finally:
            disable_raw_mode()

    def display_recognition_stats(self):
        pass


def reverse_chord_mode(inport, outport, chord_set):
    """Point d'entrée pour le mode reconnaissance d'accords"""
    mode = ReverseChordMode(inport, outport, chord_set)
    mode.run()
