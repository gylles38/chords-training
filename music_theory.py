# music_theory.py

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
        inversion_label = inversion_labels[inversion_index] if inversion_index < len(inversion_labels) else ""
        return chord_name, inversion_label
    
    return None, None

def is_enharmonic_match_improved(played_chord_name, target_chord_name, all_chords_dict=None):
    """
    Version améliorée qui compare les classes de hauteur plutôt que les noms.
    Cette fonction est plus robuste car elle détecte automatiquement toutes
    les équivalences enharmoniques sans avoir besoin de les lister manuellement.
    """
    if all_chords_dict is None:
        from data.chords import all_chords
        all_chords_dict = all_chords
    
    if played_chord_name == target_chord_name:
        return True
    
    # Si l'un des deux accords n'existe pas, pas de correspondance
    if not played_chord_name or not target_chord_name:
        return False
    if played_chord_name not in all_chords_dict or target_chord_name not in all_chords_dict:
        return False
    
    # Comparer les classes de hauteur (indépendamment de l'octave)
    played_pitch_classes = {note % 12 for note in all_chords_dict[played_chord_name]}
    target_pitch_classes = {note % 12 for note in all_chords_dict[target_chord_name]}
    
    return played_pitch_classes == target_pitch_classes

def get_chord_type_from_name(chord_name):
    """Extrait le type d'accord (Majeur, Mineur, 7ème, etc.) du nom de l'accord."""
    chord_types = ["Majeur", "Mineur", "7ème", "Diminué", "4ème", "6ème"]
    for c_type in chord_types:
        if c_type in chord_name:
            return c_type
    return "Inconnu" # Fallback pour les types non listés
