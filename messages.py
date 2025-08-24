# messages.py

class Main:
    WELCOME = "Bienvenue dans l'Entraîneur d'Accords MIDI"
    TITLE = "Entraîneur d'Accords"
    INPUT_PORT_SELECTED = "Port d'entrée MIDI sélectionné : [bold green]{port_name}[/bold green]"
    OUTPUT_PORT_SELECTED = "Port de sortie MIDI sélectionné : [bold green]{port_name}[/bold green]"
    INPUT_PORT_CANCEL = "[bold red]Annulation de la sélection du port d'entrée. Arrêt du programme.[/bold red]"
    OUTPUT_PORT_CANCEL = "[bold red]Annulation de la sélection du port de sortie. Arrêt du programme.[/bold red]"
    STOP_PROGRAM = "Arrêt du programme."
    ERROR = "[bold red]Une erreur s'est produite : {e}[/bold red]"

class MainMenu:
    TITLE = "Menu Principal"
    CHORD_EXPLORER = "[1] Explorateur d'accords (Dictionnaire)"
    SINGLE_NOTE = "[2] Ecoute et Devine la note"
    PROGRESSION_SCALE = "[3] Les gammes"
    SINGLE_CHORD = "[4] Accord Simple"
    LISTEN_AND_REVEAL = "[5] Écoute et Devine l'accord"
    PROGRESSION = "[6] Progressions d'accords (aléatoires)"
    DEGREES = "[7] Degrés (aléatoire)"
    ALL_DEGREES = "[8] Tous les Degrés (gamme)"
    CADENCE = "[9] Cadences (théorie)"
    POP_ROCK = "[10] Pop/Rock (célèbres)"
    REVERSE_CHORD = "[11] Reconnaissance Libre"
    TONAL_PROGRESSION = "[12] Progression Tonale"
    REVERSED_CHORDS = "[13] Renversements d'accords (aléatoires)"
    CHORD_TRANSITIONS = "[14] Passage d'accords"
    MISSING_CHORD = "[15] Trouve l'accord manquant"
    MODULATION = "[16] Les modulations"
    OPTIONS = "[17] Options"
    QUIT = "[q] Quitter"
    CHOICE = "Votre choix"
    CONFIG_SECTION = "--- Configuration ---"

class OptionsMenu:
    TITLE = "Menu Options"
    TIMER = "[1] Minuteur progression: "
    TIMER_ENABLED = "Activé ({duration}s)"
    TIMER_DISABLED = "Désactivé"
    SET_TIMER = "[2] Définir la durée du minuteur"
    PROGRESSION_SELECTION = "[3] Sélection progression: "
    PROGRESSION_SELECTION_MIDI = "MIDI (touche)"
    PROGRESSION_SELECTION_RANDOM = "Aléatoire"
    PLAY_PROGRESSION = "[4] Lecture progression: "
    PLAY_PROGRESSION_SHOW_AND_PLAY = "Afficher et jouer"
    PLAY_PROGRESSION_PLAY_ONLY = "Jouer sans afficher (à l'oreille)"
    PLAY_PROGRESSION_NONE = "Ne pas jouer"
    CHORD_SET = "[5] Accords autorisés: "
    CHORD_SET_ALL = "Tous les accords"
    CHORD_SET_BASIC = "Majeurs/Mineurs"
    VOICE_LEADING = "[6] Conduite des voix: "
    VOICE_LEADING_ENABLED = "Activée"
    VOICE_LEADING_DISABLED = "Désactivée"
    RETURN = "[q] Retour au menu principal"
    CHOICE = "Votre choix"
    NEW_DURATION = "Nouvelle durée en secondes"
    DURATION_UPDATED = "Durée du minuteur mise à jour à [bold green]{duration:.2f} secondes.[/bold green]"
    POSITIVE_DURATION_ERROR = "[bold red]La durée doit être un nombre positif.[/bold red]"
    INVALID_INPUT_ERROR = "[bold red]Saisie invalide. Veuillez entrer un nombre.[/bold red]"

