# modes/chord_transitions_mode.py
import random
import time
from .chord_mode_base import ChordModeBase
from data.chords import three_note_chords
from music_theory import get_note_name, recognize_chord
from rich.panel import Panel

class ChordTransitionsMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set):
        super().__init__(inport, outport, chord_set)
        self.progression_length = (2, 4)

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

                if cost < min_cost:
                    min_cost = cost
                    best_voicing = shifted_inv

            final_voicings.append(best_voicing)

        return final_voicings

    def create_live_display(self, chord_name, prog_index, total_chords, time_info=""):
        # Override to remove the unique identifier from the chord name for display
        display_name = chord_name.split(" #")[0]
        play_mode = getattr(self, "play_progression_before_start", "NONE")
        if play_mode == 'PLAY_ONLY':
            content = f"Jouez l'accord ({prog_index + 1}/{total_chords})"
        else:
            content = f"Accord à jouer ({prog_index + 1}/{total_chords}): [bold yellow]{display_name}[/bold yellow]"

        if time_info:
            content += f"\n{time_info}"
        return Panel(content, title="Progression en cours", border_style="green")

    def run(self):
        """Main loop for the chord transitions mode."""
        # Store original chord_set and restore it later
        original_chord_set = self.chord_set

        while not self.exit_flag:
            prog_len = random.randint(self.progression_length[0], self.progression_length[1])
            progression_names = random.sample(list(original_chord_set.keys()), prog_len)

            voicings = self._calculate_best_voicings(progression_names)

            # Create a temporary chord set and progression names for run_progression
            temp_chord_set = {}
            temp_progression_names = []
            for i, (name, voicing) in enumerate(zip(progression_names, voicings)):
                unique_name = f"{name} #{i}"
                temp_progression_names.append(unique_name)
                temp_chord_set[unique_name] = voicing

            # Temporarily replace the chord set for run_progression
            self.chord_set = temp_chord_set

            result = self.run_progression(
                progression_accords=temp_progression_names,
                header_title="Passage d'Accords",
                header_name="Mode Passage d'Accords",
                border_style="purple",
            )

            # Restore original chord set
            self.chord_set = original_chord_set

            if result == 'exit':
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
