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

# Initialisation de la console Rich
console = Console()

# Couleurs ANSI pour l'affichage dans le terminal
class Color:
    """Codes de couleur ANSI pour l'affichage dans le terminal."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    ORANGE = '\033[38;5;208m'
    END = '\033[0m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'

def clear_screen():
    """Efface l'écran du terminal."""
    # os.system('cls' if os.name == 'nt' else 'clear')
    console.clear()

# --- Définition des accords, des cadences et des gammes ---
# Un dictionnaire où la clé est le nom de l'accord et la valeur est un ensemble
# des numéros de notes MIDI pour cet accord. Les notes sont définies pour l'octave 4.
all_chords = {
    # Accords de trois sons (triades)
    "Do Majeur": {60, 64, 67},
    "Ré Mineur": {62, 65, 69},
    "Mi Mineur": {64, 67, 71},
    "Fa Majeur": {65, 69, 72},
    "Sol Majeur": {67, 71, 74},
    "La Mineur": {69, 72, 76},
    "Si Diminué": {71, 74, 77},
    "Do dièse Majeur": {61, 65, 68},
    "Ré dièse Mineur": {63, 66, 70},
    "Fa dièse Majeur": {66, 70, 73},
    "Sol dièse Mineur": {68, 71, 75},
    "La dièse Mineur": {70, 73, 77},
    "Mi bémol Majeur": {63, 67, 70},
    "Sol bémol Majeur": {66, 70, 73},
    "La bémol Majeur": {68, 72, 75},
    "Si bémol Majeur": {70, 74, 77},
    "Ré bémol Majeur": {61, 65, 68},
    
    # Autres triades
    "Ré Majeur": {62, 66, 69},
    "Si Mineur": {71, 74, 78},
    "Fa dièse Mineur": {66, 69, 73},
    "Do dièse Mineur": {61, 64, 68},
    "Mi dièse Mineur": {65, 68, 72}, # enharmonique de Fa Mineur
    "La Majeur": {69, 73, 76},
    "Mi Majeur": {64, 68, 71},
    "Si Majeur": {71, 75, 78},
    "Sol Mineur": {67, 70, 74},
    "Do Mineur": {60, 63, 67},
    "Fa dièse Diminué": {66, 69, 72},
    "Do dièse Diminué": {61, 64, 67},
    "Sol dièse Diminué": {68, 71, 74},
    "Ré dièse Diminué": {63, 66, 69},
    "Mi dièse Diminué": {65, 68, 71},
    "La dièse Diminué": {70, 73, 76},
    "Do bémol Majeur": {71, 74, 77}, # enharmonique de Si Majeur
    "Fa bémol Majeur": {64, 67, 71}, # enharmonique de Mi Majeur
    "Si bémol Mineur": {70, 73, 77},
    "Mi bémol Mineur": {63, 66, 70},
    "Sol dièse Majeur": {68, 72, 75},
    "Si dièse Diminué": {60, 63, 66}, # enharmonique de Do Diminué
    "Ré bémol Mineur": {61, 64, 68}, # enharmonique de Do dièse Mineur
    "La bémol Mineur": {68, 71, 75}, # enharmonique de Sol dièse Mineur
    "Fa Mineur": {65, 68, 72},
    "Mi Diminué": {64, 67, 70},
    "Fa Diminué": {65, 68, 71},
    "Sol Diminué": {67, 70, 73},
    "Do Diminué": {60, 63, 66},
    "Si bémol Diminué": {70, 73, 76},
    "Ré Diminué": {62, 65, 68},
    "La Diminué": {69, 72, 75},

    # --- Accords de 7ème ---
    # Accords de Do
    "Do Majeur 7ème": {60, 64, 67, 71},
    "Do 7ème": {60, 64, 67, 70},
    "Do Mineur 7ème": {60, 63, 67, 70},
    # Accords de Sol
    "Sol Majeur 7ème": {67, 71, 74, 78},
    "Sol 7ème": {67, 71, 74, 77},
    "Sol Mineur 7ème": {67, 70, 74, 77},
    # Accords de Fa
    "Fa Majeur 7ème": {65, 69, 72, 76},
    "Fa 7ème": {65, 69, 72, 75},
    "Fa Mineur 7ème": {65, 68, 72, 75},
    # Accords de La
    "La Majeur 7ème": {69, 73, 76, 80},
    "La 7ème": {69, 73, 76, 79},
    "La Mineur 7ème": {69, 72, 76, 79},
    # Accords de Ré
    "Ré Majeur 7ème": {62, 66, 69, 73},
    "Ré 7ème": {62, 66, 69, 72},
    "Ré Mineur 7ème": {62, 65, 69, 72},
    # Accords de Mi
    "Mi Majeur 7ème": {64, 68, 71, 76},
    "Mi 7ème": {64, 68, 71, 74},
    "Mi Mineur 7ème": {64, 67, 71, 74},
    # Accords de Si
    "Si Majeur 7ème": {71, 75, 78, 82},
    "Si 7ème": {71, 75, 78, 81},
    "Si Mineur 7ème": {71, 74, 78, 81},
    # Accords de Ré#
    "Ré dièse Mineur 7ème": {63, 66, 70, 73},
    # Accords de Mi bémol
    "Mi bémol Majeur 7ème": {63, 67, 70, 74},
    "Mi bémol 7ème": {63, 67, 70, 73},
    "Mi bémol Mineur 7ème": {63, 66, 70, 73},

    # --- Nouveaux accords de 4ème (sus4) et 6ème (add6) ---
    "Do 4ème": {60, 65, 67}, # Do-Fa-Sol
    "Ré 4ème": {62, 67, 69},
    "Mi 4ème": {64, 69, 71},
    "Fa 4ème": {65, 70, 72},
    "Sol 4ème": {67, 72, 74},
    "La 4ème": {69, 74, 76},
    "Si 4ème": {71, 76, 78},
    
    "Do 6ème": {60, 64, 67, 69}, # Do-Mi-Sol-La
    "Ré 6ème": {62, 66, 69, 71},
    "Mi 6ème": {64, 68, 71, 73},
    "Fa 6ème": {65, 69, 72, 74},
    "Sol 6ème": {67, 71, 74, 76},
    "La 6ème": {69, 73, 76, 78},
    "Si 6ème": {71, 75, 78, 80},
}

