# Base class for chord modes
import random
import time
from rich.console import Console
from rich.text import Text
from rich.panel import Panel

from ui import get_colored_notes_string, display_stats
from screen_handler import clear_screen
from keyboard_handler import wait_for_any_key, wait_for_input,enable_raw_mode, disable_raw_mode
from midi_handler import play_chord
from data.chords import all_chords
from music_theory import recognize_chord, is_enharmonic_match_improved, get_chord_type_from_name, get_note_name

class ChordModeBase:
    def __init__(self, inport, outport, chord_set):
        self.inport = inport
        self.outport = outport
        self.chord_set = chord_set
        self.console = Console()
        self.correct_count = 0
        self.total_attempts = 0
        self.exit_flag = False

        self.wait_for_input = wait_for_input

    def clear_midi_buffer(self):
        for _ in self.inport.iter_pending():
            pass

    def display_header(self, mode_title, mode_name, border_style):
        clear_screen()
        self.console.print(Panel(
            Text(mode_name, style=f"bold {border_style}", justify="center"),
            title=mode_title,
            border_style=border_style
        ))
        chord_type = 'Tous' if self.chord_set == all_chords else 'Majeurs/Mineurs'
        self.console.print(f"Type d'accords: [bold cyan]{chord_type}[/bold cyan]")

    def handle_keyboard_input(self, char):
        # Gère les entrées communes dans la classe mère
        if char and char.lower() == 'q':
            self.exit_flag = True
            return True
        if char and char.lower() == 'r':
            return 'repeat'
        if char and char.lower() == 'n':
            return 'next'

        # Appelle la méthode des classes filles pour gérer leurs entrées spécifiques
        return self._handle_custom_input(char)

    def _handle_custom_input(self, char):
        # Cette méthode est un "placeholder" qui sera redéfini par les classes filles
        return False
    
    def create_live_display(self, chord_name, prog_index, total_chords, time_info=""):
        content = f"Accord à jouer ({prog_index + 1}/{total_chords}): [bold yellow]{chord_name}[/bold yellow]"
        if time_info:
            content += f"\n{time_info}"
        return Panel(content, title="Progression en cours", border_style="green")
    
    def wait_for_end_choice(self):
        """Attend une saisie instantanée pour continuer ou quitter"""
        self.console.print("\n[bold green]Progression terminée ![/bold green] Appuyez sur une touche pour continuer ou 'q' pour quitter...")
        enable_raw_mode()
        try:
            while not self.exit_flag:
                char = wait_for_input(timeout=0.05)
                if char:
                    if char.lower() == 'q':
                        self.exit_flag = True
                    return  # N'importe quelle autre touche continue
                time.sleep(0.01)
        finally:
            disable_raw_mode()
    
    def collect_notes(self):
        notes_currently_on = set()
        attempt_notes = set()
        last_note_off_time = None

        while not self.exit_flag:
            # 1️⃣ Lecture clavier en priorité
            char = wait_for_input(timeout=0.05)  # délai augmenté pour fiabilité
            if char:
                # handle_keyboard_input gère 'q' et 'r'
                if self.handle_keyboard_input(char):
                    return None, None  # stop total (pour 'q')

            # 2️⃣ Lecture MIDI
            for msg in self.inport.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    notes_currently_on.add(msg.note)
                    attempt_notes.add(msg.note)
                    last_note_off_time = None
                elif msg.type == 'note_off':
                    notes_currently_on.discard(msg.note)
                    if not notes_currently_on and not last_note_off_time:
                        last_note_off_time = time.time()

            # 3️⃣ Validation si toutes les notes sont relâchées depuis un moment
            if last_note_off_time and time.time() - last_note_off_time > 0.3:
                return attempt_notes, True

            time.sleep(0.01)  # petite pause pour éviter 100% CPU

        return None, None

    def check_chord(self, attempt_notes, chord_name, chord_notes):
        if not attempt_notes:
            return False, None, None

        try:
            recognized_name, recognized_inversion = recognize_chord(attempt_notes)
            is_correct = (recognized_name and
                          is_enharmonic_match_improved(recognized_name, chord_name, self.chord_set) and
                          len(attempt_notes) == len(chord_notes))
            return is_correct, recognized_name, recognized_inversion
        except Exception as e:
            self.console.print(f"[bold red]Une erreur s'est produite lors de la reconnaissance : {e}[/bold red]")
            return False, None, None

    def display_feedback(self, is_correct, attempt_notes, chord_notes, recognized_name, recognized_inversion):
        colored_notes = get_colored_notes_string(attempt_notes, chord_notes)
        self.console.print(f"Notes jouées : [{colored_notes}]")

        if is_correct:
            self.console.print(f"[bold green]Correct ! C'était bien {recognized_name}.[/bold green]")
        else:
            if recognized_name:
                clean_name = str(recognized_name).replace('%', 'pct').replace('{', '(').replace('}', ')')
                clean_inversion = str(recognized_inversion).replace('%', 'pct').replace('{', '(').replace('}', ')') if recognized_inversion else "position inconnue"
                self.console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {clean_name} ({clean_inversion})")
            else:
                self.console.print("[bold red]Incorrect. Réessayez.[/bold red]")

    def run(self):
        raise NotImplementedError("Subclasses must implement the run method.")

    def display_final_stats(self):
        display_stats(self.correct_count, self.total_attempts)
        self.console.print("\nAppuyez sur une touche pour retourner au menu principal.")
        self.clear_midi_buffer()
        wait_for_any_key(self.inport)