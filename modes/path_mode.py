# modes/path_mode.py

from rich.console import Console
from rich.prompt import Prompt

# Importer les gestionnaires et les données
import progress_manager
from data.progression_path import progression_path
from ui import display_progression_path_ui # Sera créée à l'étape suivante
from screen_handler import clear_screen
from messages import PathModeMenu

# Importer tous les modes de jeu
from modes.single_note_mode import single_note_mode
from modes.chord_explorer_mode import chord_explorer_mode
from modes.single_chord_mode import single_chord_mode
from modes.listen_and_reveal_mode import listen_and_reveal_mode
from modes.degrees_mode import degrees_mode
from modes.progression_mode import progression_mode
from modes.cadence_mode import cadence_mode
from modes.pop_rock_mode import pop_rock_mode
from modes.tonal_progression_mode import tonal_progression_mode
from modes.chord_transitions_mode import chord_transitions_mode
from data.chords import all_chords, three_note_chords

# --- Mapping des ID de mode aux fonctions réelles ---
# Cela permet de découpler la configuration (data) de la logique (code).
mode_map = {
    "SINGLE_NOTE": single_note_mode,
    "CHORD_EXPLORER": chord_explorer_mode,
    "SINGLE_CHORD": single_chord_mode,
    "LISTEN_AND_REVEAL": listen_and_reveal_mode,
    "DEGREES": degrees_mode,
    "PROGRESSION": progression_mode,
    "CADENCE": cadence_mode,
    "POP_ROCK": pop_rock_mode,
    "TONAL_PROGRESSION": tonal_progression_mode,
    "CHORD_TRANSITIONS": chord_transitions_mode,
}

def path_mode(inport, outport):
    """
    Gère le parcours de progression de l'utilisateur.
    Affiche les étapes, lance les exercices et suit la progression.
    """
    console = Console()

    while True:
        clear_screen()
        current_step_index = progress_manager.get_current_step()

        # Afficher l'interface du parcours de progression
        display_progression_path_ui(console, progression_path, current_step_index)

        # Vérifier si le parcours est terminé
        if current_step_index >= len(progression_path):
            console.print(PathModeMenu.PATH_COMPLETED, style="bold green")
            Prompt.ask(PathModeMenu.RETURN_PROMPT)
            break

        # Proposer à l'utilisateur de commencer l'étape ou de quitter
        step_info = progression_path[current_step_index]
        console.print(PathModeMenu.STEP_PROMPT.format(title=step_info['title']))
        choice = Prompt.ask(PathModeMenu.CHOICE, choices=['1', 'q'], show_choices=False)

        if choice == '1':
            # Lancer le mode de jeu pour l'étape actuelle
            mode_id = step_info["mode_id"]
            params = step_info["params"]
            mode_function = mode_map.get(mode_id)

            if not mode_function:
                console.print(PathModeMenu.MODE_NOT_FOUND.format(mode_id=mode_id), style="bold red")
                break

            # --- Préparation des arguments pour la fonction de mode ---
            # Ceci est un peu complexe car chaque fonction de mode a une signature différente.
            # Nous devons construire les arguments dynamiquement.

            # Arguments par défaut pour tous les modes
            args = {'inport': inport, 'outport': outport}

            # Gérer le choix du set d'accords
            if params.get("chord_set_choice") == "basic":
                args['current_chord_set'] = three_note_chords
            else:
                args['current_chord_set'] = all_chords # Par défaut ou si 'all'

            # Ajouter les autres paramètres spécifiques si la fonction les accepte
            # NOTE: C'est une simplification. Une vraie implémentation nécessiterait
            # de vérifier la signature de chaque fonction pour passer les bons arguments.
            # Pour ce projet, nous allons manuellement lister les arguments possibles.
            possible_params = [
                'use_timer', 'timer_duration', 'progression_selection_mode',
                'play_progression_before_start', 'use_voice_leading'
            ]
            for p in possible_params:
                if p in params:
                    args[p] = params[p]

            # Filtrer les arguments pour ne garder que ceux attendus par la fonction
            import inspect
            sig = inspect.signature(mode_function)
            valid_args = {k: v for k, v in args.items() if k in sig.parameters}

            # Lancer le mode
            clear_screen()
            console.print(PathModeMenu.STARTING_STEP.format(title=step_info['title']), style="bold cyan")
            console.print(step_info['description'])

            # On suppose que le mode se termine et que l'utilisateur a "réussi"
            # Une version plus avancée pourrait retourner un score ou un statut.
            mode_function(**valid_args)

            # Mettre à jour la progression
            progress_manager.advance_to_next_step()

            console.print(PathModeMenu.STEP_COMPLETED, style="bold green")
            Prompt.ask(PathModeMenu.CONTINUE_PROMPT)

        elif choice == 'q':
            # Quitter le mode parcours
            break