# Un sous-ensemble d'accords pour le mode par défaut (majeurs et mineurs à 3 notes)
# Le dictionnaire `three_note_chords` doit être construit avec soin pour inclure
# uniquement les accords à 3 notes, majeurs et mineurs.
three_note_chords = {
    name: notes for name, notes in all_chords.items()
    if ("Majeur" in name or "Mineur" in name) and len(notes) == 3
}

# Gammes majeures pour le mode degrés
gammes_majeures = {
    "Do Majeur": ["Do Majeur", "Ré Mineur", "Mi Mineur", "Fa Majeur", "Sol Majeur", "La Mineur", "Si Diminué"],
    "Sol Majeur": ["Sol Majeur", "La Mineur", "Si Mineur", "Do Majeur", "Ré Majeur", "Mi Mineur", "Fa dièse Diminué"],
    "Ré Majeur": ["Ré Majeur", "Mi Mineur", "Fa dièse Mineur", "Sol Majeur", "La Majeur", "Si Mineur", "Do dièse Diminué"],
    "La Majeur": ["La Majeur", "Si Mineur", "Do dièse Mineur", "Ré Majeur", "Mi Majeur", "Fa dièse Mineur", "Sol dièse Diminué"],
    "Mi Majeur": ["Mi Majeur", "Fa dièse Mineur", "Sol dièse Mineur", "La Majeur", "Si Majeur", "Do dièse Mineur", "Ré dièse Diminué"],
    "Si Majeur": ["Si Majeur", "Do dièse Mineur", "Ré dièse Mineur", "Mi Majeur", "Fa dièse Majeur", "Sol dièse Mineur", "La dièse Diminué"],
    "Fa dièse Majeur": ["Fa dièse Majeur", "Sol dièse Mineur", "La dièse Mineur", "Si Majeur", "Do dièse Majeur", "Ré dièse Mineur", "Mi dièse Diminué"],
    "Do dièse Majeur": ["Do dièse Majeur", "Ré dièse Mineur", "Mi dièse Mineur", "Fa dièse Majeur", "Sol dièse Majeur", "La dièse Mineur", "Si dièse Diminué"],
    "Fa Majeur": ["Fa Majeur", "Sol Mineur", "La Mineur", "Si bémol Majeur", "Do Majeur", "Ré Mineur", "Mi Diminué"],
    "Si bémol Majeur": ["Si bémol Majeur", "Do Mineur", "Ré Mineur", "Mi bémol Majeur", "Fa Majeur", "Sol Mineur", "La Diminué"],
    "Mi bémol Majeur": ["Mi bémol Majeur", "Fa Mineur", "Sol Mineur", "La bémol Majeur", "Si bémol Majeur", "Do Mineur", "Ré Diminué"],
    "La bémol Majeur": ["La bémol Majeur", "Si bémol Mineur", "Do Mineur", "Ré bémol Majeur", "Mi bémol Majeur", "Fa Mineur", "Sol Diminué"],
    "Ré bémol Majeur": ["Ré bémol Majeur", "Mi bémol Mineur", "Fa Mineur", "Sol bémol Majeur", "La bémol Majeur", "Si bémol Mineur", "Do Diminué"],
    "Sol bémol Majeur": ["Sol bémol Majeur", "La bémol Mineur", "Si bémol Mineur", "Do bémol Majeur", "Ré bémol Majeur", "Mi bémol Mineur", "Fa Diminué"],
    "Do bémol Majeur": ["Do bémol Majeur", "Ré bémol Mineur", "Mi bémol Mineur", "Fa bémol Majeur", "Sol bémol Majeur", "La bémol Mineur", "Si bémol Diminué"],
}

# Traduction des degrés pour le mode degrés
traductions_degres = {
    0: "I", 1: "ii", 2: "iii", 3: "IV", 4: "V", 5: "vi", 6: "vii°"
}

