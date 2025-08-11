# midi_handler.py
import time
import mido

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from data.chords import all_chords

console = Console()

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
    #console.print("[bold blue]Lecture de la progression...[/bold blue]")
    for chord_name in progression:
        # S'assurer que l'accord existe dans le jeu d'accords sélectionné
        if chord_name in chord_set:
            play_chord(outport, chord_set[chord_name], duration=0.8)
            time.sleep(0.5)
        else:
            console.print(f"[bold red]L'accord {chord_name} n'a pas pu être joué (non trouvé dans le set sélectionné).[/bold red]")

def recognize_chord(played_notes_set):
    """
    Reconnaît un accord à partir d'un ensemble de notes MIDI jouées.
    Cette version prend en compte la note la plus basse pour déterminer l'accord
    correct parmi les candidats possibles et son inversion.
    
    Args:
        played_notes_set (set): Un ensemble de numéros de notes MIDI.

    Returns:
        tuple: (Nom de l'accord reconnu, type de renversement)
               ou (None, None) si non reconnu.
    """
    if len(played_notes_set) < 2:
        return None, None

    played_notes_sorted = sorted(list(played_notes_set))
    lowest_note_midi = played_notes_sorted[0]
    played_pitch_classes = frozenset(note % 12 for note in played_notes_set)
    lowest_note_pc = lowest_note_midi % 12
    
    best_match = None
    lowest_inversion_index = float('inf')

    # Parcourir tous les accords pour trouver les candidats
    for chord_name, ref_notes in all_chords.items():
        ref_pitch_classes = frozenset(note % 12 for note in ref_notes)

        # Si les classes de hauteur des notes jouées correspondent à un accord de référence
        if played_pitch_classes == ref_pitch_classes:
            
            # Déterminer la classe de hauteur de la racine de l'accord de référence
            root_note_pc = min(ref_notes) % 12
            
            # Créer une liste ordonnée des classes de hauteur de l'accord,
            # en commençant par la racine (fondamentale)
            sorted_ref_pcs = sorted(list(ref_pitch_classes))
            root_index_in_sorted = sorted_ref_pcs.index(root_note_pc)
            ordered_chord_pcs = sorted_ref_pcs[root_index_in_sorted:] + sorted_ref_pcs[:root_index_in_sorted]
            
            # L'indice de la note la plus basse dans cette liste ordonnée
            # est l'indice du renversement
            try:
                inversion_index = ordered_chord_pcs.index(lowest_note_pc)
            except ValueError:
                # Cela ne devrait pas arriver si les sets de pitch classes correspondent
                continue

            # Mettre à jour le meilleur accord s'il a un renversement plus bas
            if inversion_index < lowest_inversion_index:
                lowest_inversion_index = inversion_index
                best_match = (chord_name, inversion_index)

    if best_match:
        chord_name, inversion_index = best_match
        inversion_labels = ["position fondamentale", "1er renversement", "2ème renversement", "3ème renversement", "4ème renversement"]
        inversion_label = inversion_labels[inversion_index] if inversion_index < len(inversion_labels) else ""
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
