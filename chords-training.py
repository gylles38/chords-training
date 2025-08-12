# coding=utf-8
import mido
import time
import random
import os
import sys

# Importation des bibliothèques spécifiques à la plateforme pour la saisie non-bloquante
try:
    import msvcrt
except ImportError:
    # Pour les systèmes Unix (Linux, macOS)
    import select
    import tty
    import termios

# Importation de Rich pour une meilleure présentation de la console
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table
from rich.errors import MarkupError
from rich.live import Live

from data.chords import all_chords, chord_aliases, enharmonic_map, three_note_chords, gammes_majeures, cadences, DEGREE_MAP, progression_examples, pop_rock_progressions, tonal_progressions
from ui import get_colored_notes_string, display_stats, display_stats_fixed
from midi_handler import *
from screen_handler import clear_screen

from modes.single_chord_mode import single_chord_mode
from modes.listen_and_reveal_mode import listen_and_reveal_mode
from modes.progression_mode import progression_mode
from modes.degrees_mode import degrees_mode
from modes.all_degrees_mode import all_degrees_mode
from modes.cadence_mode import cadence_mode

#TODO : voir si supprimable une fois tout refactorisé
console = Console()

# TODO : commenté pas utilisé à supprimer ?
# --- Création d'un dictionnaire de correspondance pour la reconnaissance par classe de hauteur ---
# Cette structure est générée une seule fois au début du programme.
# La clé est un frozenset des classes de hauteur de l'accord, et la valeur est le nom de l'accord.
#pitch_class_lookup = {}
#for chord_name, notes_set in all_chords.items():
#    pitch_classes = frozenset(note % 12 for note in notes_set)
#    # Gérer les cas d'accords enharmoniques qui ont la même structure de notes.
#    # Ex: Mi Majeur et Fa bémol Majeur. La première occurrence dans la liste sera gardée.
#    if pitch_classes not in pitch_class_lookup:
#        pitch_class_lookup[pitch_classes] = chord_name

# --- Fonctions utilitaires ---

def safe_format_chord_info(chord_name, inversion):
    """Formate de manière sécurisée les informations d'accord"""
    if not chord_name:
        return "Accord non reconnu"
    
    # Nettoyer les caractères problématiques
    safe_name = str(chord_name).replace('%', 'pct').replace('{', '(').replace('}', ')')
    safe_inversion = str(inversion) if inversion else "position inconnue"
    safe_inversion = safe_inversion.replace('%', 'pct').replace('{', '(').replace('}', ')')
    
    return f"{safe_name} ({safe_inversion})"

def reverse_chord_mode(inport):
    """
    Mode de reconnaissance d'accords joués par l'utilisateur.
    Reconnaît les accords en position fondamentale et leurs renversements
    de manière indépendante de l'octave.
    """
    clear_screen()
    console.print(Panel(
        Text("Mode Reconnaissance d'accords (Tous les accords)", style="bold cyan", justify="center"),
        title="Reconnaissance d'accords",
        border_style="cyan"
    ))
    console.print("Jouez un accord sur votre clavier MIDI.")
    console.print("Appuyez sur 'q' pour quitter.")
    console.print("\nCe mode reconnaît les accords à 3 ou 4 notes en position fondamentale ainsi qu'en 1er et 2ème (et 3ème) renversement, quelle que soit l'octave.")
    console.print("---")

    notes_currently_on = set()
    attempt_notes = set()

    while True:
        char = wait_for_input(timeout=0.01)
        if char and char.lower() == 'q':
            break

        for msg in inport.iter_pending():
            if msg.type == 'note_on' and msg.velocity > 0:
                notes_currently_on.add(msg.note)
                attempt_notes.add(msg.note)
            elif msg.type == 'note_off':
                notes_currently_on.discard(msg.note)

        # Vérifier si un accord a été joué et relâché
        if not notes_currently_on and attempt_notes:
            if len(attempt_notes) > 1:
                chord_name, inversion_label = recognize_chord(attempt_notes)
                
                if chord_name:
                    enharmonic_name = enharmonic_map.get(chord_name)
                    if enharmonic_name:
                        console.print(f"Accord reconnu : [bold green]{chord_name}[/bold green] ou [bold green]{enharmonic_name}[/bold green] ({inversion_label})")
                    else:
                        console.print(f"Accord reconnu : [bold green]{chord_name}[/bold green] ({inversion_label})")
                else:
                    # Bug fix: utiliser la fonction de coloration corrigée pour ce mode également
                    # Pour ce mode, il n'y a pas d'accord "cible" à comparer. On affiche juste
                    # les notes jouées. On peut donc simplement lister les notes.
                    colored_string = ", ".join([f"[bold red]{get_note_name(n)}[/bold red]" for n in sorted(list(attempt_notes))])
                    console.print(f"[bold red]Accord non reconnu.[/bold red] Notes jouées : [{colored_string}]")
            else:
                console.print("[bold yellow]Veuillez jouer au moins 3 notes pour former un accord.[/bold yellow]")

            attempt_notes.clear()
        
        time.sleep(0.01)

