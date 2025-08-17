# modes/listen_and_reveal_mode.py
import time
import random
from typing import Literal
from rich.prompt import Prompt

from .chord_mode_base import ChordModeBase
from stats_manager import update_chord_error, update_chord_success

from midi_handler import play_chord
from screen_handler import clear_screen
from music_theory import get_note_name, get_chord_type_from_name
from keyboard_handler import wait_for_input, enable_raw_mode, disable_raw_mode

class ListenAndRevealMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set):
        super().__init__(inport, outport, chord_set)
        self.last_chord_name = None

    def _handle_repeat(self) -> Literal['repeat', False]:
        """Redéfinition pour rejouer l'accord en cours dans ce mode"""
        if hasattr(self, "current_chord_notes") and self.current_chord_notes is not None:
            play_chord(self.outport, self.current_chord_notes)
            return False  # ne pas interrompre collect_notes
        return 'repeat'  # comportement par défaut si pas d'accord en cours
    
    def collect_notes_listen_mode(self):
        """Version spécialisée de collect_notes pour le mode Écoute et Devine avec saisie instantanée"""
        notes_currently_on = set()
        attempt_notes = set()
        last_note_off_time = None

        enable_raw_mode()
        try:
            while not self.exit_flag:
                # 1️⃣ Lecture clavier en priorité avec timeout très court pour la réactivité
                char = wait_for_input(timeout=0.01)  # délai très court pour plus de réactivité
                if char:
                    # Gestion directe des touches spéciales pour ce mode
                    if char.lower() == 'q':
                        self.exit_flag = True
                        return None, None
                    elif char.lower() == 'n':
                        return None, None  # stop pour passer au suivant
                    elif char.lower() == 'r' and getattr(self, "current_chord_notes", None) is not None:
                        # Désactiver temporairement le mode raw pour jouer l'accord proprement
                        disable_raw_mode()
                        play_chord(self.outport, self.current_chord_notes)
                        enable_raw_mode()
                        # Continuer la collecte après avoir joué l'accord
                        continue

                # 2️⃣ Lecture MIDI
                for msg in self.inport.iter_pending():
                    if msg.type == 'note_on' and msg.velocity > 0:
                        # Démarrer le chronomètre de session au premier appui MIDI si pas de compte à rebours
                        if not getattr(self, "use_timer", False) and getattr(self, "session_stopwatch_start_time", None) is None:
                            self.session_stopwatch_start_time = time.time()
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
        finally:
            disable_raw_mode()

        return None, None
    
    def run(self):
        # Affichage du header et des instructions une seule fois
        self.display_header("Écoute et Devine", "Mode Écoute et Devine", "orange3")
        self.console.print("Écoutez l'accord joué et essayez de le reproduire.")
        self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter l'accord, 'n' pour passer au suivant.")

        while not self.exit_flag:
            self.clear_midi_buffer()
            # Tirage d'un accord pour ce cycle
            new_chord_name, new_chord_notes = random.choice(list(self.chord_set.items()))
            while new_chord_name == self.last_chord_name:
                new_chord_name, new_chord_notes = random.choice(list(self.chord_set.items()))
            self.current_chord_name = new_chord_name
            self.current_chord_notes = new_chord_notes
            self.last_chord_name = new_chord_name

            self.console.print(f"\n[bold yellow]Lecture de l'accord...[/bold yellow]")
            play_chord(self.outport, self.current_chord_notes)
            self.console.print("Jouez l'accord que vous venez d'entendre.")

            incorrect_attempts = 0
            skip_to_next = False

            while not self.exit_flag and not skip_to_next:
                # Utiliser la version spécialisée de collect_notes
                attempt_notes, ready = self.collect_notes_listen_mode()
                if not ready:
                    # Si c'est None, None, c'est probablement 'q' ou 'n'
                    if attempt_notes is None:
                        if self.exit_flag:
                            return  # Sortir complètement
                        else:
                            skip_to_next = True  # 'n' a été pressé
                            break
                    break

                self.total_attempts += 1
                is_correct, recognized_name, recognized_inversion = self.check_chord(
                    attempt_notes, self.current_chord_name, self.current_chord_notes
                )

                if is_correct:
                    update_chord_success(self.current_chord_name)
                    self.display_feedback(True, attempt_notes, self.current_chord_notes, recognized_name, recognized_inversion)
                    self.correct_count += 1
                    time.sleep(1.5)
                    break
                else:
                    update_chord_error(self.current_chord_name)
                    incorrect_attempts += 1
                    self.display_feedback(False, attempt_notes, self.current_chord_notes, recognized_name, recognized_inversion)

                    if incorrect_attempts >= 3:
                        tonic_note = sorted(list(self.current_chord_notes))[0]
                        tonic_name = get_note_name(tonic_note)
                        self.console.print(f"Indice : La tonique est [bold cyan]{tonic_name}[/bold cyan].")

                    if incorrect_attempts >= 7:
                        revealed_type = get_chord_type_from_name(self.current_chord_name)
                        self.console.print(f"Indice : C'est un accord de type [bold yellow]{revealed_type}[/bold yellow].")
                        self.console.print(f"[bold magenta]La réponse était : {self.current_chord_name}[/bold magenta]")
                        # Suppression de Prompt.ask - on continue automatiquement
                        time.sleep(2)  # Pause pour lire l'information
                        break

            # Passer à l'accord suivant : effacer l'écran et réafficher les instructions minimales
            clear_screen()
            self.display_header("Écoute et Devine", "Mode Écoute et Devine", "orange3")
            self.console.print("Écoutez l'accord joué et essayez de le reproduire.")
            self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter l'accord, 'n' pour passer au suivant.")

            # Accord terminé → on supprime la référence pour éviter répétition hors cycle
            self.current_chord_notes = None
            self.current_chord_name = None

        self.display_final_stats()
        # En complément, informer du record pour ce mode basé sur les compteurs hérités
        if self.total_attempts > 0:
            from stats_manager import update_mode_record, update_stopwatch_record, update_timer_remaining_record
            accuracy = (self.correct_count / self.total_attempts) * 100.0
            mode_key = self.__class__.__name__
            is_new_record, prev_best, new_best = update_mode_record(mode_key, accuracy, self.total_attempts)
            if is_new_record:
                if prev_best is not None:
                    self.console.print(f"\n[bold bright_green]Nouveau record ![/bold bright_green] Précision {accuracy:.2f}% (ancien: {float(prev_best):.2f}%).")
                else:
                    self.console.print(f"\n[bold bright_green]Premier record enregistré ![/bold bright_green] Précision {accuracy:.2f}%.")

            # Record de temps en fin de session pour ce mode
            if getattr(self, "use_timer", False):
                # Dans ce mode, pas de timer géré; on garde la structure pour homogénéité
                pass
            else:
                # Chronomètre: utiliser self.elapsed_time calculé dans display_final_stats (via session_stopwatch_start_time)
                if getattr(self, "session_stopwatch_start_time", None) is not None:
                    elapsed = time.time() - self.session_stopwatch_start_time if not getattr(self, "elapsed_time", None) else self.elapsed_time
                    is_new_time, prev_time, new_time = update_stopwatch_record(mode_key, float(elapsed), int(self.total_attempts))
                    if is_new_time:
                        if prev_time is not None:
                            self.console.print(f"[bold bright_green]Nouveau record de temps ![/bold bright_green] {new_time:.2f}s (ancien: {float(prev_time):.2f}s).")
                        else:
                            self.console.print(f"[bold bright_green]Premier record de temps ![/bold bright_green] {new_time:.2f}s.")


def listen_and_reveal_mode(inport, outport, chord_set):
    mode = ListenAndRevealMode(inport, outport, chord_set)
    mode.run()