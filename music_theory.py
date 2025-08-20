# music_theory.py

def get_note_name_with_octave(midi_note):
    """Convertit un numéro de note MIDI en son nom avec l'octave."""
    notes = ["Do", "Do#", "Ré", "Ré#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
    octave = (midi_note // 12) - 1
    note_name = notes[midi_note % 12]
    return f"{note_name}{octave}"

def get_note_name(midi_note):
    """Convertit un numéro de note MIDI en son nom."""
    notes = ["Do", "Do#", "Ré", "Ré#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
    return notes[midi_note % 12]

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
    # Import local pour éviter la dépendance circulaire
    from data.chords import all_chords
    
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
        if 0 <= inversion_index < len(inversion_labels):
            inversion_label = inversion_labels[inversion_index]
        else:
            inversion_label = f"{inversion_index + 1}ème renversement"
        return chord_name, inversion_label
    
    return None, None

def are_chord_names_enharmonically_equivalent(name1, name2):
    """
    Vérifie si deux noms d'accords sont équivalents de manière enharmonique.
    """
    from data.chords import all_chords
    if name1 not in all_chords or name2 not in all_chords:
        return False
    
    return {n % 12 for n in all_chords[name1]} == {n % 12 for n in all_chords[name2]}

def get_chord_type_from_name(chord_name):
    """Extrait le type d'accord (Majeur, Mineur, 7ème, etc.) du nom de l'accord."""
    chord_types = ["Majeur", "Mineur", "7ème", "Diminué", "4ème", "6ème"]
    for c_type in chord_types:
        if c_type in chord_name:
            return c_type
    return "Inconnu" # Fallback pour les types non listés

def get_inversion_name(chord_name, chord_notes):
    """
    Détermine le nom du renversement pour un accord donné et un ensemble de notes.
    """
    from data.chords import all_chords
    if chord_name not in all_chords or not chord_notes:
        return ""

    ref_notes = all_chords[chord_name]
    ref_pitch_classes = {n % 12 for n in ref_notes}

    # Trouver la classe de hauteur de la fondamentale
    root_pc = min(ref_notes) % 12

    # Créer une liste ordonnée des classes de hauteur de l'accord
    sorted_ref_pcs = sorted(list(ref_pitch_classes))
    root_index_in_sorted = sorted_ref_pcs.index(root_pc)
    ordered_chord_pcs = sorted_ref_pcs[root_index_in_sorted:] + sorted_ref_pcs[:root_index_in_sorted]

    # Trouver la note la plus basse du renversement joué
    lowest_note_pc = min(chord_notes) % 12

    try:
        inversion_index = ordered_chord_pcs.index(lowest_note_pc)
    except ValueError:
        return "" # La note basse ne correspond pas à l'accord

    inversion_labels = ["position fondamentale", "1er renversement", "2ème renversement", "3ème renversement", "4ème renversement"]
    if 0 <= inversion_index < len(inversion_labels):
        return inversion_labels[inversion_index]
    else:
        return f"{inversion_index + 1}ème renversement"


SCALE_INTERVALS = {
    'major': [2, 2, 1, 2, 2, 2, 1],
    'natural_minor': [2, 1, 2, 2, 1, 2, 2],
    'harmonic_minor': [2, 1, 2, 2, 1, 3, 1],
    'melodic_minor_asc': [2, 1, 2, 2, 2, 2, 1],
}

def generate_scale(root_note: int, scale_type: str) -> list[int] | None:
    """
    Generates a scale from a root note and a scale type.
    Returns a list of MIDI notes for one octave (including the octave note).
    """
    if scale_type == 'melodic_minor_desc':
        intervals = SCALE_INTERVALS['natural_minor']
    elif scale_type in SCALE_INTERVALS:
        intervals = SCALE_INTERVALS[scale_type]
    else:
        return None

    scale = [root_note]
    current_note = root_note
    # The intervals define the steps to the next note. A 7-interval list defines an 8-note scale (octave included).
    for interval in intervals:
        current_note += interval
        scale.append(current_note)

    return scale
