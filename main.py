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
from stats_manager import clear_error_stats
from messages import Main, MainMenu, OptionsMenu, ChordModeBase

from modes.single_chord_mode import single_chord_mode
from modes.listen_and_reveal_mode import listen_and_reveal_mode
from modes.single_note_mode import single_note_mode
from modes.progression_scale_mode import progression_scale_mode
from modes.progression_mode import progression_mode
from modes.degrees_mode import degrees_mode
from modes.all_degrees_mode import all_degrees_mode
from modes.cadence_mode import cadence_mode
from modes.pop_rock_mode import pop_rock_mode
from modes.chord_explorer_mode import chord_explorer_mode
from modes.reverse_chord_mode import reverse_chord_mode
from modes.tonal_progression_mode import tonal_progression_mode
from modes.reversed_chords_mode import reversed_chords_mode
from modes.chord_transitions_mode import chord_transitions_mode
from modes.missing_chord_mode import missing_chord_mode
from modes.modulation_mode import modulation_mode

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
        return ChordModeBase.UNRECOGNIZED_CHORD

    # Nettoyer les caractères problématiques
    safe_name = str(chord_name).replace('%', 'pct').replace('{', '(').replace('}', ')')
    safe_inversion = str(inversion) if inversion else ChordModeBase.UNKNOWN_INVERSION
    safe_inversion = safe_inversion.replace('%', 'pct').replace('{', '(').replace('}', ')')

    return f"{safe_name} ({safe_inversion})"


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

def options_menu(use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice, use_voice_leading):
    """Menu d'options pour configurer le programme."""
    while True:
        clear_screen()

        if play_progression_before_start == 'SHOW_AND_PLAY':
            progression_text = OptionsMenu.PLAY_PROGRESSION_SHOW_AND_PLAY
            progression_style = "bold green"
        elif play_progression_before_start == 'PLAY_ONLY':
            progression_text = OptionsMenu.PLAY_PROGRESSION_PLAY_ONLY
            progression_style = "bold yellow"
        else: # 'NONE'
            progression_text = OptionsMenu.PLAY_PROGRESSION_NONE
            progression_style = "bold red"

        panel_content = Text()
        panel_content.append(OptionsMenu.TIMER, style="bold white")
        timer_status = OptionsMenu.TIMER_ENABLED.format(duration=timer_duration) if use_timer else OptionsMenu.TIMER_DISABLED
        panel_content.append(f"{timer_status}\n", style="bold green" if use_timer else "bold red")
        panel_content.append(f"{OptionsMenu.SET_TIMER}\n", style="bold white")
        panel_content.append(OptionsMenu.PROGRESSION_SELECTION, style="bold white")
        prog_selection_text = OptionsMenu.PROGRESSION_SELECTION_MIDI if progression_selection_mode == 'midi' else OptionsMenu.PROGRESSION_SELECTION_RANDOM
        panel_content.append(f"{prog_selection_text}\n", style="bold green" if progression_selection_mode == 'midi' else "bold red")
        panel_content.append(OptionsMenu.PLAY_PROGRESSION, style="bold white")
        panel_content.append(f"{progression_text}\n", style=progression_style)
        panel_content.append(OptionsMenu.CHORD_SET, style="bold white")
        chord_set_text = OptionsMenu.CHORD_SET_ALL if chord_set_choice == 'all' else OptionsMenu.CHORD_SET_BASIC
        panel_content.append(f"{chord_set_text}\n", style="bold green")
        panel_content.append(OptionsMenu.VOICE_LEADING, style="bold white")
        voice_leading_text = OptionsMenu.VOICE_LEADING_ENABLED if use_voice_leading else OptionsMenu.VOICE_LEADING_DISABLED
        panel_content.append(f"{voice_leading_text}\n", style="bold green" if use_voice_leading else "bold red")
        panel_content.append(OptionsMenu.RETURN, style="bold white")

        panel = Panel(
            panel_content,
            title=OptionsMenu.TITLE,
            border_style="cyan"
        )
        console.print(panel)

        choice = Prompt.ask(OptionsMenu.CHOICE, choices=['1', '2', '3', '4', '5', '6', 'q'], show_choices=False, console=console)

        if choice == '1':
            use_timer = not use_timer
        elif choice == '2':
            try:
                new_duration = Prompt.ask(OptionsMenu.NEW_DURATION, default=str(timer_duration), console=console)
                new_duration = float(new_duration)
                if new_duration > 0:
                    timer_duration = new_duration
                    console.print(OptionsMenu.DURATION_UPDATED.format(duration=timer_duration))
                    time.sleep(1)
                else:
                    console.print(OptionsMenu.POSITIVE_DURATION_ERROR)
                    time.sleep(1)
            except ValueError:
                console.print(OptionsMenu.INVALID_INPUT_ERROR)
                time.sleep(1)
        elif choice == '3':
            progression_selection_mode = 'midi' if progression_selection_mode == 'random' else 'random'
        elif choice == '4':
            if play_progression_before_start == 'SHOW_AND_PLAY':
                play_progression_before_start = 'PLAY_ONLY'
            elif play_progression_before_start == 'PLAY_ONLY':
                play_progression_before_start = 'NONE'
            else: # 'NONE'
                play_progression_before_start = 'SHOW_AND_PLAY'
        elif choice == '5':
            chord_set_choice = 'all' if chord_set_choice == 'basic' else 'basic'
        elif choice == '6':
            use_voice_leading = not use_voice_leading
        elif choice == 'q':
            return use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice, use_voice_leading

