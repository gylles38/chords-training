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
from music_theory import get_note_name, get_note_name_with_octave


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
        prog, name, key = random.choice(valid_cadences)
        return prog, "Cadences", name

    def _gen_from_pop_rock(self) -> Tuple[List[str], str, str]:
        key, data = random.choice(list(pop_rock_progressions.items()))
        prog = data["progression"]
        return prog, "Pop/Rock", key

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
        prog, name, key = random.choice(valid_progs)
        return prog, "Progression Tonale", name

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
        if result:
            prog, detail, key = result
            return prog, source_name, detail
        return None

    # --- Gameplay Methods ---

    def _get_progression_commentary(self, source_type: str, source_detail: str) -> str:
        comment = ""
        if source_type == "Gamme Complète":
            comment = "Jouer tous les accords d'une gamme est un excellent moyen de s'imprégner de sa couleur et de sa sonorité. C'est la base de la composition dans une tonalité donnée."
        elif source_type == "Cadences":
            if source_detail == "Cadence Parfaite":
                comment = "La cadence parfaite (V-I) est la plus conclusive en musique tonale. Elle donne un sentiment de résolution et de fin très fort, un peu comme un point à la fin d'une phrase."
            elif source_detail == "Cadence Plagale":
                comment = "La cadence plagale (IV-I), souvent appelée 'Amen Cadence', a une sonorité plus douce et moins conclusive que la cadence parfaite. Elle apporte une sensation de tranquillité et de solennité."
            elif source_detail == "Demi-Cadence":
                comment = "La demi-cadence se termine sur l'accord de dominante (V) et laisse une sensation de suspension, d'attente. C'est comme une virgule dans une phrase musicale, elle appelle une suite."
            elif source_detail == "Progression II-V-I":
                comment = "La progression II-V-I est la pierre angulaire de l'harmonie jazz. Elle crée une forte tension (II-V) puis une résolution satisfaisante (V-I)."
            else:
                 comment = "Les cadences sont des enchaînements d'accords qui ponctuent le discours musical, créant des effets de tension et de résolution."
        elif source_type == "Pop/Rock":
            comment = pop_rock_progressions.get(source_detail, {}).get("commentary", "")
        elif source_type == "Progression Tonale":
            comment = tonal_progressions.get(source_detail, {}).get("description", "")
        elif source_type == "Progression Diatonique":
            comment = "Voilà une progression d'accords très courante en musique tonale. L'enchaînement d'accords appartenant à la même gamme crée une sonorité cohérente et agréable."

        return f"\n[italic]{comment}[/italic]" if comment else ""


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

    def _play_full_progression(self, progression_chords: List[str], chord_set: Dict):
        self.console.print("\nVoici la progression complète :")
        time.sleep(1)

        chord_duration = 0.8
        pause_duration = 0.5

        display_prog = [f"({i+1}) {name.split(' #')[0]}" for i, name in enumerate(progression_chords)]
        self.console.print(f"[bold yellow]{' -> '.join(display_prog)}[/bold yellow]")

        for chord_name in progression_chords:
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

            progression, source_type, source_detail = None, "", ""
            while not progression or len(progression) < 3:
                prog_data = self._get_random_progression()
                if prog_data:
                    progression, source_type, source_detail = prog_data

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
            prog_to_play_with_answer = list(prog_to_play)

            self._play_gapped_progression(prog_to_play, chord_set_to_use, missing_index)
            self.console.print(f"Quel était l'accord manquant à la position {missing_index + 1} ? ('n' pour passer, 'q' pour quitter)")

            wrong_attempts = 0
            last_incorrect_chord = None
            while not self.exit_flag:
                attempt_notes, action = self._collect_and_handle_input(prog_to_play, chord_set_to_use, missing_index)

                if action in ['next', 'quit']:
                    if action == 'next': break
                    else: self.exit_flag = True; break

                if action == 'attempt':
                    is_correct, recognized_name, _ = self.check_chord(attempt_notes, missing_chord_name, missing_chord_notes)
                    if is_correct:
                        update_chord_success(missing_chord_name.split(" #")[0])

                        success_message = f"\n[bold green]Bravo ![/bold green] C'était bien [bold yellow]{missing_chord_name.split(' #')[0]}[/bold yellow]."

                        if not self.use_voice_leading and attempt_notes != missing_chord_notes:
                            target_notes_str = ", ".join(sorted([get_note_name_with_octave(n) for n in missing_chord_notes]))
                            played_notes_str = ", ".join(sorted([get_note_name_with_octave(n) for n in attempt_notes]))
                            success_message += f"\n  - Attendu : [cyan]({target_notes_str})[/cyan]"
                            success_message += f"\n  - Joué    : [green]({played_notes_str})[/green]"

                        self.console.print(success_message)

                        user_chord_name = f"{recognized_name} #user"
                        chord_set_to_use[user_chord_name] = attempt_notes
                        prog_to_play_with_answer[missing_index] = user_chord_name

                        self._play_full_progression(prog_to_play_with_answer, chord_set_to_use)

                        commentary = self._get_progression_commentary(source_type, source_detail)
                        if commentary:
                            self.console.print(commentary)

                        break
                    else:
                        wrong_attempts += 1
                        update_chord_error(missing_chord_name.split(" #")[0])

                        if recognized_name:
                            if recognized_name == last_incorrect_chord:
                                self.console.print("[bold red]Vous avez joué le même accord incorrect. Réessayez ![/bold red]")
                            else:
                                self.console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué {recognized_name}. Réessayez !")
                            last_incorrect_chord = recognized_name
                        else:
                            self.console.print("[bold red]Incorrect.[/bold red] L'accord joué n'a pas été reconnu. Réessayez !")
                            last_incorrect_chord = None

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
                        if char and char.lower() == 'n': break
                        if char and char.lower() == 'q': self.exit_flag = True; break
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