# --- Modes de jeu ---

# NOUVEAU: Mode Explorateur d'Accords
def chord_explorer_mode(outport):
    """Mode dictionnaire : l'utilisateur saisit un nom d'accord, le programme le joue et affiche ses notes."""
    clear_screen()
    console.print(Panel(
        Text("Mode Explorateur d'Accords", style="bold bright_blue", justify="center"),
        title="Dictionnaire d'accords",
        border_style="bright_blue"
    ))
    console.print("Entrez un nom d'accord pour voir ses notes et l'entendre.")
    console.print("Exemples : [cyan]C, F#m, Gm7, Bb, Ddim[/cyan]")

    while True:
        try:
            user_input = Prompt.ask("\n[prompt.label]Accord à trouver (ou 'q' pour quitter)[/prompt.label]")
            if user_input.lower() == 'q':
                break

            # Normaliser la saisie pour la recherche (minuscules, sans espaces)
            lookup_key = user_input.lower().replace(" ", "")
            full_chord_name = chord_aliases.get(lookup_key)

            if full_chord_name and full_chord_name in all_chords:
                # Accord trouvé
                chord_notes_midi = all_chords[full_chord_name]
                
                # Trier les notes pour un affichage logique (Tonique, Tierce, Quinte...)
                sorted_notes_midi = sorted(list(chord_notes_midi))
                
                # Obtenir le nom des notes
                note_names = [get_note_name(n) for n in sorted_notes_midi]
                notes_str = ", ".join(note_names)

                console.print(f"L'accord [bold green]{full_chord_name}[/bold green] est composé des notes : [bold yellow]{notes_str}[/bold yellow]")
                console.print("Lecture de l'accord...")
                play_chord(outport, chord_notes_midi, duration=1.2) # Joue l'accord un peu plus longtemps
            else:
                # Accord non trouvé
                console.print(f"[bold red]Accord '{user_input}' non reconnu.[/bold red] Veuillez réessayer.")

        except Exception as e:
            console.print(f"[bold red]Une erreur est survenue : {e}[/bold red]")
            time.sleep(2)

    console.print("\nRetour au menu principal.")
    time.sleep(1)