def main():
    """Fonction principale du programme."""
    # Réinitialiser les statistiques d'erreurs au démarrage
    clear_error_stats()

    use_timer = False
    timer_duration = 30.0
    progression_selection_mode = 'random'
    play_progression_before_start = 'SHOW_AND_PLAY'
    chord_set_choice = 'basic'
    use_voice_leading = True

    clear_screen()
    console.print(Panel(
        Text(Main.WELCOME, style="bold bright_green", justify="center"),
        title=Main.TITLE,
        border_style="green",
        padding=(1, 4)
    ))

    inport_name = select_midi_port("input")
    if not inport_name:
        console.print(Main.INPUT_PORT_CANCEL)
        return

    outport_name = select_midi_port("output")
    if not outport_name:
        console.print(Main.OUTPUT_PORT_CANCEL)
        return

    try:
        with mido.open_input(inport_name) as inport, mido.open_output(outport_name) as outport:
            clear_screen()
            console.print(Main.INPUT_PORT_SELECTED.format(port_name=inport.name))
            console.print(Main.OUTPUT_PORT_SELECTED.format(port_name=outport.name))
            time.sleep(2)

            while True:
                current_chord_set = all_chords if chord_set_choice == 'all' else three_note_chords
                for _ in inport.iter_pending():
                    pass

                clear_screen()
                menu_options = Text()
                menu_options.append(f"{MainMenu.CHORD_EXPLORER}\n", style="bold chartreuse4")
                menu_options.append(f"{MainMenu.SINGLE_NOTE}\n", style="bold bright_blue")
                menu_options.append(f"{MainMenu.PROGRESSION_SCALE}\n", style="bold bright_cyan")
                menu_options.append(f"{MainMenu.SINGLE_CHORD}\n", style="bold yellow")
                menu_options.append(f"{MainMenu.LISTEN_AND_REVEAL}\n", style="bold orange3")
                menu_options.append(f"{MainMenu.PROGRESSION}\n", style="bold grey37")
                menu_options.append(f"{MainMenu.DEGREES}\n", style="bold red")
                menu_options.append(f"{MainMenu.ALL_DEGREES}\n", style="bold purple")
                menu_options.append(f"{MainMenu.CADENCE}\n", style="bold magenta")
                menu_options.append(f"{MainMenu.POP_ROCK}\n", style="bold cyan")
                menu_options.append(f"{MainMenu.REVERSE_CHORD}\n", style="bold green4")
                menu_options.append(f"{MainMenu.TONAL_PROGRESSION}\n", style="bold bright_magenta")
                menu_options.append(f"{MainMenu.REVERSED_CHORDS}\n", style="bold blue_violet")
                menu_options.append(f"{MainMenu.CHORD_TRANSITIONS}\n", style="bold purple")
                menu_options.append(f"{MainMenu.MISSING_CHORD}\n", style="bold green_yellow")
                menu_options.append(f"{MainMenu.MODULATION}\n", style="bold red1")
                menu_options.append(f"{MainMenu.CONFIG_SECTION}\n", style="dim")
                menu_options.append(f"{MainMenu.OPTIONS}\n", style="bold white")
                menu_options.append(MainMenu.QUIT, style="bold white")

                menu_panel = Panel(
                    menu_options,
                    title=MainMenu.TITLE,
                    border_style="bold blue"
                )
                console.print(menu_panel)

                mode_choice = Prompt.ask(MainMenu.CHOICE, choices=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', 'q'], show_choices=False, console=console)

                if mode_choice == '1':
                    chord_explorer_mode(outport)
                elif mode_choice == '2':
                    single_note_mode(inport, outport)
                elif mode_choice == '3':
                    progression_scale_mode(inport, outport, play_progression_before_start)
                elif mode_choice == '4':
                    single_chord_mode(inport, outport, current_chord_set)
                elif mode_choice == '5':
                    listen_and_reveal_mode(inport, outport, current_chord_set)
                elif mode_choice == '6':
                    progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '7':
                    degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '8':
                    all_degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '9':
                    cadence_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set, use_voice_leading)
                elif mode_choice == '10':
                    pop_rock_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '11':
                    reverse_chord_mode(inport, outport, current_chord_set)
                elif mode_choice == '12':
                    tonal_progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '13':
                    reversed_chords_mode(inport, outport, current_chord_set)
                elif mode_choice == '14':
                    chord_transitions_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set, use_voice_leading)
                elif mode_choice == '15':
                    missing_chord_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set, use_voice_leading)
                elif mode_choice == '16':
                    modulation_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set, use_voice_leading)
                elif mode_choice == '17':
                    use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice, use_voice_leading = options_menu(use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice, use_voice_leading)
                elif mode_choice == 'q':
                    console.print(Main.STOP_PROGRAM, style="bold red")
                    break
                else:
                    pass
                
    except KeyboardInterrupt:
        console.print(f"\n{Main.STOP_PROGRAM}", style="bold red")
    except Exception as e:
        console.print(Main.ERROR.format(e=e))

if __name__ == "__main__":
    main()