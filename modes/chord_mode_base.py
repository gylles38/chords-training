# Base class for chord modes
import random
import time
from typing import Callable, List, Optional, Literal

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.live import Live

from ui import get_colored_notes_string, display_stats, display_stats_fixed
from stats_manager import update_mode_record, update_stopwatch_record, update_timer_remaining_record, update_chord_error, update_chord_success
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
        self.use_voice_leading = False

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

    def _handle_repeat(self) -> Literal['repeat', False]:
        """Méthode par défaut pour la répétition - peut être redéfinie par les classes filles"""
        return 'repeat'
    
    def _handle_custom_input(self, char):
        # Cette méthode est un "placeholder" qui sera redéfini par les classes filles
        return False
    
    def create_live_display(self, chord_name, prog_index, total_chords, time_info=""):
        from music_theory import get_inversion_name # Local import
        display_name = chord_name.split(" #")[0]

        play_mode = getattr(self, "play_progression_before_start", "NONE")

        # In voice leading mode, we always show the notes and inversion.
        if self.use_voice_leading:
            target_notes = self.chord_set.get(chord_name, set())
            inversion_text = get_inversion_name(display_name, target_notes)
            note_names = [get_note_name(n) for n in sorted(list(target_notes))]
            notes_display = ", ".join(note_names)
            inversion_display = f" ({inversion_text})" if inversion_text and inversion_text != "position fondamentale" else ""
            content = (
                f"Accord à jouer ({prog_index + 1}/{total_chords}): [bold yellow]{display_name}{inversion_display}[/bold yellow]\n"
                f"Notes attendues : [cyan]{notes_display}[/cyan]"
            )
        # For other modes, we keep the original behavior
        else:
            if play_mode == 'PLAY_ONLY':
                content = f"Jouez l'accord ({prog_index + 1}/{total_chords})"
            else:
                content = f"Accord à jouer ({prog_index + 1}/{total_chords}): [bold yellow]{display_name}[/bold yellow]"

        if time_info:
            content += f"\n{time_info}"
        return Panel(content, title="Progression en cours", border_style="green")
    
    def wait_for_end_choice(self) -> str:
        """Attend une saisie instantanée pour continuer ou quitter."""
        self.console.print("\n[bold green]Progression terminée ![/bold green] Appuyez sur une touche pour continuer ou 'q' pour quitter...")
        enable_raw_mode()
        try:
            while not self.exit_flag:
                char = wait_for_input(timeout=0.05)
                if char:
                    if char.lower() == 'q':
                        self.exit_flag = True
                        return 'quit'
                    return 'continue'
                time.sleep(0.01)
        finally:
            disable_raw_mode()
        return 'continue'
    
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

        # If voice leading is used, we need an exact note match.
        if getattr(self, 'use_voice_leading', False):
            is_correct = (attempt_notes == chord_notes)
            # We can still use recognize_chord to provide helpful feedback
            recognized_name, recognized_inversion = recognize_chord(attempt_notes)
            return is_correct, recognized_name, recognized_inversion

        # Original behavior: name-based recognition
        try:
            recognized_name, recognized_inversion = recognize_chord(attempt_notes)
            is_correct = (recognized_name and
                          are_chord_names_enharmonically_equivalent(recognized_name, chord_name) and
                          len(attempt_notes) == len(chord_notes))
            return is_correct, recognized_name, recognized_inversion
        except Exception as e:
            self.console.print(f"[bold red]Une erreur s'est produite lors de la reconnaissance : {e}[/bold red]")
            return False, None, None
        
    def show_overall_stats_and_wait(self, extra_stats_callback: Optional[Callable] = None):
        """Affiche les stats globales de la session et attend une touche."""
        self.console.print("\nAffichage des statistiques.")

        # Affichage principal
        display_stats_fixed(self.session_correct_count, self.session_total_attempts, self.session_total_count, self.elapsed_time)

        base_mode_key = self.__class__.__name__
        play_mode = getattr(self, "play_progression_before_start", None)

        # Créer une clé de stat unique pour les modes de progression basés sur la difficulté
        if play_mode:
            mode_key = f"{base_mode_key}_{play_mode}"
        else:
            mode_key = base_mode_key

        # Mise à jour du record de précision pour ce mode (si des tentatives existent)
        if self.session_total_attempts > 0:
            accuracy = (self.session_correct_count / self.session_total_attempts) * 100.0
            is_new_record, prev_best, new_best = update_mode_record(mode_key, accuracy, self.session_total_attempts)
            if is_new_record:
                if prev_best is not None:
                    self.console.print(f"\n[bold bright_green]Nouveau record ![/bold bright_green] Précision {accuracy:.2f}% (ancien: {float(prev_best):.2f}%).")
                else:
                    self.console.print(f"\n[bold bright_green]Premier record enregistré ![/bold bright_green] Précision {accuracy:.2f}%.")

        # Record de temps: soit chronomètre (moins de temps), soit minuteur (plus de temps restant)
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

        if extra_stats_callback:
            extra_stats_callback()

        self.console.print("\nAppuyez sur une touche pour retourner au menu principal.")
        self.clear_midi_buffer()
        wait_for_any_key(self.inport)

    # ---------- Méthodes pour le guidage vocal (transitions) ----------

    def _get_inversions(self, notes):
        """Generates all inversions for a set of notes."""
        inversions = []
        sorted_notes = sorted(list(notes))
        for i in range(len(sorted_notes)):
            inversion = set(sorted_notes[i:] + [n + 12 for n in sorted_notes[:i]])
            inversions.append(inversion)
        return inversions

    def _calculate_voice_leading_cost(self, notes1, notes2):
        """Calculates the voice leading cost between two chords."""
        if not notes1 or not notes2 or len(notes1) != len(notes2):
            return float('inf')

        list1 = sorted(list(notes1))
        list2 = sorted(list(notes2))

        return sum(abs(n1 - n2) for n1, n2 in zip(list1, list2))

    def _calculate_best_voicings(self, progression_names):
        """
        Calculates the best voicings for a progression to ensure smooth transitions.
        """
        if not progression_names:
            return [], []

        final_voicings = []
        # Start with the root position of the first chord around middle C (60)
        first_chord_notes = self.chord_set[progression_names[0]]
        avg_midi = sum(first_chord_notes) / len(first_chord_notes)
        octave_shift = round((60 - avg_midi) / 12) * 12
        current_voicing = {note + octave_shift for note in first_chord_notes}
        final_voicings.append(current_voicing)

        for i in range(1, len(progression_names)):
            previous_voicing = final_voicings[i-1]
            next_chord_name = progression_names[i]
            next_chord_notes_root = self.chord_set[next_chord_name]

            # Generate all inversions of the next chord
            inversions = self._get_inversions(next_chord_notes_root)

            best_voicing = None
            min_cost = float('inf')

            # For each inversion, find the best octave to match the previous chord
            for inv in inversions:
                # Center the inversion around the previous chord's average MIDI value
                avg_prev = sum(previous_voicing) / len(previous_voicing)
                avg_inv = sum(inv) / len(inv)
                octave_shift = round((avg_prev - avg_inv) / 12) * 12
                shifted_inv = {note + octave_shift for note in inv}

                cost = self._calculate_voice_leading_cost(previous_voicing, shifted_inv)

                if cost <= min_cost:
                    min_cost = cost
                    best_voicing = shifted_inv

            final_voicings.append(best_voicing)

        return final_voicings

    def _build_transition_summary_text(self, progression_accords, voicings, original_chord_set):
        """Builds the two Text objects for the progression summary."""
        from music_theory import get_note_name_with_octave # Local import

        # Pad labels for alignment
        label1 = "Progression à jouer : "
        label2 = "Progression des transitions : "
        max_len = max(len(label1), len(label2))

        # Line 1: Root positions
        root_pos_text = Text(label1.ljust(max_len), style="default")
        for i, name in enumerate(progression_accords):
            display_name = name.split(" #")[0]
            # Use original_chord_set to get root position notes
            root_notes = original_chord_set.get(display_name, set())
            note_names = ", ".join([get_note_name_with_octave(n) for n in sorted(list(root_notes))])
            root_pos_text.append(f"{display_name} ({note_names})", style="bold yellow")
            if i < len(progression_accords) - 1:
                root_pos_text.append(" -> ", style="default")

        # Line 2: Transitions with highlighting
        transitions_text = Text(label2.ljust(max_len), style="default")
        for i, name in enumerate(progression_accords):
            display_name = name.split(" #")[0]
            current_notes = voicings[i]
            common_notes = current_notes.intersection(voicings[i-1]) if i > 0 else set()

            transitions_text.append(f"{display_name} (", style="bold yellow")
            note_list = sorted(list(current_notes))
            for j, note_val in enumerate(note_list):
                note_name = get_note_name_with_octave(note_val)
                style = "bold green" if note_val in common_notes else "cyan"
                transitions_text.append(note_name, style=style)
                if j < len(note_list) - 1:
                    transitions_text.append(", ", style="default")
            transitions_text.append(")", style="bold yellow")

            if i < len(progression_accords) - 1:
                transitions_text.append(" -> ", style="default")

        return root_pos_text, transitions_text


    # ---------- Boucle commune pour les modes de progression ----------
    def run_progression(
        self,
        progression_accords: List[str],
        header_title: str,
        header_name: str,
        border_style: str,
        pre_display: Optional[Callable[[], None]] = None,
        debug_info: Optional[str] = None,
        key_name: str = "",
    ) -> str:
        if self.exit_flag:
            return 'exit'

        self.clear_midi_buffer()
        self.display_header(header_title, header_name, border_style)

        if debug_info:
            self.console.print(debug_info)

        self.last_played_notes = None

        if pre_display:
            pre_display()
        else:
            self.console.print("\nAppuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer à la suivante.\n")

        play_mode = getattr(self, "play_progression_before_start", "NONE")

        current_progression_chords = progression_accords
        original_chord_set = self.chord_set
        temp_chord_set = None
        voicings = []

        if self.use_voice_leading and progression_accords:
            voicings = self._calculate_best_voicings(progression_accords)
            temp_chord_set = {}
            temp_progression_names = []
            for i, (name, voicing) in enumerate(zip(progression_accords, voicings)):
                unique_name = f"{name} #{i}"
                temp_progression_names.append(unique_name)
                temp_chord_set[unique_name] = voicing

            current_progression_chords = temp_progression_names
            self.chord_set = temp_chord_set

            if play_mode == 'SHOW_AND_PLAY':
                if key_name:
                    self.console.print(f"Tonalité : [bold cyan]{key_name}[/bold cyan]")
                root_pos_text, transitions_text = self._build_transition_summary_text(progression_accords, voicings, original_chord_set)
                self.console.print(root_pos_text)
                self.console.print(transitions_text)

        elif play_mode == 'SHOW_AND_PLAY' and progression_accords:
            display_names = [name.split(" #")[0] for name in progression_accords]
            self.console.print(f"\nProgression à jouer : [bold yellow]{' -> '.join(display_names)}[/bold yellow]")

        if play_mode == 'PLAY_ONLY' and progression_accords:
            self.console.print("\nÉcoutez la progression...")

        if (play_mode == 'SHOW_AND_PLAY' or play_mode == 'PLAY_ONLY') and current_progression_chords:
            play_progression_sequence(self.outport, current_progression_chords, self.chord_set)

        progression_correct_count = 0
        progression_total_attempts = 0
        is_progression_started = False
        start_time = None
        skip_progression = False
        choice = 'continue'

        with Live(console=self.console, screen=False, auto_refresh=False) as live:
            prog_index = 0
            while prog_index < len(current_progression_chords) and not self.exit_flag and not skip_progression:
                chord_name = current_progression_chords[prog_index]
                target_notes = self.chord_set[chord_name]
                chord_attempts = 0
                
                time_info = ""
                if getattr(self, "use_timer", False) and is_progression_started and start_time is not None:
                    remaining_time = self.timer_duration - (time.time() - start_time)
                    time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"

                live.update(self.create_live_display(chord_name, prog_index, len(current_progression_chords), time_info), refresh=True)

                notes_currently_on = set()
                attempt_notes = set()

                enable_raw_mode()
                try:
                    while not self.exit_flag and not skip_progression:
                        if getattr(self, "use_timer", False) and is_progression_started and start_time is not None:
                            remaining_time = self.timer_duration - (time.time() - start_time)
                            time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"
                            disable_raw_mode()
                            live.update(self.create_live_display(chord_name, prog_index, len(current_progression_chords), time_info), refresh=True)
                            enable_raw_mode()
                            if remaining_time <= 0:
                                disable_raw_mode()
                                live.update("[bold red]Temps écoulé ! Session terminée.[/bold red]", refresh=True)
                                enable_raw_mode()
                                time.sleep(2)
                                self.exit_flag = True
                                break

                        char = wait_for_input(timeout=0.01)
                        if char:
                            action = self.handle_keyboard_input(char)
                            if action == 'repeat':
                                while wait_for_input(timeout=0.001): pass
                                disable_raw_mode()
                                live.update("[bold cyan]Lecture de la progression...[/bold cyan]", refresh=True)
                                play_progression_sequence(self.outport, current_progression_chords, self.chord_set)
                                enable_raw_mode()
                                while wait_for_input(timeout=0.001): pass
                                disable_raw_mode()
                                prog_index = 0
                                chord_name = current_progression_chords[prog_index]
                                target_notes = self.chord_set[chord_name]
                                live.update(self.create_live_display(chord_name, prog_index, len(current_progression_chords)), refresh=True)
                                enable_raw_mode()
                                break
                            elif action == 'next':
                                skip_progression = True
                                choice = 'skipped'
                                break
                            elif action is True:
                                break

                        for msg in self.inport.iter_pending():
                            if msg.type == 'note_on' and msg.velocity > 0:
                                notes_currently_on.add(msg.note)
                                attempt_notes.add(msg.note)
                            elif msg.type == 'note_off':
                                notes_currently_on.discard(msg.note)

                        if not notes_currently_on and attempt_notes:
                            chord_attempts += 1
                            progression_total_attempts += 1
                            if not is_progression_started:
                                is_progression_started = True
                                start_time = time.time()
                            is_correct, recognized_name, recognized_inversion = self.check_chord(attempt_notes, chord_name, target_notes)
                            if is_correct:
                                update_chord_success(chord_name.split(" #")[0])
                                success_msg = f"[bold green]Correct ! {chord_name.split(' #')[0]}[/bold green]\nNotes jouées : [{get_colored_notes_string(attempt_notes, target_notes)}]"
                                disable_raw_mode()
                                live.update(success_msg, refresh=True)
                                enable_raw_mode()
                                time.sleep(2)
                                if chord_attempts == 1:
                                    progression_correct_count += 1
                                prog_index += 1
                                self.last_played_notes = attempt_notes
                                break
                            else:
                                update_chord_error(chord_name.split(" #")[0])
                                error_msg = f"[bold red]Incorrect.[/bold red] Vous avez joué : {recognized_name if recognized_name else 'Accord non reconnu'}\nNotes jouées : [{get_colored_notes_string(attempt_notes, target_notes)}]"
                                disable_raw_mode()
                                live.update(error_msg, refresh=True)
                                time.sleep(2)
                                live.update(self.create_live_display(chord_name, prog_index, len(current_progression_chords)), refresh=True)
                                enable_raw_mode()
                                attempt_notes.clear()
                        time.sleep(0.01)
                finally:
                    disable_raw_mode()
            if self.exit_flag:
                if temp_chord_set: self.chord_set = original_chord_set
                return 'exit'

        if skip_progression:
            self.console.print("\n[bold yellow]Passage à la progression suivante.[/bold yellow]")
            time.sleep(1)
            if temp_chord_set: self.chord_set = original_chord_set
            return 'skipped'

        self.session_correct_count += progression_correct_count
        self.session_total_attempts += progression_total_attempts
        self.session_total_count += len(progression_accords)

        if not getattr(self, "suppress_progression_summary", False):
            self.console.print(f"\n--- Statistiques de cette progression ---")
            self.console.print(f"Accords à jouer : [bold cyan]{len(progression_accords)}[/bold cyan]")
            self.console.print(f"Tentatives totales : [bold yellow]{progression_total_attempts}[/bold yellow]")
            self.console.print(f"Réussis du premier coup : [bold green]{progression_correct_count}[/bold green]")
            if progression_total_attempts > 0:
                accuracy = (progression_correct_count / progression_total_attempts) * 100
                self.console.print(f"Précision : [bold cyan]{accuracy:.1f}%[/bold cyan]")
            if is_progression_started and start_time is not None:
                end_time = time.time()
                progression_elapsed = end_time - start_time
                if getattr(self, "use_timer", False):
                    self.elapsed_time = progression_elapsed
                    self.console.print(f"\nTemps pour la progression : [bold cyan]{self.elapsed_time:.2f} secondes[/bold cyan]")
                    remaining_time = max(0.0, self.timer_duration - self.elapsed_time)
                    if getattr(self, "session_max_remaining_time", None) is None or remaining_time > self.session_max_remaining_time:
                        self.session_max_remaining_time = remaining_time
                else:
                    self.elapsed_time += progression_elapsed
                    self.console.print(f"\nTemps pour la progression : [bold cyan]{progression_elapsed:.2f} secondes[/bold cyan]")

            choice = self.wait_for_end_choice()
            if not self.exit_flag:
                clear_screen()

        if temp_chord_set:
            self.chord_set = original_chord_set

        return choice

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