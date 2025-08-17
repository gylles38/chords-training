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
from music_theory import get_note_name


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

    # --- Progression Generation Methods (unchanged) ---
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
        random_key = random.choice(list(gammes_majeures.keys()))
        diatonic_chords = [c for c in gammes_majeures[random_key] if c in self.chord_set]
        if not diatonic_chords:
            return [], "Progression Diatonique", ""
        prog_len = random.randint(3, 5)
        prog = random.choices(diatonic_chords, k=prog_len)
        return prog, "Progression Diatonique", random_key

    def _get_random_progression(self) -> Optional[Tuple[List[str], str, str]]:
        generation_methods = {
            "Gamme Complète": self._gen_from_all_degrees,
            "Cadences": self._gen_from_cadences,
            "Pop/Rock": self._gen_from_pop_rock,
            "Progression Tonale": self._gen_from_tonal,
            "Progression Diatonique": self._gen_from_transitions,
        }
        source_name = random.choice(list(generation_methods.keys()))
        result = generation_methods[source_name]()
        return result


    # --- Gameplay Methods ---

    def _play_gapped_progression(self, progression_chords: List[str], chord_set: Dict, missing_index: int):
        self.console.print("\nÉcoutez bien la progression ('r' pour réécouter)...")
        time.sleep(1)

        chord_duration = 0.8
        pause_duration = 0.5

        display_prog = []
        for i, chord_name in enumerate(progression_chords):
            if i == missing_index:
                display_prog.append(f"({i+1}) [bold yellow]... ? ...[/bold yellow]")
            else:
                display_prog.append(f"({i+1}) {chord_name.split(' #')[0]}")

        self.console.print(" -> ".join(display_prog))

        for i, chord_name in enumerate(progression_chords):
            if i == missing_index:
                time.sleep(chord_duration + pause_duration)
            else:
                notes = chord_set.get(chord_name)
                if notes:
                    play_chord(self.outport, notes, duration=chord_duration)
                    time.sleep(pause_duration)
        self.console.print()

    def _collect_and_handle_input(self, prog_to_play, chord_set_to_use, missing_index):
        notes_currently_on = set()
        attempt_notes = set()
        last_note_off_time = None

        enable_raw_mode()
        try:
            while not self.exit_flag:
                char = wait_for_input(timeout=0.01)
                if char:
                    if char.lower() == 'r':
                        disable_raw_mode()
                        # Clear screen and replay
                        clear_screen()
                        self.display_header("Trouve l'Accord Manquant", "Mode de Jeu", "bright_cyan")
                        self._play_gapped_progression(prog_to_play, chord_set_to_use, missing_index)
                        self.console.print("Quel était l'accord manquant ?")
                        enable_raw_mode()
                        attempt_notes.clear()
                        notes_currently_on.clear()
                        last_note_off_time = None
                        continue
                    elif char.lower() == 'n':
                        return None, 'next'
                    elif char.lower() == 'q':
                        self.exit_flag = True
                        return None, 'quit'

                for msg in self.inport.iter_pending():
                    if msg.type == 'note_on' and msg.velocity > 0:
                        notes_currently_on.add(msg.note)
                        attempt_notes.add(msg.note)
                        last_note_off_time = None
                    elif msg.type == 'note_off':
                        notes_currently_on.discard(msg.note)
                        if not notes_currently_on:
                            last_note_off_time = time.time()

                if last_note_off_time and (time.time() - last_note_off_time > 0.3):
                     return attempt_notes, 'attempt'

                time.sleep(0.01)
        finally:
            disable_raw_mode()

        return None, 'quit'

    def run(self):
        while not self.exit_flag:
            clear_screen()
            self.display_header(
                "Trouve l'Accord Manquant", "Mode de Jeu", "bright_cyan"
            )
            self.console.print("Je vais jouer une progression avec un accord manquant. À vous de le trouver !")

            progression, source, key = None, "", ""
            while not progression or len(progression) < 3:
                prog_data = self._get_random_progression()
                if prog_data:
                    progression, source, key = prog_data

            voicings, prog_to_play, chord_set_to_use = [], progression, self.chord_set
            if self.use_voice_leading:
                voicings = self._calculate_best_voicings(progression)
                temp_chord_set, temp_prog_names = {}, []
                for i, (name, voicing) in enumerate(zip(progression, voicings)):
                    unique_name = f"{name} #{i}"
                    temp_prog_names.append(unique_name)
                    temp_chord_set[unique_name] = voicing
                prog_to_play, chord_set_to_use = temp_prog_names, temp_chord_set

            missing_index = random.randint(1, len(progression) - 2)
            missing_chord_name = prog_to_play[missing_index]
            missing_chord_notes = chord_set_to_use[missing_chord_name]

            self._play_gapped_progression(prog_to_play, chord_set_to_use, missing_index)
            self.console.print(f"Quel était l'accord manquant à la position {missing_index + 1} ? ('n' pour passer, 'q' pour quitter)")

            wrong_attempts = 0
            last_incorrect_chord = None
            while not self.exit_flag:
                attempt_notes, action = self._collect_and_handle_input(prog_to_play, chord_set_to_use, missing_index)

                if action in ['next', 'quit']:
                    if action == 'next':
                        break
                    else:
                        self.exit_flag = True
                        break

                if action == 'attempt':
                    is_correct, recognized_name, _ = self.check_chord(attempt_notes, missing_chord_name, missing_chord_notes)
                    if is_correct:
                        update_chord_success(missing_chord_name.split(" #")[0])
                        self.console.print(f"\n[bold green]Bravo ![/bold green] C'était bien [bold yellow]{missing_chord_name.split(' #')[0]}[/bold yellow].")
                        break
                    else:
                        wrong_attempts += 1
                        update_chord_error(missing_chord_name.split(" #")[0])

                        if recognized_name and recognized_name == last_incorrect_chord:
                            self.console.print("[bold red]Vous avez joué le même accord. Réessayez ![/bold red]")
                        else:
                            played_chord_str = f"{recognized_name}" if recognized_name else "ce que vous avez joué"
                            self.console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué {played_chord_str}. Réessayez !")

                        last_incorrect_chord = recognized_name

                        # DEBUG: Reveal after 3 attempts
                        if wrong_attempts == 3:
                            base_chord_name = missing_chord_name.split(" #")[0]
                            self.console.print(f"[bold yellow]Indice (Debug) :[/bold yellow] L'accord était [bold cyan]{base_chord_name}[/bold cyan].")
                            play_chord(self.outport, missing_chord_notes, duration=1.5)

            if not self.exit_flag:
                self.console.print("\nAppuyez sur 'n' pour la suite, 'q' pour quitter...")
                enable_raw_mode()
                try:
                    while True:
                        char = wait_for_input()
                        if char and char.lower() == 'n':
                            break
                        if char and char.lower() == 'q':
                            self.exit_flag = True
                            break
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
