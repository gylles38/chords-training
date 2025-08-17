# modes/chord_transitions_mode.py
import random
import time
from typing import Callable, List, Optional

from rich.panel import Panel
from rich.live import Live
from rich.text import Text

from .chord_mode_base import ChordModeBase
from data.chords import three_note_chords, gammes_majeures
from music_theory import get_note_name, recognize_chord, get_inversion_name, get_note_name_with_octave
from midi_handler import play_progression_sequence
from ui import get_colored_notes_string
from stats_manager import update_chord_error, update_chord_success, get_chord_errors
from keyboard_handler import wait_for_input, enable_raw_mode, disable_raw_mode
from screen_handler import clear_screen

def weighted_sample_without_replacement(population, weights, k=1):
    """
    Performs weighted sampling without replacement.
    """
    population = list(population)
    weights = list(weights)

    if len(population) < k:
        return random.sample(population, k)

    result = []
    for _ in range(k):
        if not population:
            break
        chosen_element = random.choices(population, weights=weights, k=1)[0]
        chosen_index = population.index(chosen_element)
        population.pop(chosen_index)
        weights.pop(chosen_index)
        result.append(chosen_element)
    return result

class ChordTransitionsMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set):
        super().__init__(inport, outport, chord_set)
        self.progression_length = (2, 4)
        # Declare attributes for type checker
        self.use_timer: bool = False
        self.timer_duration: float = 30.0
        self.play_progression_before_start: str = 'SHOW_AND_PLAY'

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

    def create_live_display(self, chord_name, prog_index, total_chords, time_info=""):
        # Override to remove the unique identifier from the chord name for display
        display_name = chord_name.split(" #")[0]

        # Get the target notes and inversion name for display
        target_notes = self.chord_set.get(chord_name, set())
        inversion_text = get_inversion_name(display_name, target_notes)

        note_names = [get_note_name(n) for n in sorted(list(target_notes))]
        notes_display = ", ".join(note_names)

        play_mode = getattr(self, "play_progression_before_start", "NONE")
        if play_mode == 'PLAY_ONLY':
            content = f"Jouez l'accord ({prog_index + 1}/{total_chords})"
        else:
            inversion_display = f" ({inversion_text})" if inversion_text and inversion_text != "position fondamentale" else ""
            content = (
                f"Accord à jouer ({prog_index + 1}/{total_chords}): [bold yellow]{display_name}{inversion_display}[/bold yellow]\n"
                f"Notes attendues : [cyan]{notes_display}[/cyan]"
            )

        if time_info:
            content += f"\n{time_info}"
        return Panel(content, title="Progression en cours", border_style="green")

    def check_chord(self, attempt_notes, chord_name, chord_notes):
        """
        Overrides the base class method to check for exact note matching
        for a specific voicing, rather than comparing chord names.
        """
        if not attempt_notes:
            return False, None, None

        # The core check: did the user play the exact notes of the target voicing?
        is_correct = (attempt_notes == chord_notes)

        # We can still use recognize_chord to provide helpful feedback
        recognized_name, recognized_inversion = recognize_chord(attempt_notes)

        return is_correct, recognized_name, recognized_inversion

    def wait_for_end_choice(self) -> str:
        """Overrides base method to add a 'replay' option."""
        self.console.print("\n[bold green]Progression terminée ![/bold green] Appuyez sur 'r' pour rejouer, 'q' pour quitter, ou une autre touche pour continuer...")
        enable_raw_mode()
        try:
            while not self.exit_flag:
                char = wait_for_input(timeout=0.05)
                if char:
                    if char.lower() == 'q':
                        self.exit_flag = True
                        return 'quit'
                    elif char.lower() == 'r':
                        return 'repeat'
                    else:
                        return 'continue'
                time.sleep(0.01)
        finally:
            disable_raw_mode()
        return 'continue' # Default action

    def _build_progression_summary_text(self, progression_accords, voicings):
        """Builds the two Text objects for the progression summary."""
        # Pad labels for alignment
        label1 = "Progression à jouer : "
        label2 = "Progression des transitions : "
        max_len = max(len(label1), len(label2))

        # Line 1: Root positions
        root_pos_text = Text(label1.ljust(max_len), style="default")
        for i, name in enumerate(progression_accords):
            display_name = name.split(" #")[0]
            root_notes = three_note_chords.get(display_name, set())
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

    def run_progression(
        self,
        progression_accords: List[str],
        header_title: str,
        header_name: str,
        border_style: str,
        pre_display: Optional[Callable] = None,
        debug_info: Optional[str] = None,
        key_name: str = "", # Add as optional parameter
    ) -> str:
        """
        Overrides the base class method to display cleaned-up chord names in the
        initial progression summary.
        """
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

        # --- MODIFICATION START ---
        # Display the two-line progression summary
        if play_mode == 'SHOW_AND_PLAY' and progression_accords:
            if key_name:
                self.console.print(f"Tonalité : [bold cyan]{key_name}[/bold cyan]")
            voicings = [self.chord_set.get(name, set()) for name in progression_accords]
            root_pos_text, transitions_text = self._build_progression_summary_text(progression_accords, voicings)
            self.console.print(root_pos_text)
            self.console.print(transitions_text)
        # --- MODIFICATION END ---
        elif play_mode == 'PLAY_ONLY' and progression_accords:
            self.console.print("\nÉcoutez la progression...")

        if (play_mode == 'SHOW_AND_PLAY' or play_mode == 'PLAY_ONLY') and progression_accords:
            # play_progression_sequence uses self.chord_set, which has the unique names, so we pass the original list
            play_progression_sequence(self.outport, progression_accords, self.chord_set)

        # The rest of the method is identical to the base class, so we can just call it.
        # To do that, we need to avoid recursion. We can call the base class method directly.
        # However, that would require modifying the base class.
        # For now, we accept the duplication. The rest of the code is copied from ChordModeBase.

        # ----- Traitement de la progression -----
        progression_correct_count = 0
        progression_total_attempts = 0
        is_progression_started = False
        start_time: Optional[float] = None
        skip_progression = False
        choice = 'continue' # Default value

        with Live(console=self.console, screen=False, auto_refresh=False) as live:
            prog_index = 0
            while prog_index < len(progression_accords) and not self.exit_flag and not skip_progression:
                chord_name = progression_accords[prog_index]
                target_notes = self.chord_set[chord_name]
                chord_attempts = 0

                time_info = ""
                if getattr(self, "use_timer", False) and is_progression_started and start_time is not None:
                    remaining_time = self.timer_duration - (time.time() - start_time)
                    time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"

                live.update(self.create_live_display(chord_name, prog_index, len(progression_accords), time_info), refresh=True)

                notes_currently_on = set()
                attempt_notes = set()

                enable_raw_mode()
                try:
                    while not self.exit_flag and not skip_progression:
                        if getattr(self, "use_timer", False) and is_progression_started and start_time is not None:
                            remaining_time = self.timer_duration - (time.time() - start_time)
                            time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"
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

                        char = wait_for_input(timeout=0.01)
                        if char:
                            action = self.handle_keyboard_input(char)
                            if action == 'repeat':
                                while wait_for_input(timeout=0.001): pass
                                disable_raw_mode()
                                live.update("[bold cyan]Lecture de la progression...[/bold cyan]", refresh=True)
                                play_progression_sequence(self.outport, progression_accords, self.chord_set)
                                enable_raw_mode()
                                while wait_for_input(timeout=0.001): pass
                                disable_raw_mode()
                                prog_index = 0
                                chord_name = progression_accords[prog_index]
                                target_notes = self.chord_set[chord_name]
                                live.update(self.create_live_display(chord_name, prog_index, len(progression_accords)), refresh=True)
                                enable_raw_mode()
                                break
                            elif action == 'next':
                                skip_progression = True
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
                                update_chord_success(chord_name)
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
                                update_chord_error(chord_name)
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

        if skip_progression:
            self.console.print("\n[bold yellow]Passage à la progression suivante.[/bold yellow]")
            time.sleep(1)
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

            # Capture the user's choice and return it
            choice = self.wait_for_end_choice()
            if not self.exit_flag:
                clear_screen()
        return choice

    def _generate_progression(self, chord_set):
        """Generates a musically coherent, weighted random progression."""
        # 1. Pick a random key and its diatonic chords
        random_key = random.choice(list(gammes_majeures.keys()))
        diatonic_chords = gammes_majeures[random_key]

        # 2. Get user stats and calculate weights for these chords
        chord_errors = get_chord_errors()
        weights = [1 + (chord_errors.get(chord, 0) ** 2) for chord in diatonic_chords]

        # 3. Generate a weighted random progression from the diatonic chords
        prog_len = random.randint(self.progression_length[0], self.progression_length[1])
        progression_names = weighted_sample_without_replacement(diatonic_chords, weights, k=prog_len)

        # 4. Ensure the generated chords exist in the current chord set
        progression_names = [name for name in progression_names if name in chord_set]

        return progression_names, random_key

    def run(self):
        """Main loop for the chord transitions mode."""
        original_chord_set = self.chord_set

        while not self.exit_flag:
            # Generate a new progression for the outer loop
            progression_names, key_name = self._generate_progression(original_chord_set)

            if len(progression_names) < 2:
                continue

            voicings = self._calculate_best_voicings(progression_names)

            temp_chord_set = {}
            temp_progression_names = []
            for i, (name, voicing) in enumerate(zip(progression_names, voicings)):
                unique_name = f"{name} #{i}"
                temp_progression_names.append(unique_name)
                temp_chord_set[unique_name] = voicing

            # Inner loop for replaying the same progression
            while not self.exit_flag:
                self.chord_set = temp_chord_set

                result = self.run_progression(
                    progression_accords=temp_progression_names,
                    header_title="Passage d'Accords",
                    header_name="Mode Passage d'Accords",
                    border_style="purple",
                    key_name=key_name,
                )

                self.chord_set = original_chord_set

                if result == 'repeat':
                    continue # Repeat the inner loop
                else: # 'continue' or 'quit'
                    break # Break the inner loop

            if self.exit_flag: # Handles the 'q' case
                break

        self.show_overall_stats_and_wait()


def chord_transitions_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    # This mode works best with three_note_chords
    mode_chord_set = three_note_chords
    mode = ChordTransitionsMode(inport, outport, mode_chord_set)
    # These settings are passed from main but might not be used directly in this mode's core logic
    mode.use_timer = use_timer
    mode.timer_duration = timer_duration
    mode.play_progression_before_start = play_progression_before_start
    mode.run()
