# midi_handler.py
import time
import mido

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from data.chords import all_chords
from messages import Midi

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

def get_closest_inversion(target_notes, last_notes=None):
    """
    Trouve l'inversion d'un accord qui est la plus proche du dernier accord joué.
    Retourne l'ensemble de notes MIDI pour cette inversion.
    """
    if last_notes is None:
        # Si c'est le premier accord, le centrer autour de la note MIDI 60 (Do4)
        target_bass_note = min(target_notes)
        octave_shift = (60 - target_bass_note) // 12
        return {note + (octave_shift * 12) for note in target_notes}

    # Créer toutes les inversions possibles de l'accord sur une plage de deux octaves
    inversions = []
    base_notes = sorted(list(target_notes))
    
    # Inversions dans l'octave de base
    inversions.append(set(base_notes))
    inversions.append(set([base_notes[1], base_notes[2], base_notes[0] + 12]))
    
    # Inversions dans l'octave inférieure
    inversions.append(set([n - 12 for n in base_notes]))
    inversions.append(set([base_notes[1] - 12, base_notes[2] - 12, base_notes[0]]))
    
    # Inversions dans l'octave supérieure
    inversions.append(set([n + 12 for n in base_notes]))
    inversions.append(set([base_notes[1] + 12, base_notes[2] + 12, base_notes[0] + 24]))

    last_notes_set = set(last_notes)
    min_distance = float('inf')
    best_inversion = None

    for inversion in inversions:
        distance = sum(abs(note - last_note) for note in inversion for last_note in last_notes_set)
        if distance < min_distance:
            min_distance = distance
            best_inversion = inversion

    return best_inversion

def play_progression_sequence(outport, progression, chord_set, duration=0.8):
    """Joue une séquence d'accords."""
    last_played_notes = None
    for chord_name in progression:
        if chord_name in chord_set:
            target_notes = chord_set[chord_name]
            
            # Utiliser la nouvelle fonction pour trouver la meilleure inversion
            transposed_notes = get_closest_inversion(target_notes, last_played_notes)
            
            play_chord(outport, transposed_notes, duration=duration)
            last_played_notes = transposed_notes
            time.sleep(0.5)
        else:
            console.print(Midi.CHORD_NOT_PLAYED.format(chord_name=chord_name))


def select_midi_port(port_type):
    """Permet à l'utilisateur de choisir un port MIDI parmi la liste disponible."""
    ports = mido.get_input_names() if port_type == "input" else mido.get_output_names()
    
    if not ports:
        console.print(Midi.NO_PORT_FOUND.format(port_type=port_type))
        return None
    
    table = Table(title=Midi.AVAILABLE_PORTS.format(port_type=port_type), style="bold cyan")
    table.add_column(Midi.PORT_INDEX_COLUMN, style="bold yellow")
    table.add_column(Midi.PORT_NAME_COLUMN, style="bold white")

    for i, port_name in enumerate(ports):
        table.add_row(f"[{i+1}]", port_name)
    table.add_row("[q]", Midi.QUIT)
    
    console.print(table)
    
    while True:
        choice = Prompt.ask(Midi.CHOOSE_PORT.format(port_type=port_type, port_count=len(ports)), console=console)
        if choice.lower() == 'q':
            return None
        try:
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(ports):
                return ports[choice_index]
            else:
                console.print(Midi.INVALID_SELECTION_NUMBER)
        except ValueError:
            console.print(Midi.INVALID_SELECTION_INPUT)

def play_note_sequence(outport, notes, velocity=64, duration=0.3, pause=0.1):
    """Joue une séquence de notes individuellement."""
    for note in notes:
        outport.send(mido.Message('note_on', note=note, velocity=velocity))
        time.sleep(duration)
        outport.send(mido.Message('note_off', note=note, velocity=velocity))
        time.sleep(pause)