# --- Création d'un dictionnaire de correspondance pour les accords et leurs renversements ---
# Cette structure permet une reconnaissance rapide en associant chaque ensemble de notes (en frozenset)
# à son nom d'accord et son type de renversement.
inversion_lookup = {}
for chord_name, notes_set in all_chords.items():
    # Tri des notes pour faciliter le calcul des renversements
    sorted_notes = sorted(list(notes_set))
    num_notes = len(sorted_notes)
    
    # Renversement 0 (position fondamentale)
    inversion_lookup[frozenset(notes_set)] = (chord_name, "position fondamentale")
    
    # 1er renversement
    if num_notes >= 3:
        first_inversion_notes = set(sorted_notes[1:])
        first_inversion_notes.add(sorted_notes[0] + 12)
        inversion_lookup[frozenset(first_inversion_notes)] = (chord_name, "1er renversement")

    # 2ème renversement
    if num_notes >= 3:
        second_inversion_notes = set(sorted_notes[2:])
        second_inversion_notes.add(sorted_notes[0] + 12)
        second_inversion_notes.add(sorted_notes[1] + 12)
        inversion_lookup[frozenset(second_inversion_notes)] = (chord_name, "2ème renversement")

    # 3ème renversement (pour les accords de 4 notes)
    if num_notes == 4:
        third_inversion_notes = set(sorted_notes[3:])
        third_inversion_notes.add(sorted_notes[0] + 12)
        third_inversion_notes.add(sorted_notes[1] + 12)
        third_inversion_notes.add(sorted_notes[2] + 12)
        inversion_lookup[frozenset(third_inversion_notes)] = (chord_name, "3ème renversement")

