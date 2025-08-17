# modes/missing_chord_mode.py
import random
import time
from typing import List, Tuple, Optional, Dict, Any

from rich.panel import Panel
from rich.text import Text

from .chord_mode_base import ChordModeBase
from data.chords import (
    all_chords,
    three_note_chords,
    gammes_majeures,
    cadences,
    tonal_progressions,
    pop_rock_progressions,
    DEGREE_MAP,
)
from stats_manager import get_chord_errors, update_chord_success, update_chord_error
from midi_handler import play_chord
from screen_handler import clear_screen
from keyboard_handler import wait_for_input, enable_raw_mode, disable_raw_mode


class MissingChordMode(ChordModeBase):
    def __init__(
        self,
        inport,
        outport,
        use_timer,
        timer_duration,
        progression_selection_mode,
        play_progression_before_start,
        chord_set,
        use_transitions,
    ):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.progression_selection_mode = progression_selection_mode
        self.play_progression_before_start = play_progression_before_start
        self.use_voice_leading = use_transitions

    # --- Progression Generation Methods ---

    def _gen_from_all_degrees(self) -> Tuple[List[str], str, str]:
        tonalite, gammes = random.choice(list(gammes_majeures.items()))
        prog = [g for g in gammes if g in self.chord_set]
        return prog, "Gamme Complète", tonalite

    def _gen_from_cadences(self) -> Optional[Tuple[List[str], str, str]]:
        valid_cadences = []
        for tonalite, accords_gamme in gammes_majeures.items():
            for nom_cadence, degres in cadences.items():
                try:
                    prog = [accords_gamme[DEGREE_MAP[d]] for d in degres]
                    if all(accord in self.chord_set for accord in prog):
                        valid_cadences.append((prog, nom_cadence, tonalite))
                except (KeyError, IndexError):
                    continue
        if not valid_cadences:
            return None
        return random.choice(valid_cadences)

    def _gen_from_pop_rock(self) -> Tuple[List[str], str, str]:
        key, data = random.choice(list(pop_rock_progressions.items()))
        prog = data["progression"]
        name = f"Pop/Rock: {key}"
        return prog, name, ""

    def _gen_from_tonal(self) -> Optional[Tuple[List[str], str, str]]:
        valid_progs = []
        for tonalite, gammes in gammes_majeures.items():
            gammes_filtrees = [g for g in gammes if g in self.chord_set]
            for prog_name, prog_data in tonal_progressions.items():
                try:
                    prog = [gammes_filtrees[DEGREE_MAP[d]] for d in prog_data["progression"]]
                    valid_progs.append((prog, prog_name, tonalite))
                except (KeyError, IndexError):
                    continue
        if not valid_progs:
            return None
        return random.choice(valid_progs)

    def _gen_from_transitions(self) -> Tuple[List[str], str, str]:
        # This is the same generation logic as the ChordTransitionsMode
        random_key = random.choice(list(gammes_majeures.keys()))
        diatonic_chords = [c for c in gammes_majeures[random_key] if c in self.chord_set]
        if not diatonic_chords:
            return [], "Progression Diatonique", ""
        prog_len = random.randint(3, 5)
        prog = random.choices(diatonic_chords, k=prog_len)
        return prog, "Progression Diatonique", random_key

    def _get_random_progression(self) -> Optional[Tuple[List[str], str, str]]:
        """Selects a source and generates a progression."""
        generation_methods = {
            "Gamme Complète": self._gen_from_all_degrees,
            "Cadences": self._gen_from_cadences,
            "Pop/Rock": self._gen_from_pop_rock,
            "Progression Tonale": self._gen_from_tonal,
            "Progression Diatonique": self._gen_from_transitions,
        }
        # Pick a random source and try to generate a progression
        source_name = random.choice(list(generation_methods.keys()))
        result = generation_methods[source_name]()
        return result

    # --- Gameplay Methods ---

    def _play_gapped_progression(self, progression_chords: List[str], chord_set: Dict, missing_index: int):
        """Plays a progression, leaving a silent gap for the missing chord."""
        self.console.print("\nÉcoutez bien la progression...")
        time.sleep(1)

        chord_duration = 0.8
        pause_duration = 0.5

        for i, chord_name in enumerate(progression_chords):
            if i == missing_index:
                # This is the missing chord, so we just wait
                self.console.print(f"({i+1}) [bold yellow]... ? ...[/bold yellow]", end=" -> " if i < len(progression_chords) - 1 else "\n")
                time.sleep(chord_duration + pause_duration)
            else:
                notes = chord_set.get(chord_name)
                if notes:
                    self.console.print(f"({i+1}) {chord_name.split(' #')[0]}", end=" -> " if i < len(progression_chords) - 1 else "\n")
                    play_chord(self.outport, notes, duration=chord_duration)
                    time.sleep(pause_duration)
        self.console.print()


    def run(self):
        """Main loop for the 'Find the Missing Chord' mode."""
        while not self.exit_flag:
            clear_screen()
            self.display_header(
                "Trouve l'Accord Manquant", "Mode de Jeu", "bright_cyan"
            )
            self.console.print("Je vais jouer une progression avec un accord manquant. À vous de le trouver !")

            # 1. Generate a valid progression
            progression, source, key = None, "", ""
            while not progression or len(progression) < 3:
                prog_data = self._get_random_progression()
                if prog_data:
                    progression, source, key = prog_data

            # 2. Handle voice leading if enabled
            voicings = []
            prog_to_play = progression
            chord_set_to_use = self.chord_set
            original_chord_set = self.chord_set

            if self.use_voice_leading:
                voicings = self._calculate_best_voicings(progression)
                temp_chord_set = {}
                temp_prog_names = []
                for i, (name, voicing) in enumerate(zip(progression, voicings)):
                    unique_name = f"{name} #{i}"
                    temp_prog_names.append(unique_name)
                    temp_chord_set[unique_name] = voicing
                prog_to_play = temp_prog_names
                chord_set_to_use = temp_chord_set

            # 3. Pick a chord to hide (not the first or the last)
            missing_index = random.randint(1, len(progression) - 2)
            missing_chord_name = prog_to_play[missing_index]
            missing_chord_notes = chord_set_to_use[missing_chord_name]

            # 4. Play the gapped progression
            self._play_gapped_progression(prog_to_play, chord_set_to_use, missing_index)

            # 5. Prompt user
            self.console.print(f"Quel était l'accord manquant à la position {missing_index + 1} ?")

            # 6. Get user input and check
            attempt_notes, _ = self.collect_notes()

            if attempt_notes is None: # User quit
                break

            is_correct, recognized_name, _ = self.check_chord(attempt_notes, missing_chord_name, missing_chord_notes)

            # 7. Provide feedback
            if is_correct:
                update_chord_success(missing_chord_name.split(" #")[0])
                self.console.print(f"\n[bold green]Bravo ![/bold green] C'était bien [bold yellow]{missing_chord_name.split(' #')[0]}[/bold yellow].")
            else:
                update_chord_error(missing_chord_name.split(" #")[0])
                played_chord_str = f"{recognized_name}" if recognized_name else "ce que vous avez joué"
                self.console.print(f"\n[bold red]Dommage.[/bold red] Vous avez joué {played_chord_str}, mais l'accord manquant était [bold yellow]{missing_chord_name.split(' #')[0]}[/bold yellow].")
                # Play the correct chord for them
                self.console.print("Le voici :")
                play_chord(self.outport, missing_chord_notes, duration=1.5)

            # 8. Loop or exit
            self.console.print("\nAppuyez sur 'q' pour quitter, ou une autre touche pour continuer...")
            enable_raw_mode()
            try:
                char = wait_for_input()
                if char and char.lower() == 'q':
                    self.exit_flag = True
            finally:
                disable_raw_mode()

        self.show_overall_stats_and_wait()


def missing_chord_mode(
    inport,
    outport,
    use_timer,
    timer_duration,
    progression_selection_mode,
    play_progression_before_start,
    chord_set,
    use_transitions=False,
):
    # This mode works best with three_note_chords, but we'll allow all
    mode = MissingChordMode(
        inport,
        outport,
        use_timer,
        timer_duration,
        progression_selection_mode,
        play_progression_before_start,
        chord_set,
        use_transitions,
    )
    mode.run()