class UI:
    TONALITY_TITLE = "Tonalité de [bold yellow]{tonality}[/bold yellow]"
    DEGREE_COLUMN = "Degré"
    CHORD_COLUMN = "Accord"
    SESSION_SUMMARY = "\n--- Bilan de la session totale ---"
    CORRECT_CHORDS = "Accords corrects : [bold green]{correct_count}[/bold green]"
    INCORRECT_CHORDS = "Accords incorrects : [bold red]{incorrect_count}[/bold red]"
    SUCCESS_RATE = "Taux de réussite : [bold cyan]{percentage:.2f}%[/bold cyan]"
    NO_CHORDS_PLAYED = "Aucun accord ou progression d'accords n'a été joué."
    ELAPSED_TIME = "Temps écoulé : [bold cyan]{elapsed_time:.2f} secondes[/bold cyan]"
    SESSION_SUMMARY_FIXED = "\n--- Bilan de la session ---"
    TOTAL_ATTEMPTS = "Tentatives totales : [bold yellow]{total_attempts}[/bold yellow]"
    SUCCESSFUL_ATTEMPTS = "Tentatives réussies : [bold green]{correct_count}[/bold green]"
    FAILED_ATTEMPTS = "Tentatives échouées : [bold red]{failed_count}[/bold red]"
    GLOBAL_ACCURACY = "Précision globale : [bold cyan]{accuracy:.2f}%[/bold cyan]"
    AVG_ATTEMPTS_PER_CHORD = "Moyenne tentatives/accord : [bold magenta]{avg_attempts:.1f}[/bold magenta]"
    NO_ATTEMPTS_RECORDED = "Aucune tentative enregistrée."

class Midi:
    CHORD_NOT_PLAYED = "[bold red]L'accord {chord_name} n'a pas pu être joué (non trouvé dans le set sélectionné).[/bold red]"
    NO_PORT_FOUND = "[bold red]Aucun port {port_type} MIDI trouvé. Assurez-vous que votre périphérique est connecté.[/bold red]"
    AVAILABLE_PORTS = "Ports {port_type} MIDI disponibles"
    PORT_INDEX_COLUMN = "Index"
    PORT_NAME_COLUMN = "Nom du port"
    QUIT = "Quitter"
    CHOOSE_PORT = "Veuillez choisir un port {port_type} (1-{port_count}) ou 'q' pour quitter"
    INVALID_SELECTION_NUMBER = "[bold red]Sélection invalide. Veuillez entrer un numéro valide.[/bold red]"
    INVALID_SELECTION_INPUT = "[bold red]Sélection invalide. Veuillez entrer un numéro.[/bold red]"