def pop_rock_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set):
    """
    Mode d'entraînement Pop/Rock avec des progressions d'accords courantes.
    Permet de jouer plusieurs progressions à la suite.
    """
    # Boucle principale pour permettre de jouer plusieurs progressions.
    while True:
        clear_screen()
        console.print(Panel(
            Text("Mode Pop/Rock", style="bold cyan", justify="center"),
            title="Entraînement Pop/Rock", border_style="cyan"
        ))

        # Afficher les progressions et les exemples
        table = Table(title="Progressions Pop/Rock", style="bold blue")
        table.add_column("Numéro", style="cyan")
        table.add_column("Progression", style="magenta")
        table.add_column("Exemples de chansons", style="yellow")

        for num, data in pop_rock_progressions.items():
            prog_str = " -> ".join(data["progression"])
            examples_str = "\n".join(data["examples"])
            table.add_row(num, prog_str, examples_str)
        console.print(table)

        # Demander à l'utilisateur de choisir une progression ou de quitter
        prog_choices = list(pop_rock_progressions.keys())
        prog_choice = Prompt.ask("Choisissez une progression (numéro) ou entrez 'q' pour retourner au menu", choices=prog_choices + ['q'])

        if prog_choice.lower() == 'q':
            break  # Quitte la boucle principale du mode

        selected_progression_data = pop_rock_progressions.get(prog_choice)
        current_progression = selected_progression_data["progression"]

        prog_str = " -> ".join(current_progression)
        console.print(f"\nProgression sélectionnée: [bold yellow]{prog_str}[/bold yellow]")

        if play_progression_before_start:
            play_progression_sequence(outport, current_progression, all_chords)

        notes_currently_on = set()
        attempt_notes = set()
        start_time = None
        user_quit_in_game = False

        console.print("\n[bold green]La progression commence. Jouez l'accord affiché.[/bold green]")

        def update_live_display(time_elapsed, progression_index, current_progression):
            panel_content = Text(
                f"Accord à jouer : [bold yellow]{current_progression[progression_index]}[/bold yellow]\n"
                f"Temps écoulé : [bold magenta]{time_elapsed:.1f}s[/bold magenta]",
                justify="center"
            )
            return Panel(panel_content, title="Progression en cours", border_style="green")

        with Live(console=console, screen=False, auto_refresh=False) as live:
            progression_index = 0
            while progression_index < len(current_progression):
                if use_timer:
                    if start_time is None:
                        start_time = time.time()
                    time_elapsed = time.time() - start_time
                    live.update(update_live_display(time_elapsed, progression_index, current_progression), refresh=True)

                    if time_elapsed > timer_duration:
                        live.stop()
                        console.print(f"[bold red]\nTemps écoulé ! L'accord était {current_progression[progression_index]}.[/bold red]")
                        progression_index += 1
                        start_time = None
                        if progression_index < len(current_progression):
                            console.print(f"Passage à l'accord suivant : [bold yellow]{current_progression[progression_index]}[/bold yellow]")
                        live.start()
                else:
                    live.update(Panel(f"Accord à jouer : [bold yellow]{current_progression[progression_index]}[/bold yellow]", title="Progression en cours", border_style="green"), refresh=True)
                
                for msg in inport.iter_pending():
                    if msg.type == 'note_on' and msg.velocity > 0:
                        notes_currently_on.add(msg.note)
                        attempt_notes.add(msg.note)
                    elif msg.type == 'note_off':
                        notes_currently_on.discard(msg.note)

                if not notes_currently_on and attempt_notes:
                    played_chord_name, _ = recognize_chord(attempt_notes)
                    target_chord_name = current_progression[progression_index]

                    if played_chord_name and (is_enharmonic_match_improved(played_chord_name, target_chord_name, enharmonic_map) or played_chord_name == target_chord_name):
                        live.update(f"[bold green]Correct ! {target_chord_name}[/bold green]", refresh=True)
                        time.sleep(1) # Pause pour voir le message
                        progression_index += 1
                        start_time = None
                        if progression_index >= len(current_progression):
                            break
                    else:
                        live.update(f"[bold red]Incorrect.[/bold red] Vous avez joué : {played_chord_name if played_chord_name else 'Accord non reconnu'}", refresh=True)
                        time.sleep(1) # Pause pour voir le message
                    
                    attempt_notes.clear()
                
                char = wait_for_input(timeout=0.01)
                if char and char.lower() == 'q':
                    user_quit_in_game = True
                    break
                
                time.sleep(0.01)

        if user_quit_in_game:
            break # Quitte la boucle principale du mode

        # Ce message s'affiche uniquement si la progression est terminée.
        console.print("[bold green]Progression terminée ![/bold green]")
        
        # Nouveau comportement simplifié
        choice = Prompt.ask(
            "\nProgression terminée ! Appuyez sur Entrée pour choisir une autre progression ou 'q' pour revenir au menu principal...", 
            console=console, 
            choices=["", "q"], 
            show_choices=False
        )
        if choice == 'q':
            break # Quitte la boucle principale du mode

    # Message de sortie du mode
    console.print("\nFin du mode Progression Pop/Rock.")
    console.print("Appuyez sur une touche pour revenir au menu principal.")
    wait_for_any_key(inport)