# --- Fonctions utilitaires ---
def get_note_name(midi_note):
    """Convertit un numéro de note MIDI en son nom."""
    notes = ["Do", "Do#", "Ré", "Ré#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
    return notes[midi_note % 12]

def get_chord_type_from_name(chord_name):
    """Extrait le type d'accord (Majeur, Mineur, 7ème, etc.) du nom de l'accord."""
    chord_types = ["Majeur", "Mineur", "7ème", "Diminué", "4ème", "6ème"]
    for c_type in chord_types:
        if c_type in chord_name:
            return c_type
    return "Inconnu" # Fallback pour les types non listés

def play_chord(outport, chord_notes, velocity=100, duration=0.5):
    """Joue un accord via MIDI."""
    for note in chord_notes:
        msg = mido.Message('note_on', note=note, velocity=velocity)
        outport.send(msg)
    time.sleep(duration)
    for note in chord_notes:
        msg = mido.Message('note_off', note=note, velocity=0)
        outport.send(msg)

def play_progression_sequence(outport, progression, chord_set):
    """Joue une séquence d'accords."""
    console.print("[bold blue]Lecture de la progression...[/bold blue]")
    for chord_name in progression:
        # S'assurer que l'accord existe dans le jeu d'accords sélectionné
        if chord_name in chord_set:
            play_chord(outport, chord_set[chord_name], duration=0.8)
            time.sleep(0.5)
        else:
            console.print(f"[bold red]L'accord {chord_name} n'a pas pu être joué (non trouvé dans le set sélectionné).[/bold red]")

def wait_for_input(timeout=0.01):
    """Saisie de caractère non-bloquante."""
    if 'msvcrt' in sys.modules:
        if msvcrt.kbhit():
            return msvcrt.getch().decode('utf-8')
    else:
        # Pour les systèmes Unix
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            if select.select([sys.stdin], [], [], timeout)[0]:
                return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None

def wait_for_any_key(inport):
    """Fonction non-bloquante pour attendre n'importe quelle touche du clavier."""
    while True:
        char = wait_for_input(timeout=0.01)
        if char:
            return char.lower()
        # Vider le tampon MIDI
        for _ in inport.iter_pending():
            pass

def get_single_char_choice(prompt, valid_choices):
    """Demande un choix à un caractère unique avec validation, sans spammer le terminal."""
    while True:
        choice = Prompt.ask(prompt, choices=list(valid_choices), show_choices=False, console=console)
        if choice in valid_choices:
            return choice
        else:
            console.print(f"[bold red]Choix invalide. Veuillez choisir parmi {', '.join(valid_choices)}.[/bold red]")


def select_midi_port(port_type):
    """Permet à l'utilisateur de choisir un port MIDI parmi la liste disponible."""
    ports = mido.get_input_names() if port_type == "input" else mido.get_output_names()
    
    if not ports:
        console.print(f"[bold red]Aucun port {port_type} MIDI trouvé. Assurez-vous que votre périphérique est connecté.[/bold red]")
        return None
    
    table = Table(title=f"Ports {port_type} MIDI disponibles", style="bold cyan")
    table.add_column("Index", style="bold yellow")
    table.add_column("Nom du port", style="bold white")

    for i, port_name in enumerate(ports):
        table.add_row(f"[{i+1}]", port_name)
    table.add_row("[q]", "Quitter")
    
    console.print(table)
    
    while True:
        choice = Prompt.ask(f"Veuillez choisir un port {port_type} (1-{len(ports)}) ou 'q' pour quitter", console=console)
        if choice.lower() == 'q':
            return None
        try:
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(ports):
                return ports[choice_index]
            else:
                console.print(f"[bold red]Choix invalide. Veuillez entrer un numéro entre 1 et {len(ports)}.[/bold red]")
        except ValueError:
            console.print("[bold red]Saisie invalide. Veuillez entrer un numéro.[/bold red]")

def reverse_chord_mode(inport):
    """
    Mode de reconnaissance d'accords joués par l'utilisateur.
    Reconnaît les accords en position fondamentale et leurs renversements.
    
    Cette fonction utilise la base de données globale `inversion_lookup` qui contient
    l'ensemble de tous les accords définis dans le programme, indépendamment du
    choix d'accords autorisé pour les autres modes.
    """
    clear_screen()
    console.print(Panel(
        Text("Mode Reconnaissance d'accords (Tous les accords)", style="bold cyan", justify="center"),
        title="Reconnaissance d'accords",
        border_style="cyan"
    ))
    console.print("Jouez un accord sur votre clavier MIDI.")
    console.print("Appuyez sur 'q' pour quitter.")
    console.print("\nCe mode reconnaît les accords à 3 ou 4 notes en position fondamentale ainsi qu'en 1er et 2ème (et 3ème) renversement.")
    console.print("---")

    # Ensemble pour suivre les notes actuellement enfoncées
    notes_currently_on = set()
    # Ensemble pour collecter les notes de l'accord en cours
    attempt_notes = set()

    while True:
        char = wait_for_input(timeout=0.01)
        if char and char.lower() == 'q':
            break

        # Lire tous les messages MIDI en attente
        for msg in inport.iter_pending():
            if msg.type == 'note_on' and msg.velocity > 0:
                notes_currently_on.add(msg.note)
                attempt_notes.add(msg.note)
            elif msg.type == 'note_off':
                # Retirer la note des notes actuellement enfoncées
                notes_currently_on.discard(msg.note)

        # Vérifier si un accord a été joué et relâché
        if not notes_currently_on and attempt_notes:
            found_info = inversion_lookup.get(frozenset(attempt_notes))
            
            if found_info:
                chord_name, inversion_label = found_info
                console.print(f"Accord reconnu : [bold green]{chord_name}[/bold green] ({inversion_label})")
            else:
                colored_string = get_colored_notes_string(attempt_notes, set()) # Aucun accord cible, donc les notes sont toutes "incorrectes" en rouge
                console.print(f"[bold red]Accord non reconnu.[/bold red] Notes jouées : [{colored_string}]")

            # Réinitialiser pour le prochain accord
            attempt_notes.clear()
        
        time.sleep(0.01)

def display_stats(correct_count, total_count, elapsed_time=None):
    """Affiche les statistiques de performance."""
    console.print("\n--- Bilan de la session ---")
    if total_count > 0:
        pourcentage = (correct_count / total_count) * 100
        console.print(f"Accords corrects : [bold green]{correct_count}[/bold green]")
        console.print(f"Accords incorrects : [bold red]{total_count - correct_count}[/bold red]")
        console.print(f"Taux de réussite : [bold cyan]{pourcentage:.2f}%[/bold cyan]")
    else:
        console.print("Aucun accord n'a été joué.")
    if elapsed_time is not None:
        console.print(f"Temps écoulé : [bold cyan]{elapsed_time:.2f} secondes[/bold cyan]")
    console.print("-------------------------")

def get_colored_notes_string(played_notes, correct_notes):
    """Retourne une chaîne de caractères avec les notes jouées, colorées en fonction de leur justesse."""
    output_parts = []
    
    # Créer un dictionnaire pour vérifier les notes correctes dans n'importe quelle octave
    correct_note_names = {get_note_name(n) for n in correct_notes}
    
    for note in sorted(played_notes):
        note_name = get_note_name(note)
        
        if note in correct_notes:
            output_parts.append(f"[bold green]{note_name}[/bold green]")
        elif note_name in correct_note_names:
            output_parts.append(f"[bold orange3]{note_name}[/bold orange3]")
        else:
            output_parts.append(f"[bold red]{note_name}[/bold red]")
            
    return ", ".join(output_parts)


# --- Modes de jeu ---
def single_chord_mode(inport, outport, chord_set):
    """Mode d'entraînement sur les accords simples. L'utilisateur doit jouer le bon accord pour passer au suivant."""
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

        # Choisir un nouvel accord
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
                if frozenset(attempt_notes) == frozenset(chord_notes):
                    colored_notes = get_colored_notes_string(attempt_notes, chord_notes)
                    console.print(f"Notes jouées : [{colored_notes}]")
                    console.print("[bold green]Correct ![/bold green]")
                    correct_count += 1
                    total_count += 1
                    time.sleep(1) # Pause avant le prochain accord
                    break # Passer à l'accord suivant
                else:
                    colored_string = get_colored_notes_string(attempt_notes, chord_notes)
                    
                    found_info = inversion_lookup.get(frozenset(attempt_notes))
                    if found_info:
                        chord_name_played, inversion_label = found_info
                        console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {chord_name_played} ({inversion_label})")
                    else:
                        console.print("[bold red]Incorrect. Réessayez.[/bold red]")

                    console.print(f"Notes jouées : [{colored_string}]")
                    total_count += 1
                    attempt_notes.clear() # Réinitialiser pour le prochain essai
                    
            time.sleep(0.01)
        
    # Cette partie est exécutée si on quitte le mode
    display_stats(correct_count, total_count)
    console.print("\nAppuyez sur une touche pour retourner au menu principal.")
    # Vider le tampon MIDI avant d'attendre la touche
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)

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
        
        # Effacer l'écran pour le nouvel accord et réafficher l'en-tête
        clear_screen()
        console.print(Panel(
            Text("Mode Écoute et Devine", style="bold orange3", justify="center"),
            title="Écoute et Devine",
            border_style="orange3"
        ))
        console.print(f"Type d'accords: [bold cyan]{'Tous' if chord_set == all_chords else 'Majeurs/Mineurs'}[/bold cyan]")
        console.print("Écoutez l'accord joué et essayez de le reproduire.")
        console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter l'accord.")

        # Choisir un nouvel accord et le jouer
        chord_name, chord_notes = random.choice(list(chord_set.items()))
        console.print(f"\n[bold yellow]Lecture de l'accord...[/bold yellow]")
        play_chord(outport, chord_notes)
        console.print("Jouez l'accord que vous venez d'entendre.")

        notes_currently_on = set()
        attempt_notes = set()
        incorrect_attempts = 0
        
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
                elif msg.type == 'note_off':
                    notes_currently_on.discard(msg.note)
            
            if not notes_currently_on and attempt_notes:
                total_attempts += 1
                if frozenset(attempt_notes) == frozenset(chord_notes):
                    colored_notes = get_colored_notes_string(attempt_notes, chord_notes)
                    console.print(f"Notes jouées : [{colored_notes}]")
                    console.print(f"[bold green]Correct ! C'était bien {chord_name}.[/bold green]")
                    correct_count += 1
                    time.sleep(1.5) # Pause pour que l'utilisateur lise la confirmation
                    break # Passer à l'accord suivant
                else:
                    incorrect_attempts += 1
                    colored_string = get_colored_notes_string(attempt_notes, chord_notes)
                    console.print(f"[bold red]Incorrect. Réessayez.[/bold red] Notes jouées : [{colored_string}]")

                    if incorrect_attempts >= 3:
                        # Révéler la tonique après 3 essais
                        tonic_note = sorted(list(chord_notes))[0]
                        tonic_name = get_note_name(tonic_note)
                        console.print(f"Indice : La tonique est [bold cyan]{tonic_name}[/bold cyan].")
                    if incorrect_attempts >= 7: # Après 7 essais incorrects
                        # Révéler le type d'accord et attendre la validation
                        revealed_type = get_chord_type_from_name(chord_name)
                        console.print(f"Indice : C'est un accord de type [bold yellow]{revealed_type}[/bold yellow].")
                        console.print(f"[bold magenta]La réponse était : {chord_name}[/bold magenta]") # Afficher la réponse
                        
                        # Attendre la validation de l'utilisateur par une touche Entrée
                        Prompt.ask("\nAppuyez sur Entrée pour continuer...", console=console)
                        break # Passer à l'accord suivant
                    
                    attempt_notes.clear()
            
            time.sleep(0.01)

    # Cette partie est exécutée si on quitte le mode
    display_stats(correct_count, total_attempts)
    console.print("\nAppuyez sur une touche pour retourner au menu principal.")
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)

