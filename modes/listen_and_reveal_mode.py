# modes/listen_and_reveal_mode.py
import random
import time

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.prompt import Prompt

from ui import get_colored_notes_string, display_stats
from screen_handler import clear_screen
from keyboard_handler import wait_for_input, wait_for_any_key
from midi_handler import play_chord
from data.chords import all_chords
from music_theory import recognize_chord, is_enharmonic_match_improved, get_chord_type_from_name, get_note_name

console = Console()

def listen_and_reveal_mode(inport, outport, chord_set):
    """
    Mode Écoute et Devine : joue un accord, l'utilisateur doit le reproduire.
    Des indices sont donnés après plusieurs essais.
    """
    
    correct_count = 0
    total_attempts = 0
    
    exit_flag = False
    
    while not exit_flag:
        # Vider le tampon MIDI
        for _ in inport.iter_pending():
            pass
        
        clear_screen()
        console.print(Panel(
            Text("Mode Écoute et Devine", style="bold orange3", justify="center"),
            title="Écoute et Devine",
            border_style="orange3"
        ))
        console.print(f"Type d'accords: [bold cyan]{'Tous' if chord_set == all_chords else 'Majeurs/Mineurs'}[/bold cyan]")
        console.print("Écoutez l'accord joué et essayez de le reproduire.")
        console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter l'accord.")

        chord_name, chord_notes = random.choice(list(chord_set.items()))
        console.print(f"\n[bold yellow]Lecture de l'accord...[/bold yellow]")
        play_chord(outport, chord_notes)
        console.print("Jouez l'accord que vous venez d'entendre.")

        # --- Début de la nouvelle logique pour la détection des arpèges ---
        notes_currently_on = set()
        attempt_notes = set()

        incorrect_attempts = 0
        last_note_off_time = None
        
        while not exit_flag:
            char = wait_for_input(timeout=0.01)
            if char:
                if char.lower() == 'q':
                    exit_flag = True
                    break
                if char.lower() == 'r':
                    console.print(f"[bold blue]Répétition de l'accord...[/bold blue]")
                    play_chord(outport, chord_notes)
                    continue

            for msg in inport.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    notes_currently_on.add(msg.note)
                    attempt_notes.add(msg.note)
                    last_note_off_time = None  # Annuler le timer si une nouvelle note est jouée
                elif msg.type == 'note_off':
                    notes_currently_on.discard(msg.note)
                    # Si toutes les notes sont relâchées, démarrer le timer de vérification
                    if not notes_currently_on and not last_note_off_time:
                        last_note_off_time = time.time()
            
            # Vérifier si le timer s'est écoulé
            if last_note_off_time and time.time() - last_note_off_time > 0.3: # Délai de 0.3 seconde
                total_attempts += 1
                
                # Vérification de l'accord joué par l'utilisateur avec gestion d'erreur
                try:
                    recognized_name, recognized_inversion = recognize_chord(attempt_notes)

                    # Vérifier la correspondance avec la fonction améliorée
                    is_correct = (recognized_name and 
                                is_enharmonic_match_improved(recognized_name, chord_name, chord_set) and 
                                len(attempt_notes) == len(chord_notes))
                    
                    if is_correct:
                        colored_notes = get_colored_notes_string(attempt_notes, chord_notes)
                        console.print(f"Notes jouées : [{colored_notes}]")
                        console.print(f"[bold green]Correct ! C'était bien {chord_name}.[/bold green]")
                        correct_count += 1
                        
                        time.sleep(1.5)
                        break
                    else:
                        incorrect_attempts += 1
                        colored_string = get_colored_notes_string(attempt_notes, chord_notes)
                        
                        if recognized_name:
                            # Nettoyer les noms pour éviter les conflits de formatage
                            clean_chord_name = str(recognized_name).replace('%', 'pct').replace('{', '(').replace('}', ')')
                            clean_inversion = str(recognized_inversion) if recognized_inversion else "position inconnue"
                            clean_inversion = clean_inversion.replace('%', 'pct').replace('{', '(').replace('}', ')')
                            
                            console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {clean_chord_name} ({clean_inversion})")
                        else:
                            console.print("[bold red]Incorrect. Réessayez.[/bold red]")
                        
                        console.print(f"Notes jouées : [{colored_string}]")
                        attempt_notes.clear() # Réinitialiser pour le prochain essai
                        
                        if incorrect_attempts >= 3:
                            tonic_note = sorted(list(chord_notes))[0]
                            tonic_name = get_note_name(tonic_note)
                            console.print(f"Indice : La tonique est [bold cyan]{tonic_name}[/bold cyan].")
                        if incorrect_attempts >= 7:
                            revealed_type = get_chord_type_from_name(chord_name)
                            console.print(f"Indice : C'est un accord de type [bold yellow]{revealed_type}[/bold yellow].")
                            console.print(f"[bold magenta]La réponse était : {chord_name}[/bold magenta]")
                            Prompt.ask("\nAppuyez sur Entrée pour continuer...", console=console)
                            break
                
                except Exception as e:
                    # Debug en cas d'erreur persistante
                    console.print(f"[bold red]Une erreur s'est produite lors de la reconnaissance : {e}[/bold red]")
                    console.print(f"Notes jouées : {list(attempt_notes)}")
                    console.print("Réessayez...")
                    attempt_notes.clear()
                
                # Réinitialiser pour le prochain essai après vérification
                last_note_off_time = None
            
            time.sleep(0.01)

    display_stats(correct_count, total_attempts)
    console.print("\nAppuyez sur une touche pour retourner au menu principal.")
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)