def tonal_progression_mode(inport, outport, chord_set):
    """Mode qui joue une progression d'accords puis demande à l'utilisateur de la rejouer."""
    current_tonalite = None
    current_progression_name = None
    current_progression_accords = None
    
    while True:
        clear_screen()
        console.print(Panel(
            Text("Mode Progression Tonale", style="bold bright_magenta", justify="center"),
            title="Progression Tonale",
            border_style="bright_magenta"
        ))
        
        if current_tonalite is None:
            current_tonalite, gammes = random.choice(list(gammes_majeures.items()))
            gammes_filtrees = [g for g in gammes if g in chord_set]
            
            current_progression_name, degres_progression = random.choice(list(tonal_progressions.items()))
            
            current_progression_accords = []
            for degre in degres_progression:
                index = DEGREE_MAP.get(degre)
                if index is not None and index < len(gammes_filtrees):
                    current_progression_accords.append(gammes_filtrees[index])
        
        console.print(f"Tonalité : [bold yellow]{current_tonalite}[/bold yellow]")
        console.print(f"Progression : [bold cyan]{current_progression_name}[/bold cyan]")
        console.print(f"Accords : [bold yellow]{' → '.join(current_progression_accords)}[/bold yellow]")
        
        console.print("\n[bold green]Écoutez la progression...[/bold green]")
        for chord_name in current_progression_accords:
            console.print(f"Joue : [bold bright_yellow]{chord_name}[/bold bright_yellow]")
            play_chord(outport, chord_set[chord_name], duration=1.0)
            time.sleep(0.3)
        
        console.print("\n[bold green]À vous de jouer! Répétez la progression accord par accord.[/bold green]")
        console.print("Appuyez sur 'r' pour réécouter la progression ou 'q' pour quitter en cours.")
        
        correct_count = 0
        skip_progression = False
        
        for chord_index, chord_name in enumerate(current_progression_accords):
            if skip_progression:
                break

            target_notes = chord_set[chord_name]
            
            with Live(console=console, screen=False, auto_refresh=True) as live:
                live.update(f"\nJouez l'accord ({chord_index+1}/{len(current_progression_accords)}): [bold yellow]{chord_name}[/bold yellow]")
                
                notes_currently_on = set()
                attempt_notes = set()
                
                while True:
                    char = wait_for_input(timeout=0.01)
                    if char:
                        char = char.lower()
                        if char == 'q':
                            skip_progression = True
                            break
                        if char == 'r':
                            live.console.print("[bold blue]Réécoute de la progression...[/bold blue]")
                            for name in current_progression_accords:
                                play_chord(outport, chord_set[name], duration=1.0)
                                time.sleep(0.3)
                            live.update(f"\nJouez l'accord ({chord_index+1}/{len(current_progression_accords)}): [bold yellow]{chord_name}[/bold yellow]")
                            continue
                    
                    for msg in inport.iter_pending():
                        if msg.type == 'note_on' and msg.velocity > 0:
                            notes_currently_on.add(msg.note)
                            attempt_notes.add(msg.note)
                        elif msg.type == 'note_off':
                            notes_currently_on.discard(msg.note)
                    
                    if not notes_currently_on and attempt_notes:
                        recognized_name, inversion_label = recognize_chord(attempt_notes)
                        
                        if recognized_name and is_enharmonic_match_improved(recognized_name, chord_name, None) and len(attempt_notes) == len(target_notes):
                            colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                            live.console.print(f"Notes jouées : [{colored_notes}]")
                            live.console.print("[bold green]Correct ![/bold green]")
                            correct_count += 1
                            time.sleep(1)
                            break
                        else:
                            colored_string = get_colored_notes_string(attempt_notes, target_notes)
                            
                            if recognized_name:
                                live.console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {recognized_name} ({inversion_label})")
                            else:
                                live.console.print("[bold red]Incorrect. Réessayez.[/bold red]")
                            
                            live.console.print(f"Notes jouées : [{colored_string}]")
                            attempt_notes.clear()
                    
                    time.sleep(0.01)
                
                if skip_progression:
                    break
        
        if not skip_progression:
            total_chords = len(current_progression_accords)
            accuracy = (correct_count / total_chords) * 100 if total_chords > 0 else 0
            
            console.print("\n--- Résultats de la progression ---")
            console.print(f"Accords corrects : [bold green]{correct_count}/{total_chords}[/bold green]")
            console.print(f"Précision : [bold cyan]{accuracy:.2f}%[/bold cyan]")
            console.print("----------------------------------")

        choice = Prompt.ask(
            "\nProgression terminée ! Appuyez sur Entrée pour choisir une autre progression ou 'q' pour revenir au menu principal...", 
            console=console, 
            choices=["", "q"], 
            show_choices=False
        )

        if choice == '':
            pass
        elif choice == 'q':
            current_tonalite = None
            current_progression_name = None
            current_progression_accords = None
            break