class ChordModeBase:
    UNRECOGNIZED_CHORD = "Accord non reconnu"
    UNKNOWN_INVERSION = "position inconnue"
    CHORD_TYPE = "Type d'accords: [bold cyan]{chord_type}[/bold cyan]"
    # from create_live_display
    PLAY_CHORD_PROMPT = "Jouez l'accord ({prog_index}/{total_chords})"
    PLAY_CHORD_PROMPT_WITH_NAME = "Accord à jouer ({prog_index}/{total_chords}): [bold yellow]{display_name}[/bold yellow]"
    PLAY_CHORD_PROMPT_WITH_INVERSION = "Accord à jouer ({prog_index}/{total_chords}): "
    EXPECTED_NOTES = "\nNotes attendues : "
    PROGRESS_PANEL_TITLE = "Progression en cours"
    # from wait_for_end_choice
    PROGRESSION_COMPLETE = "\n[bold green]Progression terminée ![/bold green] Appuyez sur 'r' pour répéter, 'n' pour continuer ou 'q' pour quitter..."
    # from check_chord
    RECOGNITION_ERROR = "[bold red]Une erreur s'est produite lors de la reconnaissance : {e}[/bold red]"
    # from show_overall_stats_and_wait
    SHOWING_STATS = "\nAffichage des statistiques."
    NEW_RECORD = "\n[bold bright_green]Nouveau record ![/bold bright_green] Précision {accuracy:.2f}% (ancien: {prev_best:.2f}%)."
    FIRST_RECORD = "\n[bold bright_green]Premier record enregistré ![/bold bright_green] Précision {accuracy:.2f}%."
    NEW_TIME_RECORD_REMAINING = "[bold bright_green]Nouveau record de temps restant ![/bold bright_green] {new_time:.2f}s (ancien: {prev_time:.2f}s)."
    FIRST_TIME_RECORD_REMAINING = "[bold bright_green]Premier record de temps restant ![/bold bright_green] {new_time:.2f}s."
    NEW_TIME_RECORD = "[bold bright_green]Nouveau record de temps ![/bold bright_green] {new_time:.2f}s (ancien: {prev_time:.2f}s)."
    FIRST_TIME_RECORD = "[bold bright_green]Premier record de temps ![/bold bright_green] {new_time:.2f}s."
    RETURN_TO_MENU = "\nAppuyez sur une touche pour retourner au menu principal."
    # from run_progression
    SKIPPING_PROGRESSION = "\n[bold yellow]Passage à la progression suivante.[/bold yellow]"
    PROGRESSION_STATS_TITLE = "\n--- Statistiques de cette progression ---"
    CHORDS_TO_PLAY = "Accords à jouer : [bold cyan]{count}[/bold cyan]"
    TOTAL_ATTEMPTS = "Tentatives totales : [bold yellow]{count}[/bold yellow]"
    FIRST_TRY_SUCCESS = "Réussis du premier coup : [bold green]{count}[/bold green]"
    ACCURACY = "Précision : [bold cyan]{accuracy:.1f}%[/bold cyan]"
    PROGRESSION_TIME = "\nTemps pour la progression : [bold cyan]{time:.2f} secondes[/bold cyan]"
    TRANSITION_ANALYSIS = "\n--- Analyse des transitions ---"
    YOUR_PATH = "Votre parcours : "
    SUGGESTION = "Suggestion     : "
    PLAY_PROGRESSION_PROMPT = "\nProgression à jouer : [bold yellow]{progression}[/bold yellow]"
    LISTEN_PROGRESSION_PROMPT = "\nÉcoutez la progression..."
    INSTRUCTIONS = "\nAppuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer à la suivante.\n"
    TIME_REMAINING = "Temps restant : [bold magenta]{time:.1f}s[/bold magenta]"
    TIME_UP = "[bold red]Temps écoulé ! Session terminée.[/bold red]"
    REPLAYING_PROGRESSION = "[bold cyan]Lecture de la progression...[/bold cyan]"
    CORRECT_CHORD = "[bold green]Correct ! {base_chord_name} ({recognized_inversion})[/bold green]\nNotes jouées : [{colored_notes}]"
    INCORRECT_CHORD = "[bold red]Incorrect.[/bold red] Vous avez joué : {played_chord_info}\nNotes jouées : [{colored_notes}]"
    # from display_feedback
    PLAYED_NOTES = "Notes jouées : [{colored_notes}]"
    CORRECT_RECOGNIZED = "[bold green]{name}.[/bold green]"
    CORRECT = "[bold green]Correct ![/bold green]"
    UNRECOGNIZED_CHORD_ERROR = "[bold red]Accord non reconnu ![/bold red]"
    INCORRECT_RECOGNIZED = "[bold red]Incorrect.[/bold red] Vous avez joué : {name} ({inversion})"
    INCORRECT = "[bold red]Incorrect. Réessayez.[/bold red]"
    # from display_final_stats
    FINAL_STATS_PROMPT = "\nAppuyez sur une touche pour retourner au menu principal."

class SingleChordMode:
    PLAY_CHORD = "\nJouez : [bold bright_yellow]{chord_name}[/bold bright_yellow]"
    HEADER_TITLE = "Accords Simples"
    HEADER_NAME = "Mode Accords Simples"

class ListenAndRevealMode:
    HEADER_TITLE = "Écoute et Devine"
    HEADER_NAME = "Mode Écoute et Devine"
    LISTEN_CAREFULLY = "\nÉcoutez attentivement..."
    YOUR_TURN = "À vous de jouer !"
    REPLAY_PROMPT = "Ré-écouter l'accord ? (o/n)"
    REPLAYING_CHORD = "L'accord est rejoué..."

class SingleNoteMode:
    HEADER_TITLE = "Notes Simples"
    HEADER_NAME = "Mode Notes Simples"
    PLAY_NOTE = "\nJouez la note : [bold bright_yellow]{note_name}[/bold bright_yellow]"

class ProgressionScaleMode:
    HEADER_TITLE = "Gammes"
    HEADER_NAME = "Mode Gammes"
    SCALE_INFO = "\nLa gamme de [bold cyan]{tonality}[/bold cyan] est jouée."
    PLAY_SCALE = "À votre tour, jouez la gamme de [bold yellow]{tonality}[/bold yellow]."

class ProgressionMode:
    HEADER_TITLE = "Progressions"
    HEADER_NAME = "Mode Progressions"
    PLAY_PROGRESSION = "\nJouez la progression : [bold bright_yellow]{progression}[/bold bright_yellow]"

class DegreesMode:
    HEADER_TITLE = "Degrés"
    HEADER_NAME = "Mode Degrés"
    TONALITY_INFO = "Tonalité : [bold cyan]{tonality}[/bold cyan]"
    PLAY_DEGREES = "\nJouez la progression ([bold bright_yellow]{degree_progression}[/bold bright_yellow]) : [bold bright_cyan]{chord_progression}[/bold bright_cyan]"

