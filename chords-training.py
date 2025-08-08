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

# Initialisation de la console Rich
console = Console()

# --- Définition des accords, des cadences et des gammes ---
# Dictionnaire des accords. La clé est le nom de l'accord, et la valeur est un ensemble
# des numéros de notes MIDI pour cet accord, dans une octave de référence.
# Cette structure est utilisée comme la "source de vérité" pour les notes de chaque accord.
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
    "Ré bémol Majeur": {61, 65, 68}, # enharmonique de Do dièse Majeur
    "Do bémol Majeur": {59, 63, 66},
    "Ré Majeur": {62, 66, 69},
    "Si Mineur": {71, 74, 78},
    "Fa dièse Mineur": {66, 69, 73},
    "Do dièse Mineur": {61, 64, 68},
    "Mi dièse Mineur": {65, 68, 72}, # enharmonique de Fa Mineur
    "La Majeur": {69, 73, 76},
    "Mi Majeur": {64, 68, 71},
    "Fa bémol Majeur": {64, 68, 71}, # Correction: enharmonique de Mi Majeur
    "Si Majeur": {71, 75, 78},
    "Sol Mineur": {67, 70, 74},
    "Do Mineur": {60, 63, 67},
    "Fa dièse Diminué": {66, 69, 72},
    "Do dièse Diminué": {61, 64, 67},
    "Sol dièse Diminué": {68, 71, 74},
    "Ré dièse Diminué": {63, 66, 69},
    "Mi dièse Diminué": {65, 68, 71},
    "La dièse Diminué": {70, 73, 76},
    "Si bémol Mineur": {70, 73, 77},
    "Mi bémol Mineur": {63, 66, 70}, # enharmonique de Ré dièse Mineur
    "Sol dièse Majeur": {68, 72, 75}, # enharmonique de La bémol Majeur
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
    "Do Majeur 7ème": {60, 64, 67, 71},
    "Do 7ème": {60, 64, 67, 70},
    "Do Mineur 7ème": {60, 63, 67, 70},
    "Sol Majeur 7ème": {67, 71, 74, 78},
    "Sol 7ème": {67, 71, 74, 77},
    "Sol Mineur 7ème": {67, 70, 74, 77},
    "Fa Majeur 7ème": {65, 69, 72, 76},
    "Fa 7ème": {65, 69, 72, 75},
    "Fa Mineur 7ème": {65, 68, 72, 75},
    "La Majeur 7ème": {69, 73, 76, 80},
    "La 7ème": {69, 73, 76, 79},
    "La Mineur 7ème": {69, 72, 76, 79},
    "Ré Majeur 7ème": {62, 66, 69, 73},
    "Ré 7ème": {62, 66, 69, 72},
    "Ré Mineur 7ème": {62, 65, 69, 72},
    "Mi Majeur 7ème": {64, 68, 71, 76},
    "Mi 7ème": {64, 68, 71, 74},
    "Mi Mineur 7ème": {64, 67, 71, 74},
    "Si Majeur 7ème": {71, 75, 78, 82},
    "Si 7ème": {71, 75, 78, 81},
    "Si Mineur 7ème": {71, 74, 78, 81},
    "Ré dièse Mineur 7ème": {63, 66, 70, 73},
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

# --- Carte des équivalences enharmoniques pour la reconnaissance ---
# Permet de lier les noms d'accords qui partagent les mêmes notes MIDI
enharmonic_map = {
    "Ré dièse Mineur": "Mi bémol Mineur",
    "Mi bémol Mineur": "Ré dièse Mineur",
    "Fa dièse Majeur": "Sol bémol Majeur",
    "Sol bémol Majeur": "Fa dièse Majeur",
    "Do dièse Majeur": "Ré bémol Majeur",
    "Ré bémol Majeur": "Do dièse Majeur",
    "Fa bémol Majeur": "Mi Majeur",
    "Mi Majeur": "Fa bémol Majeur",
    "Mi dièse Mineur": "Fa Mineur",
    "Fa Mineur": "Mi dièse Mineur",
    "Sol dièse Majeur": "La bémol Majeur",
    "La bémol Majeur": "Sol dièse Majeur",
    "Ré bémol Mineur": "Do dièse Mineur",
    "Do dièse Mineur": "Ré bémol Mineur",
    "La bémol Mineur": "Sol dièse Mineur",
    "Sol dièse Mineur": "La bémol Mineur",
    "Si dièse Diminué": "Do Diminué",
    "Do Diminué": "Si dièse Diminué",
}


