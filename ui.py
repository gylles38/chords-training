# ui.py
import time

# Importations de la bibliothèque Rich pour l'interface
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table

# Importations depuis nos propres modules
import music_theory
from midi_handler import play_chord

def clear_screen(console):
    """Efface l'écran du terminal."""
    console.clear()

def get_colored_notes_string(played_notes, correct_notes):
    """
    Retourne une chaîne de caractères avec les notes jouées, colorées en fonction de leur justesse.
    - Vert : Note correcte à la bonne octave.
    - Jaune : Note correcte à la mauvaise octave.
    - Rouge : Note incorrecte.
    """
    output_parts = []
    correct_pitch_classes = {note % 12 for note in correct_notes}
    
    for note in sorted(list(played_notes)):
        note_name = music_theory.get_note_name(note)
        
        if note in correct_notes:
            output_parts.append(f"[bold green]{note_name}[/bold green]")
        elif (note % 12) in correct_pitch_classes:
            output_parts.append(f"[bold yellow]{note_name}[/bold yellow]")
        else:
            output_parts.append(f"[bold red]{note_name}[/bold red]")
            
    return ", ".join(output_parts)

def display_stats_fixed(console, correct_count, total_attempts, total_challenges, elapsed_time=None):
    """Affiche les statistiques de performance de la session."""
    console.print("\n--- Bilan de la session ---", style="bold cyan")
    if total_attempts > 0:
        accuracy = (correct_count / total_attempts) * 100
        console.print(f"Tentatives réussies : [bold green]{correct_count}[/bold green]")
        console.print(f"Tentatives totales : [bold yellow]{total_attempts}[/bold yellow]")
        console.print(f"Nombre de défis : [bold blue]{total_challenges}[/bold blue]")
        console.print(f"Précision : [bold cyan]{accuracy:.2f}%[/bold cyan]")
    else:
        console.print("Aucune tentative enregistrée.")
    
    if elapsed_time is not None:
        console.print(f"Temps écoulé : [bold cyan]{elapsed_time:.2f} secondes[/bold cyan]")
    console.print("-------------------------", style="bold cyan")

def display_degrees_table(console, tonalite):
    """Affiche un tableau des accords de la gamme pour une tonalité donnée."""
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
    accords_de_la_gamme = music_theory.gammes_majeures.get(tonalite, [])
    
    for i, accord_name in enumerate(accords_de_la_gamme):
        table.add_row(degrees_romans[i], accord_name)

    console.print(table)
    
