# modes/reverse_chord_mode.py
import time
from rich.panel import Panel
from rich.live import Live

from .chord_mode_base import ChordModeBase
from music_theory import recognize_chord, get_note_name
from keyboard_handler import enable_raw_mode, disable_raw_mode
from data.chords import enharmonic_map


class ReverseChordMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set):
        super().__init__(inport, outport, chord_set)

    def _build_result_panel(self, attempt_notes):
        """Construit le panneau d'affichage du résultat."""
        if len(attempt_notes) > 1:
            chord_name, inversion_label = recognize_chord(attempt_notes)
            if chord_name:
                enharmonic_name = enharmonic_map.get(chord_name)
                if enharmonic_name:
                    text = (
                        f"[bold green]{chord_name}[/bold green] "
                        f"ou [bold green]{enharmonic_name}[/bold green] "
                        f"({inversion_label})"
                    )
                else:
                    text = f"[bold green]{chord_name}[/bold green] ({inversion_label})"
            else:
                colored_notes = ", ".join(
                    f"[bold red]{get_note_name(n)}[/bold red]" for n in sorted(attempt_notes)
                )
                text = (
                    f"[bold red]Accord non reconnu.[/bold red] "
                    f"Notes jouées : {colored_notes}"
                )
        else:
            text = "[bold yellow]Veuillez jouer au moins 3 notes pour former un accord.[/bold yellow]"

        return Panel(text, title="Résultat", border_style="green")

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
                    attempt_notes, ready = self.collect_notes()
                    if not ready:
                        break

                    # Met à jour l'affichage avec le résultat
                    panel = self._build_result_panel(attempt_notes)
                    live.update(panel, refresh=True)

        finally:
            disable_raw_mode()

    def display_recognition_stats(self):
        pass


def reverse_chord_mode(inport, outport, chord_set):
    """Point d'entrée pour le mode reconnaissance d'accords"""
    mode = ReverseChordMode(inport, outport, chord_set)
    mode.run()