# Un sous-ensemble d'accords pour le mode par défaut (majeurs et mineurs à 3 notes)
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

# --- Création d'un dictionnaire de correspondance pour la reconnaissance par classe de hauteur ---
# Cette structure est générée une seule fois au début du programme.
# La clé est un frozenset des classes de hauteur de l'accord, et la valeur est le nom de l'accord.
pitch_class_lookup = {}
for chord_name, notes_set in all_chords.items():
    pitch_classes = frozenset(note % 12 for note in notes_set)
    # Gérer les cas d'accords enharmoniques qui ont la même structure de notes.
    # Ex: Mi Majeur et Fa bémol Majeur. La première occurrence dans la liste sera gardée.
    if pitch_classes not in pitch_class_lookup:
        pitch_class_lookup[pitch_classes] = chord_name

# --- Fonctions utilitaires ---
def clear_screen():
    """Efface l'écran du terminal."""
    console.clear()

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

def is_enharmonic_match(name1, name2, enharmonic_map):
    """Vérifie si deux noms d'accords sont enharmoniquement équivalents."""
    if name1 == name2:
        return True
    return enharmonic_map.get(name1) == name2 or enharmonic_map.get(name2) == name1

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

def recognize_chord(played_notes_set):
    """
    Reconnaît un accord à partir d'un ensemble de notes MIDI jouées,
    en utilisant la méthode de la classe de hauteur.
    
    Retourne le nom de l'accord et le type de renversement, ou None si non reconnu.
    """
    if len(played_notes_set) < 2:
        return None, None

    # Convertir les notes jouées en un ensemble de classes de hauteur (pitch classes)
    played_pitch_classes = frozenset(note % 12 for note in played_notes_set)
    
    # Rechercher la correspondance dans la table pré-calculée
    chord_name = pitch_class_lookup.get(played_pitch_classes)
    
    if chord_name:
        # Déterminer la tonique et le renversement pour le feedback utilisateur
        chord_notes_reference = sorted(list(all_chords[chord_name]))
        played_notes_sorted = sorted(list(played_notes_set))
        
        # Trouver la tonique de l'accord joué
        tonic_played = played_notes_sorted[0] % 12
        
        # Trouver la tonique de l'accord de référence
        tonic_reference = chord_notes_reference[0] % 12

        # Décalage de la tonique (utile pour identifier les renversements)
        # 0 = position fondamentale, 1 = 1er renversement, etc.
        # Cette partie est illustrative pour l'affichage, la reconnaissance est déjà faite.
        root_offset = 0
        if tonic_played == tonic_reference:
            root_offset = 0
        elif tonic_played == chord_notes_reference[1] % 12:
            root_offset = 1
        elif len(chord_notes_reference) >= 3 and tonic_played == chord_notes_reference[2] % 12:
            root_offset = 2
        elif len(chord_notes_reference) == 4 and tonic_played == chord_notes_reference[3] % 12:
            root_offset = 3

        inversion_label = ""
        if root_offset == 0:
            inversion_label = "position fondamentale"
        elif root_offset == 1:
            inversion_label = "1er renversement"
        elif root_offset == 2:
            inversion_label = "2ème renversement"
        elif root_offset == 3:
            inversion_label = "3ème renversement"
            
        return chord_name, inversion_label
    
    return None, None

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
    """
    Retourne une chaîne de caractères avec les notes jouées, colorées en fonction de leur justesse.
    
    Correction de bug : cette fonction est maintenant plus intelligente.
    - Vert : La note jouée est exactement la bonne (même note, même octave).
    - Jaune : La note jouée est la bonne, mais dans une octave différente.
    - Rouge : La note jouée est incorrecte.
    """
    output_parts = []
    
    # Créer un ensemble des classes de hauteur correctes (indépendant de l'octave)
    correct_pitch_classes = {note % 12 for note in correct_notes}
    
    for note in sorted(played_notes):
        note_name = get_note_name(note)
        
        if note in correct_notes:
            # Correspondance parfaite (note et octave)
            output_parts.append(f"[bold green]{note_name}[/bold green]")
        elif (note % 12) in correct_pitch_classes:
            # Bonne note, mais mauvaise octave
            output_parts.append(f"[bold yellow]{note_name}[/bold yellow]")
        else:
            # Mauvaise note
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
                # Vérification de l'accord joué par l'utilisateur
                recognized_name, recognized_inversion = recognize_chord(attempt_notes)
                
                # Correction: Utiliser la carte enharmonique et la taille pour valider la réponse
                if is_enharmonic_match(recognized_name, chord_name, enharmonic_map) and len(attempt_notes) == len(chord_notes):
                    colored_notes = get_colored_notes_string(attempt_notes, chord_notes)
                    console.print(f"Notes jouées : [{colored_notes}]")
                    console.print("[bold green]Correct ![/bold green]")
                    correct_count += 1
                    total_count += 1
                    time.sleep(1) # Pause avant le prochain accord
                    break # Passer à l'accord suivant
                else:
                    colored_string = get_colored_notes_string(attempt_notes, chord_notes)
                    
                    found_chord, found_inversion = recognize_chord(attempt_notes)
                    
                    if found_chord:
                        console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {found_chord} ({found_inversion})")
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
                
                # Vérification de l'accord joué par l'utilisateur
                recognized_name, recognized_inversion = recognize_chord(attempt_notes)

                # Fix du bug: on vérifie que le nombre de notes jouées est le même que le nombre de notes de l'accord cible
                if is_enharmonic_match(recognized_name, chord_name, enharmonic_map) and len(attempt_notes) == len(chord_notes):
                    colored_notes = get_colored_notes_string(attempt_notes, chord_notes)
                    console.print(f"Notes jouées : [{colored_notes}]")
                    console.print(f"[bold green]Correct ! C'était bien {chord_name}.[/bold green]")
                    correct_count += 1
                    
                    time.sleep(1.5)
                    break
                else:
                    incorrect_attempts += 1
                    colored_string = get_colored_notes_string(attempt_notes, chord_notes)
                    
                    found_chord, found_inversion = recognize_chord(attempt_notes)
                    
                    if found_chord:
                        console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {found_chord} ({found_inversion})")
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
                
                # Réinitialiser pour le prochain essai après vérification
                #attempt_notes.clear()
                last_note_off_time = None
            
            time.sleep(0.01)

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
        "I-IV-V": ["Do Majeur", "Fa Majeur", "Sol Majeur"],
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
    
    exit_flag = False
    
    while not exit_flag:
        for _ in inport.iter_pending():
            pass
        
        prog_name, progression, exemples = get_progression_choice(progression_selection_mode, inport, last_progression_name)
        if prog_name is None:
            exit_flag = True
            break
        
        last_progression_name = prog_name
        
        clear_screen()
        console.print(Panel(
            Text("Mode Progressions Pop/Rock", style="bold magenta", justify="center"),
            title="Progressions Pop/Rock",
            border_style="magenta"
        ))
        console.print(f"Type d'accords: [bold cyan]{'Tous' if chord_set == all_chords else 'Majeurs/Mineurs'}[/bold cyan]")
        console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer à la suivante.")
        
        console.print(f"\nProgression à jouer : [bold yellow]{' -> '.join(progression)}[/bold yellow]")
        if prog_name in exemples:
            console.print(f"Exemples : [bold blue]{exemples[0]}[/bold blue] et [bold blue]{exemples[1]}[/bold blue]")
        
        if play_progression_before_start:
            play_progression_sequence(outport, progression, chord_set)

        progression_correct_count = 0
        is_progression_started = False
        start_time = None
        elapsed_time = 0.0 # Initialisation de la variable
        skip_progression = False
        
        # Boucle principale pour la progression
        prog_index = 0
        while prog_index < len(progression) and not exit_flag and not skip_progression:
            chord_name = progression[prog_index]
            target_notes = chord_set[chord_name]
            console.print(f"Jouez l'accord [bold yellow]{chord_name}[/bold yellow]")
            
            notes_currently_on = set()
            attempt_notes = set()

            # Boucle pour chaque accord
            while not exit_flag and not skip_progression:
                if use_timer and is_progression_started:
                    remaining_time = timer_duration - (time.time() - start_time)
                    console.print(f"Temps restant : {remaining_time:.1f} secondes", end='\r', style="bold bright_cyan")
                    if remaining_time <= 0:
                        console.print(f"\n[bold red]Temps écoulé ! Session terminée.[/bold red]")
                        exit_flag = True
                        break

                char = wait_for_input(timeout=0.01)
                if char:
                    char = char.lower()
                    if char == 'q':
                        exit_flag = True
                        break
                    if char == 'r':
                        # Rejouer la progression depuis le début
                        play_progression_sequence(outport, progression, chord_set)
                        prog_index = 0
                        console.print(f"Reprenons. Jouez l'accord [bold yellow]{progression[prog_index]}[/bold yellow]")
                        break # Recommencer la boucle de l'accord
                    if char == 'n':
                        # Passer à la progression suivante
                        skip_progression = True
                        break

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
                    
                    if is_enharmonic_match(recognize_chord(attempt_notes)[0], chord_name, enharmonic_map) and len(attempt_notes) == len(chord_set[chord_name]):
                        colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                        console.print(f"Notes jouées : [{colored_notes}]")
                        console.print("[bold green]Correct ![/bold green]")
                        progression_correct_count += 1
                        prog_index += 1
                        break # Passer à l'accord suivant de la progression
                    else:
                        colored_string = get_colored_notes_string(attempt_notes, target_notes)
                        
                        found_chord, found_inversion = recognize_chord(attempt_notes)
                        
                        if found_chord:
                            console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {found_chord} ({found_inversion})")
                        else:
                            console.print("[bold red]Incorrect. Réessayez.[/bold red]")
                        
                        console.print(f"Notes jouées : [{colored_string}]")
                        attempt_notes.clear()
                
                time.sleep(0.01)

        # Fin de la progression
        if not exit_flag and not skip_progression:
            session_correct_count += progression_correct_count
            session_total_chords += len(progression)
            
            if use_timer and is_progression_started:
                end_time = time.time()
                elapsed_time = end_time - start_time
                console.print(f"\nTemps pour la progression : [bold cyan]{elapsed_time:.2f} secondes[/bold cyan]")
            
            Prompt.ask("\nProgression terminée ! Appuyez sur Entrée pour la suivante...", console=console)
        elif skip_progression:
            # Si l'utilisateur a skip, on ne met pas à jour les stats
            console.print("\n[bold yellow]Passage à la progression suivante.[/bold yellow]")
            time.sleep(1)

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
        console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer à la suivante.")
        
        prog_len = random.randint(3, 5)
        
        progression = random.sample(list(chord_set.keys()), prog_len)
        while progression == last_progression_accords:
            progression = random.sample(list(chord_set.keys()), prog_len)
        
        last_progression_accords = progression
        
        console.print(f"\nProgression à jouer : [bold yellow]{' -> '.join(progression)}[/bold yellow]")
        
        if play_progression_before_start:
            play_progression_sequence(outport, progression, chord_set)

        progression_correct_count = 0
        is_progression_started = False
        start_time = None
        elapsed_time = 0.0 # Initialisation de la variable
        skip_progression = False

        # Boucle principale pour la progression
        prog_index = 0
        while prog_index < len(progression) and not exit_flag and not skip_progression:
            chord_name = progression[prog_index]
            target_notes = chord_set[chord_name]
            console.print(f"Jouez l'accord [bold yellow]{chord_name}[/bold yellow]")
            
            notes_currently_on = set()
            attempt_notes = set()

            # Boucle pour chaque accord
            while not exit_flag and not skip_progression:
                if use_timer and is_progression_started:
                    remaining_time = timer_duration - (time.time() - start_time)
                    console.print(f"Temps restant : {remaining_time:.1f} secondes", end='\r', style="bold bright_cyan")
                    if remaining_time <= 0:
                        console.print(f"\n[bold red]Temps écoulé ! Session terminée.[/bold red]")
                        exit_flag = True
                        break
                    
                char = wait_for_input(timeout=0.01)
                if char:
                    char = char.lower()
                    if char == 'q':
                        exit_flag = True
                        break
                    if char == 'r':
                        # Rejouer la progression depuis le début
                        play_progression_sequence(outport, progression, chord_set)
                        prog_index = 0
                        console.print(f"Reprenons. Jouez l'accord [bold yellow]{progression[prog_index]}[/bold yellow]")
                        break
                    if char == 'n':
                        # Passer à la progression suivante
                        skip_progression = True
                        break

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

                    if is_enharmonic_match(recognize_chord(attempt_notes)[0], chord_name, enharmonic_map) and len(attempt_notes) == len(chord_set[chord_name]):
                        colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                        console.print(f"Notes jouées : [{colored_notes}]")
                        console.print("[bold green]Correct ![/bold green]")
                        progression_correct_count += 1
                        prog_index += 1
                        break
                    else:
                        colored_string = get_colored_notes_string(attempt_notes, target_notes)
                        
                        found_chord, found_inversion = recognize_chord(attempt_notes)
                        
                        if found_chord:
                            console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {found_chord} ({found_inversion})")
                        else:
                            console.print("[bold red]Incorrect. Réessayez.[/bold red]")
                        
                        console.print(f"Notes jouées : [{colored_string}]")
                        attempt_notes.clear()
                
                time.sleep(0.01)
            
            if exit_flag:
                break
            
        if not exit_flag and not skip_progression:
            session_correct_count += progression_correct_count
            session_total_chords += len(progression_accords)

            if use_timer and is_progression_started:
                end_time = time.time()
                elapsed_time = end_time - start_time
                console.print(f"\nTemps pour la progression : [bold cyan]{elapsed_time:.2f} secondes[/bold cyan]")
            
            Prompt.ask("\nProgression terminée ! Appuyez sur Entrée pour la suivante...", console=console)
        elif skip_progression:
            console.print("\n[bold yellow]Passage à la progression suivante.[/bold yellow]")
            time.sleep(1)

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
        console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer à la suivante.")
        
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
        
        display_degrees_table(tonalite, gammes_filtrees)

        console.print(f"\nDans la tonalité de [bold yellow]{tonalite}[/bold yellow], jouez la progression : [bold yellow]{' -> '.join(progression_accords)}[/bold yellow]")
        
        if play_progression_before_start:
            play_progression_sequence(outport, progression_accords, chord_set)

        progression_correct_count = 0
        is_progression_started = False
        start_time = None
        elapsed_time = 0.0 # Initialisation de la variable
        skip_progression = False

        # Boucle principale pour la progression
        prog_index = 0
        while prog_index < len(progression_accords) and not exit_flag and not skip_progression:
            chord_name = progression_accords[prog_index]
            target_notes = chord_set[chord_name]
            console.print(f"Jouez l'accord [bold yellow]{chord_name}[/bold yellow]")
            
            notes_currently_on = set()
            attempt_notes = set()
            
            # Boucle pour chaque accord
            while not exit_flag and not skip_progression:
                if use_timer and is_progression_started:
                    remaining_time = timer_duration - (time.time() - start_time)
                    console.print(f"Temps restant : {remaining_time:.1f} secondes", end='\r', style="bold bright_cyan")
                    if remaining_time <= 0:
                        console.print(f"\n[bold red]Temps écoulé ! Session terminée.[/bold red]")
                        exit_flag = True
                        break

                char = wait_for_input(timeout=0.01)
                if char:
                    char = char.lower()
                    if char == 'q':
                        exit_flag = True
                        break
                    if char == 'r':
                        # Rejouer la progression depuis le début
                        play_progression_sequence(outport, progression_accords, chord_set)
                        prog_index = 0
                        console.print(f"Reprenons. Jouez l'accord [bold yellow]{progression_accords[prog_index]}[/bold yellow]")
                        break
                    if char == 'n':
                        # Passer à la progression suivante
                        skip_progression = True
                        break

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

                    if is_enharmonic_match(recognize_chord(attempt_notes)[0], chord_name, enharmonic_map) and len(attempt_notes) == len(chord_set[chord_name]):
                        colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                        console.print(f"Notes jouées : [{colored_notes}]")
                        console.print("[bold green]Correct ![/bold green]")
                        progression_correct_count += 1
                        prog_index += 1
                        break
                    else:
                        colored_string = get_colored_notes_string(attempt_notes, target_notes)
                        
                        found_chord, found_inversion = recognize_chord(attempt_notes)
                        
                        if found_chord:
                            console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {found_chord} ({found_inversion})")
                        else:
                            console.print("[bold red]Incorrect. Réessayez.[/bold red]")
                        
                        console.print(f"Notes jouées : [{colored_string}]")
                        attempt_notes.clear()
                
                time.sleep(0.01)
            
            if exit_flag:
                break
            
        if not exit_flag and not skip_progression:
            session_correct_count += progression_correct_count
            session_total_chords += len(progression_accords)

            if use_timer and is_progression_started:
                end_time = time.time()
                elapsed_time = end_time - start_time
                console.print(f"\nTemps pour la progression : [bold cyan]{elapsed_time:.2f} secondes[/bold cyan]")
            
            Prompt.ask("\nProgression terminée ! Appuyez sur Entrée pour la suivante...", console=console)
        elif skip_progression:
            console.print("\n[bold yellow]Passage à la progression suivante.[/bold yellow]")
            time.sleep(1)

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