def get_progression_choice(progression_selection_mode, inport, last_progression=None):
    """Permet de choisir une progression, soit aléatoirement, soit via MIDI."""
    # Liste des progressions Pop/Rock
    progressions_pop_rock = {
        "I-V-vi-IV": ["Do Majeur", "Sol Majeur", "La Mineur", "Fa Majeur"],
        "ii-V-I": ["Ré Mineur", "Sol Majeur", "Do Majeur"],
        "I-vi-ii-V": ["Do Majeur", "La Mineur", "Ré Mineur", "Sol Majeur"],
        "IV-I-V-vi": ["Fa Majeur", "Do Majeur", "Sol Majeur", "La Mineur"],
        "I-IV-V": ["Do Majeur", "Fa Majeur", "Sol Majeur"], # Correction ici
        "I-vi-IV-V": ["Do Majeur", "La Mineur", "Fa Majeur", "Sol Majeur"],
        "vi-IV-I-V": ["La Mineur", "Fa Majeur", "Do Majeur", "Sol Majeur"],
        "I-bVII-IV": ["Do Majeur", "Si bémol Majeur", "Fa Majeur"],
    }
    progression_examples = {
        "I-V-vi-IV": ["Let It Be (The Beatles)", "Don't Stop Believin' (Journey)"],
        "ii-V-I": ["Autumn Leaves (Jazz Standard)", "I Will Survive (Gloria Gaynor)"],
        "I-vi-ii-V": ["Heart and Soul (Hoagy Carmichael)", "Blue Moon (Rodgers & Hart)"],
        "IV-I-V-vi": ["No Woman, No Cry (Bob Marley)", "With or Without You (U2)"],
        "I-IV-V": ["La Bamba (Ritchie Valens)", "Twist and Shout (The Beatles)"],
        "I-vi-IV-V": ["Stand By Me (Ben E. King)", "Unchained Melody (The Righteous Brothers)"],
        "vi-IV-I-V": ["Africa (Toto)", "With or Without You (U2)"],
        "I-bVII-IV": ["Lust for Life (Iggy Pop)", "Sweet Home Alabama (Lynyrd Skynyrd)"],
    }

    if progression_selection_mode == 'midi':
        console.print(f"Appuyez sur une note de la 4ème octave pour choisir une progression ([bold cyan]Do4 à La4[/bold cyan]) ou 'q' pour revenir au menu.")
        note_map = {
            60: "I-V-vi-IV", 62: "ii-V-I", 64: "I-vi-ii-V", 65: "IV-I-V-vi", 66: "I-IV-V", 67: "I-vi-IV-V", 69: "vi-IV-I-V", 70: "I-bVII-IV"
        }
        
        while True:
            char = wait_for_input(timeout=0.01)
            if char and char.lower() == 'q':
                return None, None, None
                
            for msg in inport.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    note = msg.note
                    if note in note_map:
                        prog_name = note_map[note]
                        if not last_progression or prog_name != last_progression:
                            progression = progressions_pop_rock[prog_name]
                            console.print(f"Progression sélectionnée : [bold cyan]{prog_name}[/bold cyan]")
                            return prog_name, progression, progression_examples[prog_name]
                        else:
                            console.print(f"[bold red]Progression déjà jouée. Veuillez en choisir une autre.[/bold red]")
            
            time.sleep(0.01)
    else: # Mode aléatoire par défaut
        prog_name, progression = random.choice(list(progressions_pop_rock.items()))
        while progression == last_progression:
            prog_name, progression = random.choice(list(progressions_pop_rock.items()))
        return prog_name, progression, progression_examples[prog_name]