def display_degrees_table(tonalite, gammes_filtrees):
    """Affiche un tableau des accords de la gamme pour une tonalité donnée en utilisant Rich."""
    table = Table(
        title=f"Tonalité de [bold yellow]{tonalite}[/bold yellow]",
        style="cyan",
        title_style="bold bright_cyan",
        header_style="bold bright_cyan",
        show_header=True
    )
    table.add_column("Degré", style="dim", width=10)
    table.add_column("Accord", style="bold", width=20)
    
    degrees_romans = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']
    
    accords_de_la_gamme = gammes_majeures.get(tonalite, [])
    
    for i, accord_name in enumerate(accords_de_la_gamme):
        if accord_name in gammes_filtrees:
            table.add_row(degrees_romans[i], accord_name)

    console.print(table)

def options_menu(use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice):
    """Menu d'options pour configurer le programme."""
    while True:
        clear_screen() # Correction: efface l'écran à chaque affichage du menu
        panel_content = Text()
        panel_content.append("[1] Minuteur progression: ", style="bold white")
        panel_content.append(f"Activé ({timer_duration}s)\n" if use_timer else f"Désactivé\n", style="bold green" if use_timer else "bold red")
        panel_content.append("[2] Définir la durée du minuteur\n", style="bold white")
        panel_content.append("[3] Sélection progression: ", style="bold white")
        panel_content.append(f"MIDI (touche)\n" if progression_selection_mode == 'midi' else f"Aléatoire\n", style="bold green" if progression_selection_mode == 'midi' else "bold red")
        panel_content.append("[4] Lecture progression: ", style="bold white")
        panel_content.append(f"Avant de commencer\n" if play_progression_before_start else f"Non\n", style="bold green" if play_progression_before_start else "bold red")
        panel_content.append("[5] Accords autorisés: ", style="bold white")
        panel_content.append(f"{'Tous les accords' if chord_set_choice == 'all' else 'Majeurs/Mineurs'}\n", style="bold green")
        panel_content.append("[6] Retour au menu principal", style="bold white")
        
        panel = Panel(
            panel_content,
            title="Menu Options",
            border_style="cyan"
        )
        console.print(panel)
        
        choice = Prompt.ask("Votre choix", choices=['1', '2', '3', '4', '5', '6'], show_choices=False, console=console)
        
        if choice == '1':
            use_timer = not use_timer
        elif choice == '2':
            try:
                new_duration = Prompt.ask("Nouvelle durée en secondes", default=str(timer_duration), console=console)
                new_duration = float(new_duration)
                if new_duration > 0:
                    timer_duration = new_duration
                    console.print(f"Durée du minuteur mise à jour à [bold green]{timer_duration:.2f} secondes.[/bold green]")
                    time.sleep(1)
                else:
                    console.print("[bold red]La durée doit être un nombre positif.[/bold red]")
                    time.sleep(1)
            except ValueError:
                console.print("[bold red]Saisie invalide. Veuillez entrer un nombre.[/bold red]")
                time.sleep(1)
        elif choice == '3':
            progression_selection_mode = 'midi' if progression_selection_mode == 'random' else 'random'
        elif choice == '4':
            play_progression_before_start = not play_progression_before_start
        elif choice == '5':
            chord_set_choice = 'all' if chord_set_choice == 'basic' else 'basic'
        elif choice == '6':
            return use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice
    return use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice

