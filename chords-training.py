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
from modes.pop_rock_mode import pop_rock_mode as pop_rock_mode_refactored
from modes.chord_explorer_mode import chord_explorer_mode
from modes.reverse_chord_mode import reverse_chord_mode
from modes.tonal_progression_mode import tonal_progression_mode
from modes.reversed_chords_mode import reversed_chords_mode

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


def pop_rock_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set):
    # Délégué vers la version refactorisée basée sur ChordModeBase
    return pop_rock_mode_refactored(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)

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
                menu_options.append("[1] Explorateur d'accords (Dictionnaire)\n", style="bold chartreuse4")
                menu_options.append("[2] Accord Simple\n", style="bold yellow")
                menu_options.append("[3] Écoute et Devine l'accord\n", style="bold orange3")
                menu_options.append("[4] Progressions d'accords (aléatoires)\n", style="bold grey37")
                menu_options.append("[5] Degrés (aléatoire)\n", style="bold red")
                menu_options.append("[6] Tous les Degrés (gamme)\n", style="bold purple")
                menu_options.append("[7] Cadences (théorie)\n", style="bold magenta")
                menu_options.append("[8] Pop/Rock (célèbres)\n", style="bold cyan")
                menu_options.append("[9] Reconnaissance Libre\n", style="bold green4")
                menu_options.append("[10] Progression Tonale\n", style="bold bright_magenta")
                menu_options.append("[11] Renversements d'accords (aléatoires)\n", style="bold blue_violet") # NOUVEAU MODE
                menu_options.append("--- Configuration ---\n", style="dim")
                menu_options.append("[12] Options\n", style="bold white")
                menu_options.append("[13] Quitter", style="bold white")
                menu_panel = Panel(
                    menu_options,
                    title="Menu Principal",
                    border_style="bold blue"
                )
                console.print(menu_panel)
                
                # MODIFIÉ: Mise à jour des choix possibles
                mode_choice = Prompt.ask("Votre choix", choices=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13'], show_choices=False, console=console)
                
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
                    cadence_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '8':
                    pop_rock_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '9':
                    reverse_chord_mode(inport, outport, current_chord_set)
                elif mode_choice == '10':
                    tonal_progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '11':
                    reversed_chords_mode(inport, outport, current_chord_set)
                elif mode_choice == '12':
                    use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice = options_menu(use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice)
                elif mode_choice == '13':
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