# modes/listen_and_reveal_mode.py
import random
import time
from rich.prompt import Prompt

from .chord_mode_base import ChordModeBase

from midi_handler import play_chord
from music_theory import get_note_name, get_chord_type_from_name
from screen_handler import clear_screen
from keyboard_handler import wait_for_input, enable_raw_mode, disable_raw_mode

class ListenAndRevealMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = False
        self.play_progression_before_start = False
        self.suppress_progression_summary = True

        self.current_chord_notes = None
        self.current_chord_name = None

    def _handle_repeat(self):
        if self.current_chord_notes:
            play_chord(self.outport, self.current_chord_notes)
        return False

    def run(self):
        # Affichage du header et des instructions une seule fois
        self.display_header("Écoute et Devine", "Mode Écoute et Devine", "orange3")

        def pre_display():
            self.console.print("Écoutez l'accord joué et essayez de le reproduire.")
            # Le message d'aide spécifique est maintenant ici
            self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter l'accord, 'n' pour passer au suivant.")

        last_chord_name = None
        while not self.exit_flag:
            self.clear_midi_buffer()
            
            chord_name, chord_notes = random.choice(list(self.chord_set.items()))
            if len(self.chord_set) > 1:
                while chord_name == last_chord_name:
                    chord_name, chord_notes = random.choice(list(self.chord_set.items()))
            last_chord_name = chord_name
            
            self.current_chord_name = chord_name
            self.current_chord_notes = chord_notes

            self.console.print(f"\n[bold yellow]Lecture de l'accord...[/bold yellow]")
            play_chord(self.outport, self.current_chord_notes)
            self.console.print("Jouez l'accord que vous venez d'entendre.")

            result = self.run_progression(
                progression_accords=[chord_name],
                header_title="Écoute et Devine",
                header_name="Mode Écoute et Devine",
                border_style="orange3",
                pre_display=pre_display,
            )

            if result == 'exit':
                break
        
        self.show_overall_stats_and_wait()

def listen_and_reveal_mode(inport, outport, chord_set):
    mode = ListenAndRevealMode(inport, outport, chord_set)
    mode.run()