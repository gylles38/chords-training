# modes/base_mode.py
import time
from abc import ABC, abstractmethod
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text

# Importer les fonctions nécessaires des autres modules
from midi_handler import play_chord, wait_for_input
from ui import get_colored_notes_string, display_stats_fixed

class BaseGameMode(ABC):
    """
    Classe de base abstraite pour tous les modes d'entraînement.
    Gère la boucle principale, la gestion des entrées MIDI et l'affichage.
    """
    def __init__(self, console, inport, outport, settings, chord_set):
        self.console = console
        self.inport = inport
        self.outport = outport
        self.settings = settings
        self.chord_set = chord_set
        self.exit_flag = False
        
        self.correct_count = 0
        self.total_attempts = 0
        self.total_challenges = 0

    @abstractmethod
    def get_challenge(self):
        """Génère un nouveau défi (ex: un accord, une progression)."""
        pass

    @abstractmethod
    def display_challenge(self, live, challenge):
        """
        Affiche le défi à l'utilisateur.
        Doit afficher le défi initial (ex: le nom de l'accord).
        """
        pass

    @abstractmethod
    def check_answer(self, played_notes, challenge):
        """Vérifie si les notes jouées correspondent au défi."""
        pass

    def run(self):
        """Lance la boucle principale du mode de jeu."""
        self.setup_display()

        while not self.exit_flag:
            challenge = self.get_challenge()
            if challenge is None:
                break
                
            self.total_challenges += 1
            self.play_challenge_audio(challenge)

            with Live(console=self.console, auto_refresh=True) as live:
                self.display_challenge(live, challenge)
                
                notes_currently_on = set()
                attempt_notes = set()

                while not self.exit_flag:
                    self.handle_keyboard_input()

                    # Itérer sur les messages MIDI en attente
                    for msg in self.inport.iter_pending():
                        if msg.type == 'note_on' and msg.velocity > 0:
                            notes_currently_on.add(msg.note)
                            attempt_notes.add(msg.note)
                            # On ne met pas à jour le panneau ici pour éviter le clignotement
                            # L'affichage se fera une fois l'accord relâché.

                        elif msg.type == 'note_off' and msg.note in notes_currently_on:
                            notes_currently_on.discard(msg.note)
                    
                    # Vérifier l'accord uniquement si aucune note n'est enfoncée et qu'un essai a eu lieu
                    if not notes_currently_on and attempt_notes:
                        self.total_attempts += 1
                        is_correct, recognized_info = self.check_answer(attempt_notes, challenge)
                        
                        if is_correct:
                            self.on_correct(live, attempt_notes, challenge)
                            time.sleep(1.5)
                            break  # Sortir de la boucle pour le prochain défi
                        else:
                            self.on_incorrect(live, attempt_notes, challenge, recognized_info)
                            attempt_notes.clear()  # Réinitialiser l'essai
                    
                    time.sleep(0.01)

        self.show_summary()


    def setup_display(self):
        self.console.clear()
        self.console.print(Panel(Text.from_markup(f"Mode : [bold]{self.__class__.__name__}[/bold]"), border_style="cyan"))
        self.console.print("Appuyez sur 'q' pour quitter.")

    def handle_keyboard_input(self):
        char = wait_for_input(timeout=0.01)
        if char and char.lower() == 'q':
            self.exit_flag = True

    def play_challenge_audio(self, challenge):
        pass

    def on_correct(self, live, played_notes, challenge):
        self.correct_count += 1
        target_name = challenge[0] if isinstance(challenge, tuple) else "Défi"
        live.update(Panel(Text.from_markup(f"Jouez : [bold bright_yellow]{target_name}[/bold bright_yellow]\n\n[bold green]Correct ![/bold green]"), title="Mode Accord Simple"))


    def on_incorrect(self, live, played_notes, challenge, recognized_info):
        target_notes = challenge[1] if isinstance(challenge, tuple) else None
        played_notes_str = get_colored_notes_string(played_notes, target_notes) if target_notes else ", ".join([str(n) for n in played_notes])
        
        # Récupérer le contenu actuel de l'affichage Live
        current_display = live.get_renderable()
        
        # Ajouter le nouveau message en dessous
        new_text = Text.from_markup(
            f"\nNotes jouées : {played_notes_str}\n"
            f"[bold red]Incorrect.[/bold red] Vous avez joué : {recognized_info}\n"
            f"Réessayez le même accord..."
        )
        
        # Combiner l'ancien contenu avec le nouveau
        live.update(Panel(Text.from_markup(str(current_display.render(self.console.options))).append(new_text), title="Mode Accord Simple"))
        time.sleep(1) # Un petit délai pour que le message soit visible.


    def show_summary(self):
        from ui import display_stats_fixed
        display_stats_fixed(self.console, self.correct_count, self.total_attempts, self.total_challenges)