def display_main_menu(console):
    """Affiche le menu principal et retourne le choix de l'utilisateur."""
    clear_screen(console)
    menu_options = Text()
    menu_options.append("[1] Mode Explorateur d'accords (Dictionnaire)\n", style="bold bright_blue")
    menu_options.append("--- Entraînement ---\n", style="dim")
    menu_options.append("[2] Mode Accord Simple\n", style="bold yellow")
    menu_options.append("[3] Mode Écoute et Devine\n", style="bold orange3")
    menu_options.append("[4] Mode Progressions (aléatoires)\n", style="bold blue")
    menu_options.append("[5] Mode Degrés (aléatoire)\n", style="bold red")
    menu_options.append("[6] Mode Tous les Degrés (gamme)\n", style="bold purple")
    menu_options.append("[7] Mode Cadences (théorie)\n", style="bold magenta")
    menu_options.append("[8] Mode Pop/Rock (célèbres)\n", style="bold cyan")
    menu_options.append("[9] Mode Reconnaissance Libre\n", style="bold bright_cyan")
    menu_options.append("[10] Mode Progression Tonale\n", style="bold bright_magenta")
    menu_options.append("--- Configuration ---\n", style="dim")
    menu_options.append("[11] Options\n", style="bold white")
    menu_options.append("[12] Quitter", style="bold white")                
    
    menu_panel = Panel(
        menu_options,
        title="Menu Principal",
        border_style="bold blue"
    )
    console.print(menu_panel)
    
    # Demander le choix à l'utilisateur
    mode_choice = Prompt.ask("Votre choix", choices=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'], show_choices=False, console=console)
    return mode_choice

def options_menu(console, settings):
    """
    Menu d'options pour configurer le programme.
    Modifie directement l'objet 'settings' passé en argument.
    """
    while True:
        clear_screen(console)
        panel_content = Text()
        panel_content.append("[1] Minuteur progression: ", style="bold white")
        panel_content.append(f"Activé ({settings.timer_duration}s)\n" if settings.use_timer else f"Désactivé\n", style="bold green" if settings.use_timer else "bold red")
        panel_content.append(f"[2] Définir durée minuteur ({settings.timer_duration}s)\n", style="bold white")
        panel_content.append("[3] Lecture avant progression: ", style="bold white")
        panel_content.append(f"Activée\n" if settings.play_progression_before_start else f"Désactivée\n", style="bold green" if settings.play_progression_before_start else "bold red")
        panel_content.append("[4] Accords autorisés: ", style="bold white")
        panel_content.append(f"{'Tous les accords' if settings.chord_set_choice == 'all' else 'Majeurs/Mineurs'}\n", style="bold green")
        panel_content.append("[5] Retour au menu principal", style="bold white")
        
        console.print(Panel(panel_content, title="Menu Options", border_style="cyan"))
        
        choice = Prompt.ask("Votre choix", choices=['1', '2', '3', '4', '5'], show_choices=False, console=console)
        
        if choice == '1':
            settings.use_timer = not settings.use_timer
        elif choice == '2':
            try:
                new_duration = Prompt.ask("Nouvelle durée en secondes", default=str(settings.timer_duration), console=console)
                new_duration = float(new_duration)
                if new_duration > 0:
                    settings.timer_duration = new_duration
                else:
                    console.print("[bold red]La durée doit être un nombre positif.[/bold red]", justify="center"); time.sleep(1)
            except ValueError:
                console.print("[bold red]Saisie invalide. Veuillez entrer un nombre.[/bold red]", justify="center"); time.sleep(1)
        elif choice == '3':
            settings.play_progression_before_start = not settings.play_progression_before_start
        elif choice == '4':
            settings.chord_set_choice = 'all' if settings.chord_set_choice == 'basic' else 'basic'
        elif choice == '5':
            break # Quitte le menu des options

def chord_explorer_mode(outport, console):
    """Mode dictionnaire : l'utilisateur saisit un nom d'accord, le programme le joue et affiche ses notes."""
    clear_screen(console)
    console.print(Panel(
        Text("Mode Explorateur d'Accords", style="bold bright_blue", justify="center"),
        border_style="bright_blue"
    ))
    console.print("Entrez un nom d'accord (ex: [cyan]C, F#m, Gm7, Bb, Ddim[/cyan]) ou 'q' pour quitter.")

    while True:
        try:
            user_input = Prompt.ask("\n[prompt.label]Accord à trouver[/prompt.label]")
            if user_input.lower() == 'q':
                break

            lookup_key = user_input.lower().replace(" ", "")
            full_chord_name = music_theory.chord_aliases.get(lookup_key)

            if full_chord_name and full_chord_name in music_theory.all_chords:
                chord_notes = music_theory.all_chords[full_chord_name]
                sorted_notes = sorted(list(chord_notes))
                note_names = ", ".join([music_theory.get_note_name(n) for n in sorted_notes])

                console.print(f"L'accord [bold green]{full_chord_name}[/bold green] contient les notes : [bold yellow]{note_names}[/bold yellow]")
                play_chord(outport, chord_notes, duration=1.2)
            else:
                console.print(f"[bold red]Accord '{user_input}' non reconnu.[/bold red]")

        except Exception as e:
            console.print(f"[bold red]Une erreur est survenue : {e}[/bold red]")