def pop_rock_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    """Mode d'entraînement sur des progressions Pop/Rock."""
    
    session_correct_count = 0
    session_total_chords = 0
    last_progression_name = None
    last_progression_to_play = []
    
    exit_flag = False
    
    while not exit_flag:
        for _ in inport.iter_pending():
            pass
        
        prog_name, progression, exemples = get_progression_choice(progression_selection_mode, inport, last_progression_name)
        if prog_name is None:
            exit_flag = True
            break
        
        last_progression_name = prog_name
        last_progression_to_play = progression
        
        clear_screen()
        console.print(Panel(
            Text("Mode Progressions Pop/Rock", style="bold magenta", justify="center"),
            title="Progressions Pop/Rock",
            border_style="magenta"
        ))
        console.print(f"Type d'accords: [bold cyan]{'Tous' if chord_set == all_chords else 'Majeurs/Mineurs'}[/bold cyan]")
        console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter.")
        
        console.print(f"\nProgression à jouer : [bold yellow]{' -> '.join(progression)}[/bold yellow]")
        if prog_name in exemples:
            console.print(f"Exemples : [bold blue]{exemples[0]}[/bold blue] et [bold blue]{exemples[1]}[/bold blue]")
        
        if play_progression_before_start:
            play_progression_sequence(outport, progression, chord_set)

        progression_correct_count = 0
        is_progression_started = False
        start_time = None
        elapsed_time = 0.0 # Initialisation de la variable

        for chord_name in progression:
            target_notes = chord_set[chord_name]
            console.print(f"Jouez l'accord [bold yellow]{chord_name}[/bold yellow]")
            
            notes_currently_on = set()
            attempt_notes = set()

            while not exit_flag:
                if use_timer and is_progression_started:
                    remaining_time = timer_duration - (time.time() - start_time)
                    console.print(f"Temps restant : {remaining_time:.1f} secondes", end='\r', style="bold bright_cyan")
                    if remaining_time <= 0:
                        console.print(f"\n[bold red]Temps écoulé ! Session terminée.[/bold red]")
                        exit_flag = True
                        break

                char = wait_for_input(timeout=0.01)
                if char:
                    if char.lower() == 'q':
                        exit_flag = True
                        break
                    if char.lower() == 'r':
                        play_progression_sequence(outport, last_progression_to_play, chord_set)
                        console.print(f"Reprenons. Jouez l'accord [bold yellow]{chord_name}[/bold yellow]")
                        continue
                
                for msg in inport.iter_pending():
                    if msg.type == 'note_on' and msg.velocity > 0:
                        notes_currently_on.add(msg.note)
                        attempt_notes.add(msg.note)
                    elif msg.type == 'note_off':
                        notes_currently_on.discard(msg.note)

                if not notes_currently_on and attempt_notes:
                    if use_timer and not is_progression_started:
                        is_progression_started = True
                        start_time = time.time()
                    
                    if frozenset(attempt_notes) == frozenset(target_notes):
                        colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                        console.print(f"Notes jouées : [{colored_notes}]")
                        console.print("[bold green]Correct ![/bold green]")
                        progression_correct_count += 1
                        break
                    else:
                        colored_string = get_colored_notes_string(attempt_notes, target_notes)
                        found_info = inversion_lookup.get(frozenset(attempt_notes))
                        if found_info:
                            chord_name_played, inversion_label = found_info
                            console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {chord_name_played} ({inversion_label})")
                        else:
                            console.print("[bold red]Incorrect. Réessayez.[/bold red]")
                        console.print(f"Notes jouées : [{colored_string}]")
                        attempt_notes.clear()
                        
                time.sleep(0.01)
            
            if exit_flag:
                break
            
        session_correct_count += progression_correct_count
        session_total_chords += len(progression)
        
        if use_timer and not exit_flag and is_progression_started:
            end_time = time.time()
            elapsed_time = end_time - start_time
            console.print(f"\nTemps pour la progression : [bold cyan]{elapsed_time:.2f} secondes[/bold cyan]")
        elif not exit_flag and use_timer:
            elapsed_time = 0.0

        if not exit_flag:
            Prompt.ask("\nAppuyez sur Entrée pour la progression suivante...", console=console)
            
    if use_timer:
        display_stats(session_correct_count, session_total_chords, elapsed_time)
    else:
        display_stats(session_correct_count, session_total_chords)
        
    console.print("\nAppuyez sur Entrée pour retourner au menu principal.")
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)


def progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    """Mode d'entraînement sur des progressions d'accords."""

    session_correct_count = 0
    session_total_chords = 0
    last_progression_accords = []
    last_progression_to_play = []
    
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
        console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter.")
        
        prog_len = random.randint(3, 5)
        
        progression = random.sample(list(chord_set.keys()), prog_len)
        while progression == last_progression_accords:
            progression = random.sample(list(chord_set.keys()), prog_len)
        
        last_progression_accords = progression
        last_progression_to_play = progression
        
        console.print(f"\nProgression à jouer : [bold yellow]{' -> '.join(progression)}[/bold yellow]")
        
        if play_progression_before_start:
            play_progression_sequence(outport, progression, chord_set)

        progression_correct_count = 0
        is_progression_started = False
        start_time = None
        elapsed_time = 0.0 # Initialisation de la variable
        
        for chord_name in progression:
            target_notes = chord_set[chord_name]
            console.print(f"Jouez l'accord [bold yellow]{chord_name}[/bold yellow]")
            
            notes_currently_on = set()
            attempt_notes = set()
            
            while not exit_flag:
                if use_timer and is_progression_started:
                    remaining_time = timer_duration - (time.time() - start_time)
                    console.print(f"Temps restant : {remaining_time:.1f} secondes", end='\r', style="bold bright_cyan")
                    if remaining_time <= 0:
                        console.print(f"\n[bold red]Temps écoulé ! Session terminée.[/bold red]")
                        exit_flag = True
                        break
                    
                char = wait_for_input(timeout=0.01)
                if char:
                    if char.lower() == 'q':
                        exit_flag = True
                        break
                    if char.lower() == 'r':
                        play_progression_sequence(outport, last_progression_to_play, chord_set)
                        console.print(f"Reprenons. Jouez l'accord [bold yellow]{chord_name}[/bold yellow]")
                        continue
                
                for msg in inport.iter_pending():
                    if msg.type == 'note_on' and msg.velocity > 0:
                        notes_currently_on.add(msg.note)
                        attempt_notes.add(msg.note)
                    elif msg.type == 'note_off':
                        notes_currently_on.discard(msg.note)

                if not notes_currently_on and attempt_notes:
                    if use_timer and not is_progression_started:
                        is_progression_started = True
                        start_time = time.time()

                    if frozenset(attempt_notes) == frozenset(target_notes):
                        colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                        console.print(f"Notes jouées : [{colored_notes}]")
                        console.print("[bold green]Correct ![/bold green]")
                        progression_correct_count += 1
                        break
                    else:
                        colored_string = get_colored_notes_string(attempt_notes, target_notes)
                        found_info = inversion_lookup.get(frozenset(attempt_notes))
                        if found_info:
                            chord_name_played, inversion_label = found_info
                            console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {chord_name_played} ({inversion_label})")
                        else:
                            console.print("[bold red]Incorrect. Réessayez.[/bold red]")
                        console.print(f"Notes jouées : [{colored_string}]")
                        attempt_notes.clear()
                
                time.sleep(0.01)
            
            if exit_flag:
                break
            
        session_correct_count += progression_correct_count
        session_total_chords += len(progression)

        if use_timer and not exit_flag and is_progression_started:
            end_time = time.time()
            elapsed_time = end_time - start_time
            console.print(f"\nTemps pour la progression : [bold cyan]{elapsed_time:.2f} secondes[/bold cyan]")
        elif not exit_flag and use_timer:
            elapsed_time = 0.0

        if not exit_flag:
            Prompt.ask("\nAppuyez sur Entrée pour la progression suivante...", console=console)
            
    if use_timer:
        display_stats(session_correct_count, session_total_chords, elapsed_time)
    else:
        display_stats(session_correct_count, session_total_chords)
        
    console.print("\nAppuyez sur Entrée pour retourner au menu principal.")
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)

def degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    """Mode d'entraînement sur les accords par degrés."""
    
    session_correct_count = 0
    session_total_chords = 0
    last_progression_accords = []
    last_progression_to_play = []
    
    exit_flag = False
    
    while not exit_flag:
        for _ in inport.iter_pending():
            pass

        clear_screen()
        console.print(Panel(
            Text("Mode Degrés", style="bold red", justify="center"),
            title="Degrés",
            border_style="red"
        ))
        console.print(f"Type d'accords: [bold cyan]{'Tous' if chord_set == all_chords else 'Majeurs/Mineurs'}[/bold cyan]")
        console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter.")
        
        tonalite, gammes = random.choice(list(gammes_majeures.items()))
        gammes_filtrees = [g for g in gammes if g in chord_set]
        if len(gammes_filtrees) < 3:
            continue
            
        prog_len = random.randint(3, min(len(gammes_filtrees), 5))
        
        progression_accords = []
        while not progression_accords or progression_accords == last_progression_accords:
            degres_progression = random.sample(range(len(gammes_filtrees)), prog_len)
            progression_accords = [gammes_filtrees[d] for d in degres_progression]
            
        last_progression_accords = progression_accords
        last_progression_to_play = progression_accords
        
        display_degrees_table(tonalite, gammes_filtrees)

        console.print(f"\nDans la tonalité de [bold yellow]{tonalite}[/bold yellow], jouez la progression : [bold yellow]{' -> '.join(progression_accords)}[/bold yellow]")
        
        if play_progression_before_start:
            play_progression_sequence(outport, progression_accords, chord_set)

        progression_correct_count = 0
        is_progression_started = False
        start_time = None
        elapsed_time = 0.0 # Initialisation de la variable

        for chord_name in progression_accords:
            target_notes = chord_set[chord_name]
            console.print(f"Jouez l'accord [bold yellow]{chord_name}[/bold yellow]")
            
            notes_currently_on = set()
            attempt_notes = set()
            
            while not exit_flag:
                if use_timer and is_progression_started:
                    remaining_time = timer_duration - (time.time() - start_time)
                    console.print(f"Temps restant : {remaining_time:.1f} secondes", end='\r', style="bold bright_cyan")
                    if remaining_time <= 0:
                        console.print(f"\n[bold red]Temps écoulé ! Session terminée.[/bold red]")
                        exit_flag = True
                        break

                char = wait_for_input(timeout=0.01)
                if char:
                    if char.lower() == 'q':
                        exit_flag = True
                        break
                    if char.lower() == 'r':
                        play_progression_sequence(outport, last_progression_to_play, chord_set)
                        console.print(f"Reprenons. Jouez l'accord [bold yellow]{chord_name}[/bold yellow]")
                        continue

                for msg in inport.iter_pending():
                    if msg.type == 'note_on' and msg.velocity > 0:
                        notes_currently_on.add(msg.note)
                        attempt_notes.add(msg.note)
                    elif msg.type == 'note_off':
                        notes_currently_on.discard(msg.note)

                if not notes_currently_on and attempt_notes:
                    if use_timer and not is_progression_started:
                        is_progression_started = True
                        start_time = time.time()

                    if frozenset(attempt_notes) == frozenset(target_notes):
                        colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                        console.print(f"Notes jouées : [{colored_notes}]")
                        console.print("[bold green]Correct ![/bold green]")
                        progression_correct_count += 1
                        break
                    else:
                        colored_string = get_colored_notes_string(attempt_notes, target_notes)
                        found_info = inversion_lookup.get(frozenset(attempt_notes))
                        if found_info:
                            chord_name_played, inversion_label = found_info
                            console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {chord_name_played} ({inversion_label})")
                        else:
                            console.print("[bold red]Incorrect. Réessayez.[/bold red]")
                        console.print(f"Notes jouées : [{colored_string}]")
                        attempt_notes.clear()
                
                time.sleep(0.01)
            
            if exit_flag:
                break
            
        session_correct_count += progression_correct_count
        session_total_chords += len(progression_accords)

        if use_timer and not exit_flag and is_progression_started:
            end_time = time.time()
            elapsed_time = end_time - start_time
            console.print(f"\nTemps pour la progression : [bold cyan]{elapsed_time:.2f} secondes[/bold cyan]")
        elif not exit_flag and use_timer:
            elapsed_time = 0.0

        if not exit_flag:
            Prompt.ask("\nAppuyez sur Entrée pour la progression suivante...", console=console)
            
    if use_timer:
        display_stats(session_correct_count, session_total_chords, elapsed_time)
    else:
        display_stats(session_correct_count, session_total_chords)
        
    console.print("\nAppuyez sur Entrée pour retourner au menu principal.")
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)

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
    clear_screen()
    while True:
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
                else:
                    console.print("[bold red]La durée doit être un nombre positif.[/bold red]")
            except ValueError:
                console.print("[bold red]Saisie invalide. Veuillez entrer un nombre.[/bold red]")
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
                menu_options.append("[1] Mode Accord Simple\n", style="bold yellow")
                menu_options.append("[2] Mode Écoute et Devine\n", style="bold orange3")
                menu_options.append("[3] Mode Progressions d'Accords (aléatoires)\n", style="bold blue")
                menu_options.append("[4] Mode Degrés (par tonalité)\n", style="bold red")
                menu_options.append("[5] Mode Pop/Rock (progressions célèbres)\n", style="bold magenta")
                menu_options.append("[6] Mode Reconnaissance d'accords\n", style="bold cyan")
                menu_options.append("[7] Options\n", style="bold white")
                menu_options.append("[8] Quitter", style="bold white")
                
                menu_panel = Panel(
                    menu_options,
                    title="Menu Principal",
                    border_style="bold blue"
                )
                console.print(menu_panel)
                
                mode_choice = Prompt.ask("Votre choix", choices=['1', '2', '3', '4', '5', '6', '7', '8'], show_choices=False, console=console)
                
                if mode_choice == '1':
                    single_chord_mode(inport, outport, current_chord_set)
                elif mode_choice == '2':
                    listen_and_reveal_mode(inport, outport, current_chord_set)
                elif mode_choice == '3':
                    progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '4':
                    degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '5':
                    pop_rock_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '6':
                    # L'appel a été corrigé ici pour ne plus passer le paramètre `outport`
                    # car il n'est pas utilisé par la fonction `reverse_chord_mode`.
                    reverse_chord_mode(inport)
                elif mode_choice == '7':
                    use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice = options_menu(use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice)
                elif mode_choice == '8':
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
