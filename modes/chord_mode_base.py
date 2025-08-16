# Base class for chord modes
import random
import time
from typing import Callable, List, Optional

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.live import Live

from ui import get_colored_notes_string, display_stats, display_stats_fixed
from stats_manager import update_mode_record, update_stopwatch_record, update_timer_remaining_record
from screen_handler import clear_screen
from keyboard_handler import wait_for_any_key, wait_for_input,enable_raw_mode, disable_raw_mode
from midi_handler import play_chord, play_progression_sequence
from data.chords import all_chords
from music_theory import recognize_chord, are_chord_names_enharmonically_equivalent, get_chord_type_from_name, get_note_name

class ChordModeBase:
    def __init__(self, inport, outport, chord_set):
        self.inport = inport
        self.outport = outport
        self.chord_set = chord_set
        self.console = Console()
        # Compteurs hérités (utilisés par certains modes simples)
        self.correct_count = 0
        self.total_attempts = 0
        self.exit_flag = False

        self.wait_for_input = wait_for_input

        # Compteurs de session (utilisés par les modes de progression)
        self.session_correct_count = 0
        self.session_total_count = 0
        self.session_total_attempts = 0
        self.elapsed_time = 0.0
        self.last_played_notes = None  # Ajout de la variable ici pour la persistance
        # Chronomètre de session (actif quand le compte à rebours n'est pas utilisé)
        self.session_stopwatch_start_time = None
        self.session_max_remaining_time = None

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
            # Appeler la méthode spécialisée pour la répétition
            return self._handle_repeat()
        if char and char.lower() == 'n':
            return 'next'

        # Appelle la méthode des classes filles pour gérer leurs entrées spécifiques
        return self._handle_custom_input(char)

    def _handle_repeat(self):
        """Méthode par défaut pour la répétition - peut être redéfinie par les classes filles"""
        return 'repeat'
    
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
                result = self.handle_keyboard_input(char)
                if result is True:  # 'q' a été pressé
                    return None, None  # stop total
                if result == 'next':  # 'n' a été pressé
                    return None, None  # stop pour passer au suivant
                # Pour 'r' et autres touches, on continue la collecte

            # 2️⃣ Lecture MIDI
            for msg in self.inport.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Démarrer le chronomètre de session au premier appui MIDI si pas de compte à rebours
                    if not getattr(self, "use_timer", False) and self.session_stopwatch_start_time is None:
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

        return None, None

    def check_chord(self, attempt_notes, chord_name, chord_notes):
        if not attempt_notes:
            return False, None, None

        try:
            recognized_name, recognized_inversion = recognize_chord(attempt_notes)
            is_correct = (recognized_name and
                          are_chord_names_enharmonically_equivalent(recognized_name, chord_name) and
                          len(attempt_notes) == len(chord_notes))
            return is_correct, recognized_name, recognized_inversion
        except Exception as e:
            self.console.print(f"[bold red]Une erreur s'est produite lors de la reconnaissance : {e}[/bold red]")
            return False, None, None
        
    def show_overall_stats_and_wait(self):
        """Affiche les stats globales de la session et attend une touche."""
        self.console.print("\nAffichage des statistiques.")

        # Affichage principal
        display_stats_fixed(self.session_correct_count, self.session_total_attempts, self.session_total_count, self.elapsed_time)

        # Mise à jour du record de précision pour ce mode (si des tentatives existent)
        if self.session_total_attempts > 0:
            accuracy = (self.session_correct_count / self.session_total_attempts) * 100.0
            mode_key = self.__class__.__name__
            is_new_record, prev_best, new_best = update_mode_record(mode_key, accuracy, self.session_total_attempts)
            if is_new_record:
                if prev_best is not None:
                    self.console.print(f"\n[bold bright_green]Nouveau record ![/bold bright_green] Précision {accuracy:.2f}% (ancien: {float(prev_best):.2f}%).")
                else:
                    self.console.print(f"\n[bold bright_green]Premier record enregistré ![/bold bright_green] Précision {accuracy:.2f}%.")

        # Record de temps: soit chronomètre (moins de temps), soit minuteur (plus de temps restant)
        mode_key = self.__class__.__name__
        if getattr(self, "use_timer", False):
            if getattr(self, "session_max_remaining_time", None) is not None:
                is_new_time, prev_time, new_time = update_timer_remaining_record(mode_key, float(self.session_max_remaining_time), int(self.session_total_attempts))
                if is_new_time:
                    if prev_time is not None:
                        self.console.print(f"[bold bright_green]Nouveau record de temps restant ![/bold bright_green] {new_time:.2f}s (ancien: {float(prev_time):.2f}s).")
                    else:
                        self.console.print(f"[bold bright_green]Premier record de temps restant ![/bold bright_green] {new_time:.2f}s.")
        else:
            if self.elapsed_time:
                is_new_time, prev_time, new_time = update_stopwatch_record(mode_key, float(self.elapsed_time), int(self.session_total_attempts))
                if is_new_time:
                    if prev_time is not None:
                        self.console.print(f"[bold bright_green]Nouveau record de temps ![/bold bright_green] {new_time:.2f}s (ancien: {float(prev_time):.2f}s).")
                    else:
                        self.console.print(f"[bold bright_green]Premier record de temps ![/bold bright_green] {new_time:.2f}s.")

        self.console.print("\nAppuyez sur une touche pour retourner au menu principal.")
        self.clear_midi_buffer()
        wait_for_any_key(self.inport)

    # ---------- Boucle commune pour les modes de progression ----------
    def run_progression(
        self,
        progression_accords: List[str],
        header_title: str,
        header_name: str,
        border_style: str,
        pre_display: Optional[Callable[[], None]] = None,
    ) -> str:
        """
        Exécute une progression complète (boucle commune aux modes Cadence/Progression/Degrees).
        Retourne : 'exit' | 'skipped' | 'done'
        """
        if self.exit_flag:
            return 'exit'

        self.clear_midi_buffer()
        self.display_header(header_title, header_name, border_style)

        # Réinitialiser last_played_notes au début de chaque progression
        self.last_played_notes = None

        # Affichage optionnel spécifique (ex: tableau des degrés pour CadenceMode)
        if pre_display:
            pre_display()
        else:
            # Ligne d'aide commune, affichée seulement si pas de pre_display
            self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer à la suivante.")
            
        # Affichage progression
        if progression_accords:
            self.console.print(f"\nProgression à jouer : [bold yellow]{' -> '.join(progression_accords)}[/bold yellow]")

        # Lecture de la progression avant départ si demandé
        if getattr(self, "play_progression_before_start", False) and progression_accords:
            play_progression_sequence(self.outport, progression_accords, self.chord_set)

        # ----- Traitement de la progression -----
        progression_correct_count = 0
        progression_total_attempts = 0
        is_progression_started = False
        start_time = None
        skip_progression = False

        with Live(console=self.console, screen=False, auto_refresh=False) as live:
            prog_index = 0
            while prog_index < len(progression_accords) and not self.exit_flag and not skip_progression:
                chord_name = progression_accords[prog_index]
                target_notes = self.chord_set[chord_name]
                chord_attempts = 0
                
                # Correction du bug : On ne joue pas l'accord ici. On attend l'entrée utilisateur.
                
                time_info = ""
                if getattr(self, "use_timer", False) and is_progression_started:
                    remaining_time = self.timer_duration - (time.time() - start_time)
                    time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"

                live.update(self.create_live_display(chord_name, prog_index, len(progression_accords), time_info), refresh=True)

                notes_currently_on = set()
                attempt_notes = set()

                enable_raw_mode()
                try:
                    while not self.exit_flag and not skip_progression:
                        # Gestion du timer (affichage + fin)
                        if getattr(self, "use_timer", False) and is_progression_started:
                            remaining_time = self.timer_duration - (time.time() - start_time)
                            time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"
                            # On coupe le raw un instant pour rafraîchir correctement
                            disable_raw_mode()
                            live.update(self.create_live_display(chord_name, prog_index, len(progression_accords), time_info), refresh=True)
                            enable_raw_mode()

                            if remaining_time <= 0:
                                disable_raw_mode()
                                live.update("[bold red]Temps écoulé ! Session terminée.[/bold red]", refresh=True)
                                enable_raw_mode()
                                time.sleep(2)
                                self.exit_flag = True
                                break

                        # Clavier
                        char = wait_for_input(timeout=0.01)
                        if char:
                            action = self.handle_keyboard_input(char)
                            if action == 'repeat':
                                # vider le tampon clavier
                                while wait_for_input(timeout=0.001):
                                    pass
                                # lecture progression
                                disable_raw_mode()
                                live.update("[bold cyan]Lecture de la progression...[/bold cyan]", refresh=True)
                                play_progression_sequence(self.outport, progression_accords, self.chord_set)

                                # vider tampon puis repartir du début
                                enable_raw_mode()
                                while wait_for_input(timeout=0.001):
                                    pass
                                disable_raw_mode()

                                prog_index = 0
                                chord_name = progression_accords[prog_index]
                                target_notes = self.chord_set[chord_name]
                                live.update(self.create_live_display(chord_name, prog_index, len(progression_accords)), refresh=True)
                                enable_raw_mode()
                                break  # on sort de la boucle interne pour relancer sur le 1er accord

                            elif action == 'next':
                                skip_progression = True
                                break
                            elif action is True:  # 'q'
                                break

                        # MIDI
                        for msg in self.inport.iter_pending():
                            if msg.type == 'note_on' and msg.velocity > 0:
                                notes_currently_on.add(msg.note)
                                attempt_notes.add(msg.note)
                            elif msg.type == 'note_off':
                                notes_currently_on.discard(msg.note)

                        # Validation d'un essai
                        if not notes_currently_on and attempt_notes:
                            chord_attempts += 1
                            progression_total_attempts += 1

                            if not is_progression_started:
                                is_progression_started = True
                                start_time = time.time()

                            is_correct, recognized_name, recognized_inversion = self.check_chord(attempt_notes, chord_name, target_notes)

                            if is_correct:
                                success_msg = f"[bold green]Correct ! {chord_name}[/bold green]\nNotes jouées : [{get_colored_notes_string(attempt_notes, target_notes)}]"
                                disable_raw_mode()
                                live.update(success_msg, refresh=True)
                                enable_raw_mode()
                                time.sleep(2)
                                if chord_attempts == 1:
                                    progression_correct_count += 1
                                prog_index += 1
                                # On met à jour l'accord précédent après une réponse correcte
                                self.last_played_notes = attempt_notes
                                break
                            else:
                                error_msg = f"[bold red]Incorrect.[/bold red] Vous avez joué : {recognized_name if recognized_name else 'Accord non reconnu'}\nNotes jouées : [{get_colored_notes_string(attempt_notes, target_notes)}]"
                                disable_raw_mode()
                                live.update(error_msg, refresh=True)
                                time.sleep(2)
                                live.update(self.create_live_display(chord_name, prog_index, len(progression_accords)), refresh=True)
                                enable_raw_mode()
                                attempt_notes.clear()

                        time.sleep(0.01)
                finally:
                    disable_raw_mode()

            if self.exit_flag:
                return 'exit'

        # ----- Après la boucle -----
        if skip_progression:
            self.console.print("\n[bold yellow]Passage à la progression suivante.[/bold yellow]")
            time.sleep(1)
            return 'skipped'

        # Progression terminée : mise à jour stats de session
        self.session_correct_count += progression_correct_count
        self.session_total_attempts += progression_total_attempts
        # Correction du bug 7 accords: la boucle `while prog_index < len(progression_accords)`
        # ne permet pas de boucler une fois de trop, donc on peut simplement
        # ajouter la taille de la progression.
        self.session_total_count += len(progression_accords)


        # Affichage et pause de fin optionnels (peuvent être supprimés par une classe fille)
        if not getattr(self, "suppress_progression_summary", False):
            self.console.print(f"\n--- Statistiques de cette progression ---")
            self.console.print(f"Accords à jouer : [bold cyan]{len(progression_accords)}[/bold cyan]")
            self.console.print(f"Tentatives totales : [bold yellow]{progression_total_attempts}[/bold yellow]")
            self.console.print(f"Réussis du premier coup : [bold green]{progression_correct_count}[/bold green]")

            if progression_total_attempts > 0:
                accuracy = (progression_correct_count / progression_total_attempts) * 100
                self.console.print(f"Précision : [bold cyan]{accuracy:.1f}%[/bold cyan]")

            if is_progression_started:
                end_time = time.time()
                progression_elapsed = end_time - start_time
                if getattr(self, "use_timer", False):
                    self.elapsed_time = progression_elapsed
                    self.console.print(f"\nTemps pour la progression : [bold cyan]{self.elapsed_time:.2f} secondes[/bold cyan]")
                    # Mettre à jour le meilleur temps restant de la session si minuteur actif
                    remaining_time = max(0.0, self.timer_duration - self.elapsed_time)
                    if getattr(self, "session_max_remaining_time", None) is None or remaining_time > self.session_max_remaining_time:
                        self.session_max_remaining_time = remaining_time
                else:  # Stopwatch mode
                    self.elapsed_time += progression_elapsed
                    self.console.print(f"\nTemps pour la progression : [bold cyan]{progression_elapsed:.2f} secondes[/bold cyan]")

            # Pause fin progression
            self.wait_for_end_choice()
            if not self.exit_flag:
                clear_screen()

        return 'done'

    def display_feedback(self, is_correct, attempt_notes, chord_notes, recognized_name, recognized_inversion, specific = False):
        colored_notes = get_colored_notes_string(attempt_notes, chord_notes)
        self.console.print(f"Notes jouées : [{colored_notes}]")

        if is_correct:
            if recognized_name:
                self.console.print(f"[bold green]{recognized_name}.[/bold green]")
            else:
                if not specific:
                    self.console.print("[bold green]Correct ![/bold green]")
                else:
                    self.console.print("[bold red]Accord non reconnu ![/bold red]")
        else:
            if recognized_name:
                try:
                    clean_name = str(recognized_name).replace('%', 'pct').replace('{', '(').replace('}', ')')
                    clean_inversion = str(recognized_inversion).replace('%', 'pct').replace('{', '(').replace('}', ')') if recognized_inversion else "position inconnue"
                    self.console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {clean_name} ({clean_inversion})")
                except Exception:
                    self.console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {recognized_name}")
            else:
                self.console.print("[bold red]Incorrect. Réessayez.[/bold red]")

    def run(self):
        raise NotImplementedError("Subclasses must implement the run method.")

    def display_final_stats(self):
        # Calculer le temps écoulé de session si chronomètre actif (sans compte à rebours)
        if not getattr(self, "use_timer", False) and getattr(self, "session_stopwatch_start_time", None) is not None:
            self.elapsed_time = time.time() - self.session_stopwatch_start_time
        display_stats(self.correct_count, self.total_attempts, self.elapsed_time if self.elapsed_time else None)
        self.console.print("\nAppuyez sur une touche pour retourner au menu principal.")
        self.clear_midi_buffer()
        wait_for_any_key(self.inport)