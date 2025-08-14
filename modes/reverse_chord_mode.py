# modes/reverse_chord_mode.py
import time
from .chord_mode_base import ChordModeBase
from music_theory import recognize_chord, get_note_name
from keyboard_handler import wait_for_input, enable_raw_mode, disable_raw_mode
from data.chords import enharmonic_map

class ReverseChordMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set):
        super().__init__(inport, outport, chord_set)

    def recognize_and_display_chord(self, attempt_notes):
        """Reconnaît et affiche l'accord joué"""
        if len(attempt_notes) > 1:
            chord_name, inversion_label = recognize_chord(attempt_notes)
            
            if chord_name:
                enharmonic_name = enharmonic_map.get(chord_name)
                if enharmonic_name:
                    self.console.print(
                        f"Accord reconnu : [bold green]{chord_name}[/bold green] "
                        f"ou [bold green]{enharmonic_name}[/bold green] ({inversion_label})"
                    )
                else:
                    self.console.print(f"Accord reconnu : [bold green]{chord_name}[/bold green] ({inversion_label})")
            else:
                colored_string = ", ".join(
                    [f"[bold red]{get_note_name(n)}[/bold red]" for n in sorted(list(attempt_notes))]
                )
                self.console.print(f"[bold red]Accord non reconnu.[/bold red] Notes jouées : [{colored_string}]")
        else:
            self.console.print("[bold yellow]Veuillez jouer au moins 3 notes pour former un accord.[/bold yellow]")

    def run(self):
        def pre_display():
            self.console.print("Jouez un accord sur votre clavier MIDI.")
            self.console.print("Appuyez sur 'q' pour quitter.")
            self.console.print("\nCe mode reconnaît les accords à 3 ou 4 notes en position fondamentale "
                               "ainsi qu'en 1er et 2ème (et 3ème) renversement, quelle que soit l'octave.")
            self.console.print("---")

        self.display_header("Reconnaissance d'accords", "Mode Reconnaissance d'accords (Tous les accords)", "cyan")
        pre_display()

        # Cache le curseur
        print("\033[?25l", end="", flush=True)

        enable_raw_mode()
        try:
            while not self.exit_flag:
                self.clear_midi_buffer()
                attempt_notes, ready = self.collect_notes()
                if not ready:
                    break

                # Retour à gauche + effacement ligne
                print("\r\033[K", end="")
                self.recognize_and_display_chord(attempt_notes)

        finally:
            disable_raw_mode()
            # Réaffiche le curseur
            print("\033[?25h", end="", flush=True)
            
    def display_recognition_stats(self):
        pass

def reverse_chord_mode(inport, outport, chord_set):
    """Point d'entrée pour le mode reconnaissance d'accords"""
    mode = ReverseChordMode(inport, outport, chord_set)
    mode.run()
