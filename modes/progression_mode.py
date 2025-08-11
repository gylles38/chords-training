# modes/progression _mode.py
import random
import time

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live

from ui import get_colored_notes_string, display_stats_fixed
from screen_handler import clear_screen
from keyboard_handler import wait_for_input, wait_for_any_key
from midi_handler import play_progression_sequence
from data.chords import all_chords
from music_theory import recognize_chord, is_enharmonic_match_improved, get_chord_type_from_name, get_note_name

console = Console()

def progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    """Mode d'entraînement sur des progressions d'accords."""

    session_correct_count = 0
    session_total_count = 0
    session_total_attempts = 0
    last_progression_accords = []
    
    exit_flag = False
    
    while not exit_flag:
        for _ in inport.iter_pending():
            pass

        clear_screen()
        console.print(Panel(
            Text("Mode Progressions d'Accords", style="bold blue", justify="center"),
            title="Progressions d'Accords",
            border_style="blue"
        ))
        console.print(f"Type d'accords: [bold cyan]{'Tous' if chord_set == all_chords else 'Majeurs/Mineurs'}[/bold cyan]")
        console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer à la suivante.")
        
        prog_len = random.randint(3, 5)
        
        progression = random.sample(list(chord_set.keys()), prog_len)
        while progression == last_progression_accords:
            progression = random.sample(list(chord_set.keys()), prog_len)
        
        last_progression_accords = progression
        
        console.print(f"\nProgression à jouer : [bold yellow]{' -> '.join(progression)}[/bold yellow]")
        
        if play_progression_before_start:
            play_progression_sequence(outport, progression, chord_set)

        progression_correct_count = 0
        progression_total_attempts = 0
        is_progression_started = False
        start_time = None
        elapsed_time = 0.0
        skip_progression = False

        # Fonction pour créer l'affichage live
        def create_live_display(chord_name, prog_index, total_chords, time_info=""):
            content = f"Accord à jouer ({prog_index + 1}/{total_chords}): [bold yellow]{chord_name}[/bold yellow]"
            if time_info:
                content += f"\n{time_info}"
            return Panel(content, title="Progression en cours", border_style="green")

        # Boucle principale avec Live display
        with Live(console=console, screen=False, auto_refresh=False) as live:
            prog_index = 0
            while prog_index < len(progression) and not exit_flag and not skip_progression:
                chord_name = progression[prog_index]
                target_notes = chord_set[chord_name]
                chord_attempts = 0
                
                # Affichage initial
                time_info = ""
                if use_timer and is_progression_started:
                    remaining_time = timer_duration - (time.time() - start_time)
                    time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"
                
                live.update(create_live_display(chord_name, prog_index, len(progression), time_info), refresh=True)
                
                notes_currently_on = set()
                attempt_notes = set()

                # Boucle pour chaque accord
                while not exit_flag and not skip_progression:
                    if use_timer and is_progression_started:
                        remaining_time = timer_duration - (time.time() - start_time)
                        time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"
                        live.update(create_live_display(chord_name, prog_index, len(progression), time_info), refresh=True)
                        
                        if remaining_time <= 0:
                            live.update("[bold red]Temps écoulé ! Session terminée.[/bold red]", refresh=True)
                            time.sleep(2)
                            exit_flag = True
                            break
                        
                    char = wait_for_input(timeout=0.01)
                    if char:
                        char = char.lower()
                        if char == 'q':
                            exit_flag = True
                            break
                        if char == 'r':
                            # Vider le buffer des entrées clavier pour éviter l'accumulation
                            while wait_for_input(timeout=0.001):
                                pass
                            
                            # Afficher le message de lecture et rediriger temporairement TOUS les affichages
                            live.update("[bold cyan]Lecture de la progression...[/bold cyan]", refresh=True)
                            
                            # Sauvegarder les fonctions d'affichage originales
                            original_print = print
                            original_console_print = console.print
                            
                            # Rediriger TOUS les affichages vers des fonctions vides
                            import builtins
                            builtins.print = lambda *args, **kwargs: None
                            console.print = lambda *args, **kwargs: None
                            
                            try:
                                play_progression_sequence(outport, progression, chord_set)
                            finally:
                                # Restaurer les fonctions d'affichage originales
                                builtins.print = original_print
                                console.print = original_console_print
                            
                            # Vider à nouveau le buffer après la lecture
                            while wait_for_input(timeout=0.001):
                                pass
                            
                            # Remettre l'affichage normal après la lecture
                            prog_index = 0
                            chord_name = progression[prog_index]
                            target_notes = chord_set[chord_name]
                            live.update(create_live_display(chord_name, prog_index, len(progression)), refresh=True)
                            break
                        if char == 'n':
                            skip_progression = True
                            break

                    for msg in inport.iter_pending():
                        if msg.type == 'note_on' and msg.velocity > 0:
                            notes_currently_on.add(msg.note)
                            attempt_notes.add(msg.note)
                        elif msg.type == 'note_off':
                            notes_currently_on.discard(msg.note)

                    if not notes_currently_on and attempt_notes:
                        chord_attempts += 1
                        progression_total_attempts += 1
                        
                        if use_timer and not is_progression_started:
                            is_progression_started = True
                            start_time = time.time()

                        try:
                            recognized_name, recognized_inversion = recognize_chord(attempt_notes)
                            
                            is_correct = (recognized_name and 
                                        is_enharmonic_match_improved(recognized_name, chord_name, chord_set) and 
                                        len(attempt_notes) == len(chord_set[chord_name]))
                            
                            if is_correct:
                                # Afficher le succès avec les notes jouées
                                colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                                success_msg = f"[bold green]Correct ! {chord_name}[/bold green]\nNotes jouées : [{colored_notes}]"
                                live.update(success_msg, refresh=True)
                                time.sleep(2)
                                
                                if chord_attempts == 1:
                                    progression_correct_count += 1
                                
                                prog_index += 1
                                break
                            else:
                                # Afficher l'erreur avec les notes jouées
                                colored_string = get_colored_notes_string(attempt_notes, target_notes)
                                error_msg = f"[bold red]Incorrect.[/bold red] Vous avez joué : {recognized_name if recognized_name else 'Accord non reconnu'}\nNotes jouées : [{colored_string}]"
                                live.update(error_msg, refresh=True)
                                time.sleep(2)
                                
                                # Remettre l'affichage normal
                                live.update(create_live_display(chord_name, prog_index, len(progression)), refresh=True)
                                attempt_notes.clear()

                        except Exception as e:
                            print(f"ERREUR dans progression_mode: {e}")
                            attempt_notes.clear()
                    
                    time.sleep(0.01)
                
                if exit_flag:
                    break
            
        if not exit_flag and not skip_progression:
            session_correct_count += progression_correct_count
            session_total_attempts += progression_total_attempts
            session_total_count += len(progression)
            
            console.print(f"\n--- Statistiques de cette progression ---")
            console.print(f"Accords à jouer : [bold cyan]{len(progression)}[/bold cyan]")
            console.print(f"Tentatives totales : [bold yellow]{progression_total_attempts}[/bold yellow]")
            console.print(f"Réussis du premier coup : [bold green]{progression_correct_count}[/bold green]")
            
            if progression_total_attempts > 0:
                accuracy = (progression_correct_count / progression_total_attempts) * 100
                console.print(f"Précision : [bold cyan]{accuracy:.1f}%[/bold cyan]")
            
            if use_timer and is_progression_started:
                end_time = time.time()
                elapsed_time = end_time - start_time
                console.print(f"\nTemps pour la progression : [bold cyan]{elapsed_time:.2f} secondes[/bold cyan]")
            
            choice = Prompt.ask("\nProgression terminée ! Appuyez sur Entrée pour la suivante ou 'q' pour revenir au menu principal...", console=console, choices=["", "q"], show_choices=False)
            if choice == 'q':
                exit_flag = True
                break
            clear_screen()

        elif skip_progression:
            console.print("\n[bold yellow]Passage à la progression suivante.[/bold yellow]")
            time.sleep(1)

    if use_timer:
        display_stats_fixed(session_correct_count, session_total_attempts, session_total_count, elapsed_time)
    else:
        display_stats_fixed(session_correct_count, session_total_attempts, session_total_count)
        
    console.print("\nAppuyez sur Entrée pour retourner au menu principal.")
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)
