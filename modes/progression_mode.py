# modes/progression_mode.py
import time
import random

from rich.live import Live
from rich.prompt import Prompt
from rich.panel import Panel

from .chord_mode_base import ChordModeBase

from midi_handler import play_progression_sequence
from ui import get_colored_notes_string, display_stats_fixed
from screen_handler import clear_screen
from keyboard_handler import wait_for_any_key, wait_for_input, enable_raw_mode, disable_raw_mode

class ProgressionMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.progression_selection_mode = progression_selection_mode  # Not used in provided code, kept for completeness
        self.play_progression_before_start = play_progression_before_start
        self.session_correct_count = 0
        self.session_total_count = 0
        self.session_total_attempts = 0
        self.elapsed_time = 0.0

    # La gestion de la lecture du clavier est confiée à la classe mère ChordModBase.handle_keyboard_input (n,r,q)
    # La méthode _handle_custom_input est redéfinie pour gérer 'p' (pause) par exemple
    #def _handle_custom_input(self, char):
    #    if char and char.lower() == 'p':
    #        return 'pause'
    #    return False

    def run(self):
        last_progression = []
        while not self.exit_flag:
            self.clear_midi_buffer()
            self.display_header("Progressions d'Accords", "Mode Progressions d'Accords", "blue")
            self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer à la suivante.")

            prog_len = random.randint(3, 5)
            progression_accords = random.sample(list(self.chord_set.keys()), prog_len)
            while progression_accords == last_progression:
                progression_accords = random.sample(list(self.chord_set.keys()), prog_len)
            last_progression = progression_accords

            self.console.print(f"\nProgression à jouer : [bold yellow]{' -> '.join(progression_accords)}[/bold yellow]")

            if self.play_progression_before_start:
                play_progression_sequence(self.outport, progression_accords, self.chord_set)

            # Traitement de la progression
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
                    if self.use_timer and is_progression_started:
                        remaining_time = self.timer_duration - (time.time() - start_time)
                        time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"

                    live.update(self.create_live_display(chord_name, prog_index, len(progression_accords), time_info), refresh=True)

                    notes_currently_on = set()
                    attempt_notes = set()

                    # Activer le mode raw seulement pour cette boucle d'interaction
                    enable_raw_mode()
                    try:
                        while not self.exit_flag and not skip_progression:
                            if self.use_timer and is_progression_started:
                                remaining_time = self.timer_duration - (time.time() - start_time)
                                time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"
                                # Désactiver/réactiver le mode raw pour l'update
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
                                    # Vider le buffer clavier
                                    while wait_for_input(timeout=0.001):
                                        pass
                                    
                                    # Désactiver le mode raw pour les updates
                                    disable_raw_mode()
                                    live.update("[bold cyan]Lecture de la progression...[/bold cyan]", refresh=True)
                                    play_progression_sequence(self.outport, progression_accords, self.chord_set)
                                    
                                    # Vider le buffer après la lecture
                                    enable_raw_mode()
                                    while wait_for_input(timeout=0.001):
                                        pass
                                    disable_raw_mode()
                                    
                                    # Revenir au premier accord
                                    prog_index = 0
                                    chord_name = progression_accords[prog_index]
                                    target_notes = self.chord_set[chord_name]
                                    live.update(self.create_live_display(chord_name, prog_index, len(progression_accords)), refresh=True)
                                    enable_raw_mode()
                                    break
                                elif action == 'next':
                                    skip_progression = True
                                    break
                                elif action is True:  # 'q' pressed
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

                                if self.use_timer and not is_progression_started:
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
                    break

            if not self.exit_flag and not skip_progression:
                # Si la progression n'est pas sautée, afficher les statistiques
                self.session_correct_count += progression_correct_count
                self.session_total_attempts += progression_total_attempts
                self.session_total_count += len(progression_accords)

                self.console.print(f"\n--- Statistiques de cette progression ---")
                self.console.print(f"Accords à jouer : [bold cyan]{len(progression_accords)}[/bold cyan]")
                self.console.print(f"Tentatives totales : [bold yellow]{progression_total_attempts}[/bold yellow]")
                self.console.print(f"Réussis du premier coup : [bold green]{progression_correct_count}[/bold green]")

                if progression_total_attempts > 0:
                    accuracy = (progression_correct_count / progression_total_attempts) * 100
                    self.console.print(f"Précision : [bold cyan]{accuracy:.1f}%[/bold cyan]")

                if self.use_timer and is_progression_started:
                    end_time = time.time()
                    self.elapsed_time = end_time - start_time
                    self.console.print(f"\nTemps pour la progression : [bold cyan]{self.elapsed_time:.2f} secondes[/bold cyan]")

                # Utiliser la nouvelle méthode pour la saisie instantanée
                self.wait_for_end_choice()
                if not self.exit_flag:
                    clear_screen()

            elif skip_progression:
                self.console.print("\n[bold yellow]Passage à la progression suivante.[/bold yellow]")
                time.sleep(1)

        if self.use_timer:
            display_stats_fixed(self.session_correct_count, self.session_total_attempts, self.session_total_count, self.elapsed_time)
        else:
            self.console.print("\nAffichage des statistiques.")            
            display_stats_fixed(self.session_correct_count, self.session_total_attempts, self.session_total_count)

        self.console.print("\nAppuyez sur une touche pour retourner au menu principal.")
        self.clear_midi_buffer()
        wait_for_any_key(self.inport)

def progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    mode = ProgressionMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set)
    mode.run()