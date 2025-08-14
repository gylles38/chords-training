# modes/pop_rock_mode.py
import random

from rich.table import Table

from .chord_mode_base import ChordModeBase
from data.chords import gammes_majeures
from screen_handler import int_to_roman

class PopRockMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.progression_selection_mode = progression_selection_mode
        self.play_progression_before_start = play_progression_before_start

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


def pop_rock_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    mode = PopRockMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set)
    mode.run()
