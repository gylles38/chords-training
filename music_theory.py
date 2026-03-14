# music_theory.py

def get_note_name_with_octave(midi_note):
    """Convertit un numéro de note MIDI en son nom avec l'octave (bilingue)."""
    notes_fr = ["Do", "Do#", "Ré", "Ré#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
    notes_en = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = (midi_note // 12) - 1
    idx = midi_note % 12
    return f"{notes_fr[idx]}{octave}({notes_en[idx]}{octave})"

def get_note_name(midi_note):
    """Convertit un numéro de note MIDI en son nom (bilingue)."""
    notes_fr = ["Do", "Do#", "Ré", "Ré#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
    notes_en = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    idx = midi_note % 12
    return f"{notes_fr[idx]}({notes_en[idx]})"

def get_chord_display_name(french_name):
    """Convertit un nom d'accord français en format bilingue français(anglais)."""
    if not french_name:
        return ""

    if "(" in french_name and ")" in french_name:
        return french_name

    english_name = french_name

    # Mapping des notes
    note_map = {
        "Do": "C",
        "Ré": "D",
        "Mi": "E",
        "Fa": "F",
        "Sol": "G",
        "La": "A",
        "Si": "B"
    }

    # Remplacer les altérations
    english_name = english_name.replace(" dièse", "#").replace(" bémol", "b")

    # Remplacer les noms de notes
    for fr, en in note_map.items():
        if english_name.startswith(fr):
            english_name = en + english_name[len(fr):]
            break

    # Remplacer les types d'accords
    english_name = english_name.replace(" Majeur 7ème", "maj7")
    english_name = english_name.replace(" Mineur 7ème", "m7")
    english_name = english_name.replace(" Majeur", "")
    english_name = english_name.replace(" Mineur", "m")
    english_name = english_name.replace(" Diminué", "dim")
    english_name = english_name.replace(" 7ème", "7")
    english_name = english_name.replace(" 4ème", "sus4")
    english_name = english_name.replace(" 6ème", "6")

    return f"{french_name}({english_name})"

def recognize_chord(played_notes_set):
    """
    Reconnaît un accord à partir d'un ensemble de notes MIDI jouées.
    Supporte les accords de 7ème simplifiés (3 notes au lieu de 4).
    
    Args:
        played_notes_set (set): Un ensemble de numéros de notes MIDI.

    Returns:
        tuple: (Nom de l'accord reconnu, type de renversement, is_simplified)
               ou (None, None, False) si non reconnu.
    """
    from data.chords import all_chords
    
    if len(played_notes_set) < 2:
        return None, None, False

    played_notes_sorted = sorted(list(played_notes_set))
    lowest_note_midi = played_notes_sorted[0]
    played_pitch_classes = frozenset(note % 12 for note in played_notes_set)
    lowest_note_pc = lowest_note_midi % 12
    
    best_match = None
    best_is_simplified = False
    lowest_inversion_index = float('inf')

    for chord_name, ref_notes in all_chords.items():
        ref_pitch_classes = frozenset(note % 12 for note in ref_notes)
        root_note_pc = min(ref_notes) % 12

        is_match = False
        is_simplified = False

        # 1. Correspondance exacte
        if played_pitch_classes == ref_pitch_classes:
            is_match = True
        # 2. Correspondance simplifiée (pour les accords de 7ème à 4 notes)
        elif len(ref_notes) == 4 and "7ème" in chord_name and len(played_notes_set) == 3:
            # L'accord simplifié doit contenir la tonique et être un sous-ensemble de l'accord complet
            if root_note_pc in played_pitch_classes and played_pitch_classes.issubset(ref_pitch_classes):
                is_match = True
                is_simplified = True

        if is_match:
            # Pour les inversions, on se base sur l'accord de référence
            sorted_ref_pcs = sorted(list(ref_pitch_classes))
            root_index_in_sorted = sorted_ref_pcs.index(root_note_pc)
            ordered_chord_pcs = sorted_ref_pcs[root_index_in_sorted:] + sorted_ref_pcs[:root_index_in_sorted]
            
            try:
                inversion_index = ordered_chord_pcs.index(lowest_note_pc)
            except ValueError:
                # Dans le cas d'un accord simplifié, la note basse pourrait ne pas être dans l'ordre de référence ?
                # Normalement si c'est un subset et que la note basse est dedans, ça marche.
                continue

            # Priorité aux matchs non simplifiés, puis au renversement le plus bas
            if (not best_is_simplified and is_simplified) and best_match:
                continue

            if is_simplified and not best_is_simplified:
                # Premier match simplifié trouvé
                best_match = (chord_name, inversion_index)
                best_is_simplified = True
                lowest_inversion_index = inversion_index
            elif (is_simplified == best_is_simplified):
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
        return chord_name, inversion_label, best_is_simplified
    
    return None, None, False

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
