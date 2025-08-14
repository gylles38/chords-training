# Base class for chord modes
import random
import time
from typing import Callable, List, Optional

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.live import Live

from ui import get_colored_notes_string, display_stats, display_stats_fixed
from screen_handler import clear_screen
from keyboard_handler import wait_for_any_key, wait_for_input,enable_raw_mode, disable_raw_mode
from midi_handler import play_chord, play_progression_sequence
from data.chords import all_chords
from music_theory import recognize_chord, is_enharmonic_match_improved, get_chord_type_from_name, get_note_name

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
                result = self.handle_keyboard_input(char)
                if result is True:  # 'q' a été pressé
                    return None, None  # stop total
                # Pour 'r' et autres touches, on continue la collecte

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

    def show_overall_stats_and_wait(self):
        """Affiche les stats globales de la session et attend une touche."""
        self.console.print("\nAffichage des statistiques.")
        display_stats_fixed(self.session_correct_count, self.session_total_attempts, self.session_total_count, self.elapsed_time)
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

        # Affichage optionnel spécifique (ex: tableau des degrés pour CadenceMode)
        if pre_display:
            pre_display()

        # Ligne d'aide commune
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

                            if getattr(self, "use_timer", False) and not is_progression_started:
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

            if getattr(self, "use_timer", False) and is_progression_started:
                end_time = time.time()
                self.elapsed_time = end_time - start_time
                self.console.print(f"\nTemps pour la progression : [bold cyan]{self.elapsed_time:.2f} secondes[/bold cyan]")

            # Pause fin progression
            self.wait_for_end_choice()
            if not self.exit_flag:
                clear_screen()

        return 'done'

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