class AllDegreesMode:
    HEADER_TITLE = "Tous les Degrés"
    HEADER_NAME = "Mode Tous les Degrés"
    TONALITY_INFO = "Tonalité : [bold cyan]{tonality}[/bold cyan]"
    PLAY_DEGREES = "\nJouez la progression de la gamme de {tonality} ([bold bright_yellow]{degree_progression}[/bold bright_yellow]) : [bold bright_cyan]{chord_progression}[/bold bright_cyan]"

class CadenceMode:
    HEADER_TITLE = "Cadences"
    HEADER_NAME = "Mode Cadences"
    TONALITY_INFO = "Tonalité : [bold cyan]{tonality}[/bold cyan]"
    PLAY_CADENCE = "\nJouez la cadence ([bold bright_yellow]{cadence_name}[/bold bright_yellow]) : [bold bright_cyan]{chord_progression}[/bold bright_cyan]"

class PopRockMode:
    HEADER_TITLE = "Pop/Rock"
    HEADER_NAME = "Mode Pop/Rock"
    PLAY_PROGRESSION = "\nJouez la progression : [bold bright_yellow]{progression_name}[/bold bright_yellow] - [bold bright_cyan]{chords}[/bold bright_cyan]"

class ChordExplorerMode:
    TITLE = "Explorateur d'accords"
    SUBTITLE = "Tapez le nom d'un accord pour l'entendre, 'q' pour quitter."
    PROMPT = "Accord"
    INVALID_CHORD = "[bold red]Accord non valide. Essayez à nouveau.[/bold red]"
    QUITTING = "Retour au menu principal."
    PLAYING_CHORD = "\nJoue [bold green]{chord_name}[/bold green] avec les notes : [bold cyan]{notes}[/bold cyan]"

class ReverseChordMode:
    HEADER_TITLE = "Reconnaissance Libre"
    HEADER_NAME = "Mode Reconnaissance Libre"
    INSTRUCTIONS = "Jouez un accord sur votre clavier MIDI..."

class TonalProgressionMode:
    HEADER_TITLE = "Progression Tonale"
    HEADER_NAME = "Mode Progression Tonale"
    TONALITY_INFO = "Tonalité : [bold cyan]{tonality}[/bold cyan]"
    PLAY_PROGRESSION = "\nJouez la progression ([bold bright_yellow]{degree_progression}[/bold bright_yellow]) : [bold bright_cyan]{chord_progression}[/bold bright_cyan]"

class ReversedChordsMode:
    HEADER_TITLE = "Renversements"
    HEADER_NAME = "Mode Renversements"
    PLAY_CHORD = "\nJouez : [bold bright_yellow]{chord_name}[/bold bright_yellow] ({inversion})"

class ChordTransitionsMode:
    HEADER_TITLE = "Passage d'accords"
    HEADER_NAME = "Mode Passage d'accords"
    TONALITY_INFO = "Tonalité : [bold cyan]{tonality}[/bold cyan]"
    PLAY_TRANSITION = "\nJouez la transition : [bold bright_yellow]{chord1}[/bold bright_yellow] -> [bold bright_cyan]{chord2}[/bold bright_cyan]"

class MissingChordMode:
    HEADER_TITLE = "Accord Manquant"
    HEADER_NAME = "Mode Accord Manquant"
    TONALITY_INFO = "Tonalité : [bold cyan]{tonality}[/bold cyan]"
    PLAY_PROGRESSION = "\nJouez la progression avec l'accord manquant ([bold red]?[/bold red]) : [bold bright_cyan]{progression}[/bold bright_cyan]"
    REPLAY_PROMPT = "Ré-écouter la progression ? (o/n)"
    REPLAYING = "La progression est rejouée..."
    WHAT_WAS_MISSING = "Quel était l'accord manquant ?"
    ENTER_CHOICE = "Entrez votre choix (1-{num_choices})"
    CORRECT_CHOICE = "[bold green]Correct ![/bold green] C'était bien [bold cyan]{chord}[/bold cyan]."
    INCORRECT_CHOICE = "[bold red]Incorrect.[/bold red] La bonne réponse était [bold cyan]{correct_chord}[/bold cyan], vous avez joué {played_chord}."

class ModulationMode:
    HEADER_TITLE = "Modulations"
    HEADER_NAME = "Mode Modulations"
    PLAY_MODULATION = "\nModulez de [bold bright_yellow]{from_tonality}[/bold bright_yellow] à [bold bright_cyan]{to_tonality}[/bold bright_cyan] via [bold magenta]{pivot_chord}[/bold magenta]"
    PROGRESSION_INFO = "Progression : [bold cyan]{progression}[/bold cyan]"
