# modes/single_chord_mode.py
import random
import time

from rich.console import Console
from rich.text import Text
from rich.panel import Panel

from ui import get_colored_notes_string, display_stats
from screen_handler import clear_screen
from keyboard_handler import wait_for_input, wait_for_any_key
from data.chords import all_chords
from music_theory import recognize_chord, is_enharmonic_match_improved

console = Console()

def single_chord_mode(inport, outport, chord_set):
    """Mode Accord Simple. 
    L'utilisateur doit jouer le bon accord pour passer au suivant.
    """
    clear_screen()
    console.print(Panel(
        Text("Mode Accords Simples", style="bold yellow", justify="center"),
        title="Accords Simples",
        border_style="yellow"
    ))
    console.print(f"Type d'accords: [bold cyan]{'Tous' if chord_set == all_chords else 'Majeurs/Mineurs'}[/bold cyan]")
    console.print("Jouez l'accord affiché. Appuyez sur 'q' pour quitter.")
    
    correct_count = 0
    total_count = 0
    last_chord_name = None
    exit_flag = False
    
    while not exit_flag:
        # Vider le tampon MIDI
        for _ in inport.iter_pending():
            pass

        # Choisir un nouvel accord différent du précédent
        chord_name, chord_notes = random.choice(list(chord_set.items()))
        while chord_name == last_chord_name:
            chord_name, chord_notes = random.choice(list(chord_set.items()))
        last_chord_name = chord_name
        
        # Effacer l'écran pour le nouvel accord
        clear_screen()
        console.print(Panel(
            Text("Mode Accords Simples", style="bold yellow", justify="center"),
            title="Accords Simples",
            border_style="yellow"
        ))
        console.print(f"Type d'accords: [bold cyan]{'Tous' if chord_set == all_chords else 'Majeurs/Mineurs'}[/bold cyan]")
        console.print("Jouez l'accord affiché. Appuyez sur 'q' pour quitter.")
        console.print(f"\nJouez : [bold bright_yellow]{chord_name}[/bold bright_yellow]")

        notes_currently_on = set()
        attempt_notes = set()
        
        while not exit_flag:
            char = wait_for_input(timeout=0.01)
            if char and char.lower() == 'q':
                exit_flag = True
                break
            
            for msg in inport.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    notes_currently_on.add(msg.note)
                    attempt_notes.add(msg.note)
                elif msg.type == 'note_off':
                    notes_currently_on.discard(msg.note)
            
            # Un accord a été joué et toutes les notes ont été relâchées
            if not notes_currently_on and attempt_notes:
                recognized_name, recognized_inversion = recognize_chord(attempt_notes)
                
                if recognized_name and is_enharmonic_match_improved(recognized_name, chord_name, all_chords) \
                   and len(attempt_notes) == len(chord_notes):
                    colored_notes = get_colored_notes_string(attempt_notes, chord_notes)
                    console.print(f"Notes jouées : [{colored_notes}]")
                    console.print("[bold green]Correct ![/bold green]")
                    correct_count += 1
                    total_count += 1
                    time.sleep(2)  # Pause avant le prochain accord
                    break
                else:
                    colored_string = get_colored_notes_string(attempt_notes, chord_notes)
                    found_chord, found_inversion = recognize_chord(attempt_notes)
                    
                    if found_chord:
                        console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {found_chord} ({found_inversion})")
                    else:
                        console.print("[bold red]Incorrect. Réessayez.[/bold red]")

                    console.print(f"Notes jouées : [{colored_string}]")
                    total_count += 1
                    attempt_notes.clear()  # Réinitialiser pour le prochain essai
                    
            time.sleep(0.01)
        
    # Affichage des statistiques de la session
    display_stats(correct_count, total_count)
    console.print("\nAppuyez sur une touche pour retourner au menu principal.")
    # Vider le tampon MIDI avant d'attendre la touche
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)
