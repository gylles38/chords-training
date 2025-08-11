# modes/single_chord_mode.py
import random
from rich.panel import Panel
from rich.text import Text

from .base_mode import BaseGameMode
from music_theory import recognize_chord, is_enharmonic_match_improved

class SingleChordMode(BaseGameMode):
    """Mode Accord Simple. L'utilisateur doit jouer l'accord affiché."""

    def get_challenge(self):
        """Retourne un tuple (nom_accord, notes_midi)."""
        chord_name, chord_notes = random.choice(list(self.chord_set.items()))
        return chord_name, chord_notes

    def display_challenge(self, live, challenge):
        """Affiche l'accord à jouer."""
        chord_name, _ = challenge
        # Correction : utiliser le balisage Rich directement dans le texte.
        # Rich.Live peut alors le parser correctement.
        panel = Panel(Text.from_markup(f"Jouez : [bold bright_yellow]{chord_name}[/bold bright_yellow]", justify="center"), title="Mode Accord Simple")
        live.update(panel, refresh=True)

    def check_answer(self, played_notes, challenge):
        """Vérifie si l'accord joué est le bon."""
        target_name, target_notes = challenge
        
        recognized_name, _ = recognize_chord(played_notes)
        
        is_correct = (recognized_name and
                      is_enharmonic_match_improved(recognized_name, target_name) and
                      len(played_notes) == len(target_notes))
                      
        recognized_info = recognized_name if recognized_name else "Accord non reconnu"
        return is_correct, recognized_info
