# midi_handler.py
import mido
import time
import sys

# Importation des bibliothèques spécifiques à la plateforme pour la saisie non-bloquante
try:
    # Pour Windows
    import msvcrt
except ImportError:
    # Pour les systèmes Unix (Linux, macOS)
    import select
    import tty
    import termios

# Importation de Rich pour la sélection des ports
from rich.table import Table
from rich.prompt import Prompt

def select_midi_port(port_type, console):
    """
    Permet à l'utilisateur de choisir un port MIDI parmi la liste disponible.
    
    Args:
        port_type (str): "input" ou "output".
        console (rich.console.Console): L'instance de la console pour l'affichage.

    Returns:
        str | None: Le nom du port choisi, ou None si l'utilisateur quitte.
    """
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

def play_chord(outport, chord_notes, velocity=100, duration=0.5):
    """
    Joue un accord via MIDI.
    
    Args:
        outport (mido.ports.BaseOutput): Le port de sortie MIDI.
        chord_notes (iterable): Un ensemble ou une liste de numéros de notes MIDI.
        velocity (int): La vélocité des notes (0-127).
        duration (float): La durée pendant laquelle les notes sont maintenues (en secondes).
    """
    for note in chord_notes:
        msg = mido.Message('note_on', note=note, velocity=velocity)
        outport.send(msg)
    time.sleep(duration)
    for note in chord_notes:
        msg = mido.Message('note_off', note=note, velocity=0)
        outport.send(msg)

def play_progression_sequence(outport, progression, chord_set, console):
    """
    Joue une séquence d'accords.
    
    Args:
        outport (mido.ports.BaseOutput): Le port de sortie MIDI.
        progression (list): Une liste de noms d'accords.
        chord_set (dict): Le dictionnaire contenant les notes des accords.
        console (rich.console.Console): L'instance de la console pour afficher les messages.
    """
    console.print("[bold blue]Lecture de la progression...[/bold blue]")
    for chord_name in progression:
        if chord_name in chord_set:
            notes = chord_set[chord_name]
            # Affiche le nom de l'accord joué
            console.print(f"  -> Joue : [bold yellow]{chord_name}[/bold yellow]")
            play_chord(outport, notes, duration=0.8)
            time.sleep(0.3) # Petite pause entre les accords
        else:
            console.print(f"[bold red]L'accord '{chord_name}' n'a pas pu être joué (non trouvé).[/bold red]")

def wait_for_input(timeout=0.01):
    """
    Saisie de caractère non-bloquante, compatible Windows et Unix.
    
    Args:
        timeout (float): Le temps d'attente maximum en secondes.

    Returns:
        str | None: Le caractère saisi, ou None si le timeout est atteint.
    """
    if 'msvcrt' in sys.modules:
        if msvcrt.kbhit():
            return msvcrt.getch().decode('utf-8')
    else: # Pour Unix
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
    """
    Fonction bloquante qui attend n'importe quelle touche du clavier.
    Vide également le tampon des messages MIDI en attente pour éviter les
    notes "fantômes" au démarrage du mode suivant.
    
    Args:
        inport (mido.ports.BaseInput): Le port d'entrée MIDI, pour vider son tampon.
    """
    # Vider le tampon MIDI
    for _ in inport.iter_pending():
        pass
        
    # Attendre une touche du clavier
    if 'msvcrt' in sys.modules:
        msvcrt.getch()
    else: # Pour Unix
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)