def main():
    """Fonction principale du programme."""
    use_timer = False
    timer_duration = 30.0
    progression_selection_mode = 'random'
    play_progression_before_start = True
    chord_set_choice = 'basic'
    
    clear_screen()
    console.print(Panel(
        Text("Bienvenue dans l'Entraîneur d'Accords MIDI", style="bold bright_green", justify="center"),
        title="Entraîneur d'Accords",
        border_style="green",
        padding=(1, 4)
    ))

    inport_name = select_midi_port("input")
    if not inport_name:
        console.print("[bold red]Annulation de la sélection du port d'entrée. Arrêt du programme.[/bold red]")
        return

    outport_name = select_midi_port("output")
    if not outport_name:
        console.print("[bold red]Annulation de la sélection du port de sortie. Arrêt du programme.[/bold red]")
        return

    try:
        with mido.open_input(inport_name) as inport, mido.open_output(outport_name) as outport:
            clear_screen()
            console.print(f"Port d'entrée MIDI sélectionné : [bold green]{inport.name}[/bold green]")
            console.print(f"Port de sortie MIDI sélectionné : [bold green]{outport.name}[/bold green]")
            time.sleep(2)
            
            while True:
                current_chord_set = all_chords if chord_set_choice == 'all' else three_note_chords
                for _ in inport.iter_pending():
                    pass

                clear_screen()
                menu_options = Text()
                menu_options.append("[1] Mode Explorateur d'accords (Dictionnaire)\n", style="bold bright_blue")
                menu_options.append("--- Entraînement ---\n", style="dim")
                menu_options.append("[2] Mode Accord Simple\n", style="bold yellow")
                menu_options.append("[3] Mode Écoute et Devine\n", style="bold orange3")
                menu_options.append("[4] Mode Progressions d'accords (aléatoires)\n", style="bold blue")
                menu_options.append("[5] Mode Degrés (aléatoire)\n", style="bold red")
                menu_options.append("[6] Mode Tous les Degrés (gamme)\n", style="bold purple")
                menu_options.append("[7] Mode Cadences (théorie)\n", style="bold magenta")
                menu_options.append("[8] Mode Pop/Rock (célèbres)\n", style="bold cyan")
                menu_options.append("[9] Mode Reconnaissance Libre\n", style="bold bright_cyan")
                menu_options.append("[10] Mode Progression Tonale\n", style="bold bright_magenta")  # NOUVEAU MODE
                menu_options.append("--- Configuration ---\n", style="dim")
                menu_options.append("[11] Options\n", style="bold white")
                menu_options.append("[12] Quitter", style="bold white")                
                menu_panel = Panel(
                    menu_options,
                    title="Menu Principal",
                    border_style="bold blue"
                )
                console.print(menu_panel)
                
                # MODIFIÉ: Mise à jour des choix possibles
                mode_choice = Prompt.ask("Votre choix", choices=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'], show_choices=False, console=console)
                
                if mode_choice == '1':
                    chord_explorer_mode(outport)
                elif mode_choice == '2':
                    single_chord_mode(inport, outport, current_chord_set)
                elif mode_choice == '3':
                    listen_and_reveal_mode(inport, outport, current_chord_set)
                elif mode_choice == '4':
                    progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '5':
                    degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '6':
                    all_degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '7':
                    cadence_mode(inport, outport, play_progression_before_start, current_chord_set)
                elif mode_choice == '8':
                    pop_rock_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '9':
                    reverse_chord_mode(inport)
                elif mode_choice == '10':
                    tonal_progression_mode(inport, outport, current_chord_set)                    
                elif mode_choice == '11':
                    use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice = options_menu(use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice)
                elif mode_choice == '12':
                    console.print("Arrêt du programme.", style="bold red")
                    break
                else:
                    pass
                
    except KeyboardInterrupt:
        console.print("\nArrêt du programme.", style="bold red")
    except Exception as e:
        console.print(f"[bold red]Une erreur s'est produite : {e}[/bold red]")

if __name__ == "__main__":
    main()