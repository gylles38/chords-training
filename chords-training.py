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
from rich.live import Live

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

# NOUVEAU : Dictionnaire d'alias pour le mode Explorateur
# Fait le lien entre une saisie utilisateur simple et le nom complet de l'accord.
chord_aliases = {
    # Majeur (ex: "c", "C", "cmaj")
    "c": "Do Majeur", "cmaj": "Do Majeur",
    "c#": "Do dièse Majeur", "c#maj": "Do dièse Majeur", "db": "Ré bémol Majeur", "dbmaj": "Ré bémol Majeur",
    "d": "Ré Majeur", "dmaj": "Ré Majeur",
    "d#": "Mi bémol Majeur", "d#maj": "Mi bémol Majeur", "eb": "Mi bémol Majeur", "ebmaj": "Mi bémol Majeur",
    "e": "Mi Majeur", "emaj": "Mi Majeur",
    "f": "Fa Majeur", "fmaj": "Fa Majeur",
    "f#": "Fa dièse Majeur", "f#maj": "Fa dièse Majeur", "gb": "Sol bémol Majeur", "gbmaj": "Sol bémol Majeur",
    "g": "Sol Majeur", "gmaj": "Sol Majeur",
    "g#": "La bémol Majeur", "g#maj": "La bémol Majeur", "ab": "La bémol Majeur", "abmaj": "La bémol Majeur",
    "a": "La Majeur", "amaj": "La Majeur",
    "a#": "Si bémol Majeur", "a#maj": "Si bémol Majeur", "bb": "Si bémol Majeur", "bbmaj": "Si bémol Majeur",
    "b": "Si Majeur", "bmaj": "Si Majeur",
    
    # Mineur (ex: "cm", "C-", "cmin")
    "cm": "Do Mineur", "c-": "Do Mineur", "cmin": "Do Mineur",
    "c#m": "Do dièse Mineur", "c#-": "Do dièse Mineur", "dbm": "Do dièse Mineur",
    "dm": "Ré Mineur", "d-": "Ré Mineur", "dmin": "Ré Mineur",
    "d#m": "Ré dièse Mineur", "d#-": "Ré dièse Mineur", "ebm": "Mi bémol Mineur",
    "em": "Mi Mineur", "e-": "Mi Mineur", "emin": "Mi Mineur",
    "fm": "Fa Mineur", "f-": "Fa Mineur", "fmin": "Fa Mineur",
    "f#m": "Fa dièse Mineur", "f#-": "Fa dièse Mineur", "gbm": "Fa dièse Mineur",
    "gm": "Sol Mineur", "g-": "Sol Mineur", "gmin": "Sol Mineur",
    "g#m": "Sol dièse Mineur", "g#-": "Sol dièse Mineur", "abm": "La bémol Mineur",
    "am": "La Mineur", "a-": "La Mineur", "amin": "La Mineur",
    "a#m": "La dièse Mineur", "a#-": "La dièse Mineur", "bbm": "Si bémol Mineur",
    "bm": "Si Mineur", "b-": "Si Mineur", "bmin": "Si Mineur",
    
    # 7ème de dominante (ex: "c7")
    "c7": "Do 7ème", "c#7": "Do dièse 7ème", "db7": "Do dièse 7ème", # Note: C#7 et Db7 ne sont pas dans la liste initiale, mais on peut les ajouter
    "d7": "Ré 7ème", "d#7": "Mi bémol 7ème", "eb7": "Mi bémol 7ème",
    "e7": "Mi 7ème", "f7": "Fa 7ème", "f#7": "Fa dièse 7ème", "gb7": "Fa dièse 7ème",
    "g7": "Sol 7ème", "g#7": "La bémol 7ème", "ab7": "La bémol 7ème",
    "a7": "La 7ème", "a#7": "Si bémol 7ème", "bb7": "Si bémol 7ème",
    "b7": "Si 7ème",

    # 7ème Majeur (ex: "cmaj7")
    "cmaj7": "Do Majeur 7ème", "c#maj7": "Ré bémol Majeur 7ème", "dbmaj7": "Ré bémol Majeur 7ème",
    "dmaj7": "Ré Majeur 7ème", "ebmaj7": "Mi bémol Majeur 7ème", "emaj7": "Mi Majeur 7ème",
    "fmaj7": "Fa Majeur 7ème", "f#maj7": "Sol bémol Majeur 7ème", "gbmaj7": "Sol bémol Majeur 7ème",
    "gmaj7": "Sol Majeur 7ème", "abmaj7": "La bémol Majeur 7ème", "amaj7": "La Majeur 7ème",
    "bbmaj7": "Si bémol Majeur 7ème", "bmaj7": "Si Majeur 7ème",
    
    # 7ème Mineur (ex: "cm7")
    "cm7": "Do Mineur 7ème", "c#m7": "Ré bémol Mineur 7ème", "dbm7": "Ré bémol Mineur 7ème",
    "dm7": "Ré Mineur 7ème", "d#m7": "Ré dièse Mineur 7ème", "ebm7": "Mi bémol Mineur 7ème",
    "em7": "Mi Mineur 7ème", "fm7": "Fa Mineur 7ème", "f#m7": "Fa dièse Mineur 7ème",
    "gm7": "Sol Mineur 7ème", "g#m7": "La bémol Mineur 7ème", "abm7": "La bémol Mineur 7ème",
    "am7": "La Mineur 7ème", "a#m7": "Si bémol Mineur 7ème", "bbm7": "Si bémol Mineur 7ème",
    "bm7": "Si Mineur 7ème",

    # Diminué (ex: "cdim")
    "cdim": "Do Diminué", "c#dim": "Do dièse Diminué", "ddim": "Ré Diminué", "d#dim": "Ré dièse Diminué",
    "edim": "Mi Diminué", "fdim": "Fa Diminué", "f#dim": "Fa dièse Diminué", "gdim": "Sol Diminué",
    "g#dim": "Sol dièse Diminué", "adim": "La Diminué", "a#dim": "Si bémol Diminué", "bbdim": "Si bémol Diminué",
    "bdim": "Si Diminué",
    
    # --- Accords de 4ème (sus4) ---
    "c4": "Do 4ème", "csus4": "Do 4ème",
    "d4": "Ré 4ème", "dsus4": "Ré 4ème",
    "e4": "Mi 4ème", "esus4": "Mi 4ème",
    "f4": "Fa 4ème", "fsus4": "Fa 4ème",
    "g4": "Sol 4ème", "gsus4": "Sol 4ème",
    "a4": "La 4ème", "asus4": "La 4ème",
    "b4": "Si 4ème", "bsus4": "Si 4ème",

    # --- Accords de 6ème (add6) ---
    "c6": "Do 6ème",
    "d6": "Ré 6ème",
    "e6": "Mi 6ème",
    "f6": "Fa 6ème",
    "g6": "Sol 6ème",
    "a6": "La 6ème",
    "b6": "Si 6ème",

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

# Définition des cadences par leurs degrés romains
cadences = {
    "Cadence Parfaite": ["V", "I"],
    "Cadence Plagale": ["IV", "I"],
    "Cadence Rompue": ["V", "vi"],
    "Demi-Cadence": ["IV", "V"],
    "Progression II-V-I": ["ii", "V", "I"]
}

# Dictionnaire pour mapper les degrés romains à un index de la liste de gamme (0-6)
DEGREE_MAP = {'I': 0, 'ii': 1, 'iii': 2, 'IV': 3, 'V': 4, 'vi': 5, 'vii°': 6}


# --- Exemples de progressions d'accords et de chansons ---
progression_examples = {
    # Exemples pour le mode Progression
    "Do Majeur, Sol Majeur, La Mineur, Fa Majeur": ["'Let It Be' - The Beatles", "'Don't Stop Believin'' - Journey", "'Take On Me' - a-ha", "'With or Without You' - U2"],
    "Do Majeur, Fa Majeur, Sol Majeur": ["'La Bamba' - Ritchie Valens", "'Twist and Shout' - The Beatles", "'Louie Louie' - The Kingsmen"],
    "La Mineur, Mi Mineur, Fa Majeur, Do Majeur": ["'Californication' - Red Hot Chili Peppers", "'Don't Look Back in Anger' - Oasis"],
}

# Nouvelles progressions pour le mode Pop/Rock
pop_rock_progressions = {
    "1": {
        "progression": ["Do Majeur", "Sol Majeur", "La Mineur", "Fa Majeur"],
        "examples": ["'Let It Be' - The Beatles", "'Don't Stop Believin'' - Journey", "'Take On Me' - a-ha"]
    },
    "2": {
        "progression": ["Do Majeur", "La Mineur", "Fa Majeur", "Sol Majeur"],
        "examples": ["'No Woman, No Cry' - Bob Marley", "'Stand By Me' - Ben E. King", "'I'm Yours' - Jason Mraz"]
    },
    "3": {
        "progression": ["Sol Majeur", "Ré Majeur", "Mi Mineur", "Do Majeur"],
        "examples": ["'With or Without You' - U2", "'Wake Me Up When September Ends' - Green Day"]
    },
    "4": {
        "progression": ["Mi Mineur", "Do Majeur", "Sol Majeur", "Ré Majeur"],
        "examples": ["'All of Me' - John Legend", "'Apologize' - OneRepublic"]
    },
}

tonal_progressions = {
    "Cadence Parfaite": ["I", "V", "I"],
    "Cadence Plagale": ["IV", "I"],
    "Progression I-IV-V-I": ["I", "IV", "V", "I"],
    "Progression ii-V-I": ["ii", "V", "I"],
    "Progression I-V-vi-IV": ["I", "V", "vi", "IV"]  # Très courante en pop
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

def is_enharmonic_match_improved(played_chord_name, target_chord_name, all_chords_dict):
    """
    Version améliorée qui compare les classes de hauteur plutôt que les noms.
    Cette fonction est plus robuste car elle détecte automatiquement toutes
    les équivalences enharmoniques sans avoir besoin de les lister manuellement.
    """
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

def safe_format_chord_info(chord_name, inversion):
    """Formate de manière sécurisée les informations d'accord"""
    if not chord_name:
        return "Accord non reconnu"
    
    # Nettoyer les caractères problématiques
    safe_name = str(chord_name).replace('%', 'pct').replace('{', '(').replace('}', ')')
    safe_inversion = str(inversion) if inversion else "position inconnue"
    safe_inversion = safe_inversion.replace('%', 'pct').replace('{', '(').replace('}', ')')
    
    return f"{safe_name} ({safe_inversion})"

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
        console.print("Aucun accord ou progression d'accords n'a été joué.")
    if elapsed_time is not None:
        console.print(f"Temps écoulé : [bold cyan]{elapsed_time:.2f} secondes[/bold cyan]")
    console.print("-------------------------")

def display_stats_fixed(correct_count, total_attempts, total_chords, elapsed_time=None):
    """Affiche les statistiques de performance corrigées."""
    console.print("\n--- Bilan de la session ---")
    if total_attempts > 0:
        accuracy = (correct_count / total_attempts) * 100
        console.print(f"Tentatives totales : [bold yellow]{total_attempts}[/bold yellow]")
        console.print(f"Tentatives réussies : [bold green]{correct_count}[/bold green]")
        console.print(f"Tentatives échouées : [bold red]{total_attempts - correct_count}[/bold red]")
        console.print(f"Précision globale : [bold cyan]{accuracy:.2f}%[/bold cyan]")
        
        if total_chords > 0:
            avg_attempts_per_chord = total_attempts / total_chords
            console.print(f"Moyenne tentatives/accord : [bold magenta]{avg_attempts_per_chord:.1f}[/bold magenta]")
    else:
        console.print("Aucune tentative enregistrée.")
    
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

# NOUVEAU: Mode Explorateur d'Accords
def chord_explorer_mode(outport):
    """Mode dictionnaire : l'utilisateur saisit un nom d'accord, le programme le joue et affiche ses notes."""
    clear_screen()
    console.print(Panel(
        Text("Mode Explorateur d'Accords", style="bold bright_blue", justify="center"),
        title="Dictionnaire d'accords",
        border_style="bright_blue"
    ))
    console.print("Entrez un nom d'accord pour voir ses notes et l'entendre.")
    console.print("Exemples : [cyan]C, F#m, Gm7, Bb, Ddim[/cyan]")

    while True:
        try:
            user_input = Prompt.ask("\n[prompt.label]Accord à trouver (ou 'q' pour quitter)[/prompt.label]")
            if user_input.lower() == 'q':
                break

            # Normaliser la saisie pour la recherche (minuscules, sans espaces)
            lookup_key = user_input.lower().replace(" ", "")
            full_chord_name = chord_aliases.get(lookup_key)

            if full_chord_name and full_chord_name in all_chords:
                # Accord trouvé
                chord_notes_midi = all_chords[full_chord_name]
                
                # Trier les notes pour un affichage logique (Tonique, Tierce, Quinte...)
                sorted_notes_midi = sorted(list(chord_notes_midi))
                
                # Obtenir le nom des notes
                note_names = [get_note_name(n) for n in sorted_notes_midi]
                notes_str = ", ".join(note_names)

                console.print(f"L'accord [bold green]{full_chord_name}[/bold green] est composé des notes : [bold yellow]{notes_str}[/bold yellow]")
                console.print("Lecture de l'accord...")
                play_chord(outport, chord_notes_midi, duration=1.2) # Joue l'accord un peu plus longtemps
            else:
                # Accord non trouvé
                console.print(f"[bold red]Accord '{user_input}' non reconnu.[/bold red] Veuillez réessayer.")

        except Exception as e:
            console.print(f"[bold red]Une erreur est survenue : {e}[/bold red]")
            time.sleep(2)

    console.print("\nRetour au menu principal.")
    time.sleep(1)


def single_chord_mode(inport, outport, chord_set):
    """Mode Accord Simple. 
    L'utilisateur doit jouer le bon accord pour passer au suivant.
    """
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

        # Choisir un nouvel accord différent du précédent
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
                recognized_name, recognized_inversion = recognize_chord(attempt_notes)
                
                if recognized_name and is_enharmonic_match_improved(recognized_name, chord_name, all_chords) \
                   and len(attempt_notes) == len(chord_notes):
                    colored_notes = get_colored_notes_string(attempt_notes, chord_notes)
                    console.print(f"Notes jouées : [{colored_notes}]")
                    console.print("[bold green]Correct ![/bold green]")
                    correct_count += 1
                    total_count += 1
                    time.sleep(2)  # Pause avant le prochain accord
                    break
                else:
                    colored_string = get_colored_notes_string(attempt_notes, chord_notes)
                    found_chord, found_inversion = recognize_chord(attempt_notes)
                    
                    if found_chord:
                        console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {found_chord} ({found_inversion})")
                    else:
                        console.print("[bold red]Incorrect. Réessayez.[/bold red]")

                    console.print(f"Notes jouées : [{colored_string}]")
                    total_count += 1
                    attempt_notes.clear()  # Réinitialiser pour le prochain essai
                    
            time.sleep(0.01)
        
    # Affichage des statistiques de la session
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
                #if is_enharmonic_match(recognized_name, chord_name, enharmonic_map) and len(attempt_notes) == len(chord_notes):
                if recognized_name and (is_enharmonic_match_improved(recognized_name, chord_name, enharmonic_map)) and len(attempt_notes) == len(chord_notes):                    
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
                last_note_off_time = None
            
            time.sleep(0.01)

    display_stats(correct_count, total_attempts)
    console.print("\nAppuyez sur une touche pour retourner au menu principal.")
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)

def pop_rock_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set):
    """
    Mode d'entraînement Pop/Rock avec des progressions d'accords courantes.
    Permet de jouer plusieurs progressions à la suite.
    """
    # Boucle principale pour permettre de jouer plusieurs progressions.
    while True:
        clear_screen()
        console.print(Panel(
            Text("Mode Pop/Rock", style="bold cyan", justify="center"),
            title="Entraînement Pop/Rock", border_style="cyan"
        ))

        # Afficher les progressions et les exemples
        table = Table(title="Progressions Pop/Rock", style="bold blue")
        table.add_column("Numéro", style="cyan")
        table.add_column("Progression", style="magenta")
        table.add_column("Exemples de chansons", style="yellow")

        for num, data in pop_rock_progressions.items():
            prog_str = " -> ".join(data["progression"])
            examples_str = "\n".join(data["examples"])
            table.add_row(num, prog_str, examples_str)
        console.print(table)

        # Demander à l'utilisateur de choisir une progression ou de quitter
        prog_choices = list(pop_rock_progressions.keys())
        prog_choice = Prompt.ask("Choisissez une progression (numéro) ou entrez 'q' pour retourner au menu", choices=prog_choices + ['q'])

        if prog_choice.lower() == 'q':
            break  # Quitte la boucle principale du mode

        selected_progression_data = pop_rock_progressions.get(prog_choice)
        current_progression = selected_progression_data["progression"]

        prog_str = " -> ".join(current_progression)
        console.print(f"\nProgression sélectionnée: [bold yellow]{prog_str}[/bold yellow]")

        if play_progression_before_start:
            play_progression_sequence(outport, current_progression, all_chords)

        notes_currently_on = set()
        attempt_notes = set()
        start_time = None
        user_quit_in_game = False

        console.print("\n[bold green]La progression commence. Jouez l'accord affiché.[/bold green]")

        def update_live_display(time_elapsed, progression_index, current_progression):
            panel_content = Text(
                f"Accord à jouer : [bold yellow]{current_progression[progression_index]}[/bold yellow]\n"
                f"Temps écoulé : [bold magenta]{time_elapsed:.1f}s[/bold magenta]",
                justify="center"
            )
            return Panel(panel_content, title="Progression en cours", border_style="green")

        with Live(console=console, screen=False, auto_refresh=False) as live:
            progression_index = 0
            while progression_index < len(current_progression):
                if use_timer:
                    if start_time is None:
                        start_time = time.time()
                    time_elapsed = time.time() - start_time
                    live.update(update_live_display(time_elapsed, progression_index, current_progression), refresh=True)

                    if time_elapsed > timer_duration:
                        live.stop()
                        console.print(f"[bold red]\nTemps écoulé ! L'accord était {current_progression[progression_index]}.[/bold red]")
                        progression_index += 1
                        start_time = None
                        if progression_index < len(current_progression):
                            console.print(f"Passage à l'accord suivant : [bold yellow]{current_progression[progression_index]}[/bold yellow]")
                        live.start()
                else:
                    live.update(Panel(f"Accord à jouer : [bold yellow]{current_progression[progression_index]}[/bold yellow]", title="Progression en cours", border_style="green"), refresh=True)
                
                for msg in inport.iter_pending():
                    if msg.type == 'note_on' and msg.velocity > 0:
                        notes_currently_on.add(msg.note)
                        attempt_notes.add(msg.note)
                    elif msg.type == 'note_off':
                        notes_currently_on.discard(msg.note)

                if not notes_currently_on and attempt_notes:
                    played_chord_name, _ = recognize_chord(attempt_notes)
                    target_chord_name = current_progression[progression_index]

                    if played_chord_name and (is_enharmonic_match_improved(played_chord_name, target_chord_name, enharmonic_map) or played_chord_name == target_chord_name):
                        live.update(f"[bold green]Correct ! {target_chord_name}[/bold green]", refresh=True)
                        time.sleep(1) # Pause pour voir le message
                        progression_index += 1
                        start_time = None
                        if progression_index >= len(current_progression):
                            break
                    else:
                        live.update(f"[bold red]Incorrect.[/bold red] Vous avez joué : {played_chord_name if played_chord_name else 'Accord non reconnu'}", refresh=True)
                        time.sleep(1) # Pause pour voir le message
                    
                    attempt_notes.clear()
                
                char = wait_for_input(timeout=0.01)
                if char and char.lower() == 'q':
                    user_quit_in_game = True
                    break
                
                time.sleep(0.01)

        if user_quit_in_game:
            break # Quitte la boucle principale du mode

        # Ce message s'affiche uniquement si la progression est terminée.
        console.print("[bold green]Progression terminée ![/bold green]")
        
        # Nouveau comportement simplifié
        choice = Prompt.ask(
            "\nProgression terminée ! Appuyez sur Entrée pour choisir une autre progression ou 'q' pour revenir au menu principal...", 
            console=console, 
            choices=["", "q"], 
            show_choices=False
        )
        if choice == 'q':
            break # Quitte la boucle principale du mode

    # Message de sortie du mode
    console.print("\nFin du mode Progression Pop/Rock.")
    console.print("Appuyez sur une touche pour revenir au menu principal.")
    wait_for_any_key(inport)

def progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    """Mode d'entraînement sur des progressions d'accords."""

    session_correct_count = 0
    session_total_count = 0
    session_total_attempts = 0
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
        progression_total_attempts = 0
        is_progression_started = False
        start_time = None
        elapsed_time = 0.0
        skip_progression = False

        # Fonction pour créer l'affichage live
        def create_live_display(chord_name, prog_index, total_chords, time_info=""):
            content = f"Accord à jouer ({prog_index + 1}/{total_chords}): [bold yellow]{chord_name}[/bold yellow]"
            if time_info:
                content += f"\n{time_info}"
            return Panel(content, title="Progression en cours", border_style="green")

        # Boucle principale avec Live display
        with Live(console=console, screen=False, auto_refresh=False) as live:
            prog_index = 0
            while prog_index < len(progression) and not exit_flag and not skip_progression:
                chord_name = progression[prog_index]
                target_notes = chord_set[chord_name]
                chord_attempts = 0
                
                # Affichage initial
                time_info = ""
                if use_timer and is_progression_started:
                    remaining_time = timer_duration - (time.time() - start_time)
                    time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"
                
                live.update(create_live_display(chord_name, prog_index, len(progression), time_info), refresh=True)
                
                notes_currently_on = set()
                attempt_notes = set()

                # Boucle pour chaque accord
                while not exit_flag and not skip_progression:
                    if use_timer and is_progression_started:
                        remaining_time = timer_duration - (time.time() - start_time)
                        time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"
                        live.update(create_live_display(chord_name, prog_index, len(progression), time_info), refresh=True)
                        
                        if remaining_time <= 0:
                            live.update("[bold red]Temps écoulé ! Session terminée.[/bold red]", refresh=True)
                            time.sleep(2)
                            exit_flag = True
                            break
                        
                    char = wait_for_input(timeout=0.01)
                    if char:
                        char = char.lower()
                        if char == 'q':
                            exit_flag = True
                            break
                        if char == 'r':
                            # Vider le buffer des entrées clavier pour éviter l'accumulation
                            while wait_for_input(timeout=0.001):
                                pass
                            
                            # Afficher le message de lecture et rediriger temporairement TOUS les affichages
                            live.update("[bold cyan]Lecture de la progression...[/bold cyan]", refresh=True)
                            
                            # Sauvegarder les fonctions d'affichage originales
                            original_print = print
                            original_console_print = console.print
                            
                            # Rediriger TOUS les affichages vers des fonctions vides
                            import builtins
                            builtins.print = lambda *args, **kwargs: None
                            console.print = lambda *args, **kwargs: None
                            
                            try:
                                play_progression_sequence(outport, progression, chord_set)
                            finally:
                                # Restaurer les fonctions d'affichage originales
                                builtins.print = original_print
                                console.print = original_console_print
                            
                            # Vider à nouveau le buffer après la lecture
                            while wait_for_input(timeout=0.001):
                                pass
                            
                            # Remettre l'affichage normal après la lecture
                            prog_index = 0
                            chord_name = progression[prog_index]
                            target_notes = chord_set[chord_name]
                            live.update(create_live_display(chord_name, prog_index, len(progression)), refresh=True)
                            break
                        if char == 'n':
                            skip_progression = True
                            break

                    for msg in inport.iter_pending():
                        if msg.type == 'note_on' and msg.velocity > 0:
                            notes_currently_on.add(msg.note)
                            attempt_notes.add(msg.note)
                        elif msg.type == 'note_off':
                            notes_currently_on.discard(msg.note)

                    if not notes_currently_on and attempt_notes:
                        chord_attempts += 1
                        progression_total_attempts += 1
                        
                        if use_timer and not is_progression_started:
                            is_progression_started = True
                            start_time = time.time()

                        try:
                            recognized_name, recognized_inversion = recognize_chord(attempt_notes)
                            
                            is_correct = (recognized_name and 
                                        is_enharmonic_match_improved(recognized_name, chord_name, chord_set) and 
                                        len(attempt_notes) == len(chord_set[chord_name]))
                            
                            if is_correct:
                                # Afficher le succès avec les notes jouées
                                colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                                success_msg = f"[bold green]Correct ! {chord_name}[/bold green]\nNotes jouées : [{colored_notes}]"
                                live.update(success_msg, refresh=True)
                                time.sleep(2)
                                
                                if chord_attempts == 1:
                                    progression_correct_count += 1
                                
                                prog_index += 1
                                break
                            else:
                                # Afficher l'erreur avec les notes jouées
                                colored_string = get_colored_notes_string(attempt_notes, target_notes)
                                error_msg = f"[bold red]Incorrect.[/bold red] Vous avez joué : {recognized_name if recognized_name else 'Accord non reconnu'}\nNotes jouées : [{colored_string}]"
                                live.update(error_msg, refresh=True)
                                time.sleep(2)
                                
                                # Remettre l'affichage normal
                                live.update(create_live_display(chord_name, prog_index, len(progression)), refresh=True)
                                attempt_notes.clear()

                        except Exception as e:
                            print(f"ERREUR dans progression_mode: {e}")
                            attempt_notes.clear()
                    
                    time.sleep(0.01)
                
                if exit_flag:
                    break
            
        if not exit_flag and not skip_progression:
            session_correct_count += progression_correct_count
            session_total_attempts += progression_total_attempts
            session_total_count += len(progression)
            
            console.print(f"\n--- Statistiques de cette progression ---")
            console.print(f"Accords à jouer : [bold cyan]{len(progression)}[/bold cyan]")
            console.print(f"Tentatives totales : [bold yellow]{progression_total_attempts}[/bold yellow]")
            console.print(f"Réussis du premier coup : [bold green]{progression_correct_count}[/bold green]")
            
            if progression_total_attempts > 0:
                accuracy = (progression_correct_count / progression_total_attempts) * 100
                console.print(f"Précision : [bold cyan]{accuracy:.1f}%[/bold cyan]")
            
            if use_timer and is_progression_started:
                end_time = time.time()
                elapsed_time = end_time - start_time
                console.print(f"\nTemps pour la progression : [bold cyan]{elapsed_time:.2f} secondes[/bold cyan]")
            
            choice = Prompt.ask("\nProgression terminée ! Appuyez sur Entrée pour la suivante ou 'q' pour revenir au menu principal...", console=console, choices=["", "q"], show_choices=False)
            if choice == 'q':
                exit_flag = True
                break
            clear_screen()

        elif skip_progression:
            console.print("\n[bold yellow]Passage à la progression suivante.[/bold yellow]")
            time.sleep(1)

    if use_timer:
        display_stats_fixed(session_correct_count, session_total_attempts, session_total_count, elapsed_time)
    else:
        display_stats_fixed(session_correct_count, session_total_attempts, session_total_count)
        
    console.print("\nAppuyez sur Entrée pour retourner au menu principal.")
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)

def all_degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    """Mode d'entraînement pour jouer tous les degrés d'une gamme dans l'ordre."""
    
    session_correct_count = 0
    session_total_count = 0
    session_total_attempts = 0
    last_tonalite = None
    
    exit_flag = False
    
    while not exit_flag:
        for _ in inport.iter_pending():
            pass

        clear_screen()
        console.print(Panel(
            Text("Mode Tous les Degrés", style="bold purple", justify="center"),
            title="Gamme Complète",
            border_style="purple"
        ))
        console.print("Jouez tous les accords de la gamme dans l'ordre.")
        console.print("Appuyez sur 'q' pour quitter, 'r' pour entendre la gamme complète.")
        
        # Choisir une nouvelle tonalité
        tonalite, gammes = random.choice(list(gammes_majeures.items()))
        while tonalite == last_tonalite:
            tonalite, gammes = random.choice(list(gammes_majeures.items()))
        last_tonalite = tonalite
        
        gammes_filtrees = [g for g in gammes if g in chord_set]
        if len(gammes_filtrees) < 3:
            continue
            
        progression_accords = gammes_filtrees
        display_degrees_table(tonalite, gammes_filtrees)

        console.print(f"\nDans la tonalité de [bold yellow]{tonalite}[/bold yellow], jouez la gamme complète : [bold yellow]{' -> '.join(progression_accords)}[/bold yellow]")
        
        if play_progression_before_start:
            play_progression_sequence(outport, progression_accords, chord_set)

        progression_correct_count = 0
        progression_total_attempts = 0
        skip_progression = False

        # Fonction pour créer l'affichage live
        def create_degrees_display(chord_name, prog_index, total_chords, tonalite):
            return Panel(
                f"Accord à jouer ({prog_index + 1}/{total_chords}): [bold yellow]{chord_name}[/bold yellow]", 
                title="Gamme Complète", 
                border_style="purple"
            )

        # Boucle principale avec Live display
        with Live(console=console, screen=False, auto_refresh=False) as live:
            prog_index = 0
            while prog_index < len(progression_accords) and not exit_flag and not skip_progression:
                chord_name = progression_accords[prog_index]
                target_notes = chord_set[chord_name]
                chord_attempts = 0
                
                # Affichage initial
                live.update(create_degrees_display(chord_name, prog_index, len(progression_accords), tonalite), refresh=True)
                
                notes_currently_on = set()
                attempt_notes = set()
                
                # Boucle pour chaque accord
                while not exit_flag:
                    char = wait_for_input(timeout=0.01)
                    if char:
                        char = char.lower()
                        if char == 'q':
                            exit_flag = True
                            break
                        if char == 'r':
                            # Vider le buffer des entrées clavier pour éviter l'accumulation
                            while wait_for_input(timeout=0.001):
                                pass
                            
                            # Afficher le message de lecture et rediriger temporairement TOUS les affichages
                            live.update("[bold cyan]Lecture de la gamme...[/bold cyan]", refresh=True)
                            
                            # Sauvegarder les fonctions d'affichage originales
                            original_print = print
                            original_console_print = console.print
                            
                            # Rediriger TOUS les affichages vers des fonctions vides
                            import builtins
                            builtins.print = lambda *args, **kwargs: None
                            console.print = lambda *args, **kwargs: None
                            
                            try:
                                play_progression_sequence(outport, progression_accords, chord_set)
                            finally:
                                # Restaurer les fonctions d'affichage originales
                                builtins.print = original_print
                                console.print = original_console_print
                            
                            # Vider à nouveau le buffer après la lecture
                            while wait_for_input(timeout=0.001):
                                pass
                            
                            # Remettre l'affichage normal après la lecture
                            prog_index = 0
                            chord_name = progression_accords[prog_index]
                            target_notes = chord_set[chord_name]
                            live.update(create_degrees_display(chord_name, prog_index, len(progression_accords), tonalite), refresh=True)
                            break

                    for msg in inport.iter_pending():
                        if msg.type == 'note_on' and msg.velocity > 0:
                            notes_currently_on.add(msg.note)
                            attempt_notes.add(msg.note)
                        elif msg.type == 'note_off':
                            notes_currently_on.discard(msg.note)

                    if not notes_currently_on and attempt_notes:
                        chord_attempts += 1
                        progression_total_attempts += 1

                        try:
                            recognized_name, recognized_inversion = recognize_chord(attempt_notes)
                            
                            is_correct = (recognized_name and 
                                        is_enharmonic_match_improved(recognized_name, chord_name, chord_set) and 
                                        len(attempt_notes) == len(chord_set[chord_name]))
                            
                            if is_correct:
                                # Afficher le succès avec les notes jouées
                                colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                                success_msg = f"[bold green]Correct ! {chord_name}[/bold green]\nNotes jouées : [{colored_notes}]"
                                live.update(success_msg, refresh=True)
                                time.sleep(2)
                                
                                if chord_attempts == 1:
                                    progression_correct_count += 1
                                
                                prog_index += 1
                                break
                            else:
                                # Afficher l'erreur avec les notes jouées
                                colored_string = get_colored_notes_string(attempt_notes, target_notes)
                                error_msg = f"[bold red]Incorrect.[/bold red] Vous avez joué : {recognized_name if recognized_name else 'Accord non reconnu'}\nNotes jouées : [{colored_string}]"
                                live.update(error_msg, refresh=True)
                                time.sleep(2)
                                
                                # Remettre l'affichage normal
                                live.update(create_degrees_display(chord_name, prog_index, len(progression_accords), tonalite), refresh=True)
                                attempt_notes.clear()

                        except Exception as e:
                            print(f"ERREUR dans all_degrees_mode: {e}")
                            attempt_notes.clear()
                    
                    time.sleep(0.01)
                
                if exit_flag:
                    break
            
        if not exit_flag and not skip_progression:
            session_correct_count += progression_correct_count
            session_total_attempts += progression_total_attempts
            session_total_count += len(progression_accords)
            
            console.print(f"\n--- Statistiques de cette progression ---")
            console.print(f"Accords à jouer : [bold cyan]{len(progression_accords)}[/bold cyan]")
            console.print(f"Tentatives totales : [bold yellow]{progression_total_attempts}[/bold yellow]")
            console.print(f"Réussis du premier coup : [bold green]{progression_correct_count}[/bold green]")
            
            if progression_total_attempts > 0:
                accuracy = (progression_correct_count / progression_total_attempts) * 100
                console.print(f"Précision : [bold cyan]{accuracy:.1f}%[/bold cyan]")
            
            choice = Prompt.ask("\nProgression terminée ! Appuyez sur Entrée pour la suivante ou 'q' pour revenir au menu principal...", console=console, choices=["", "q"], show_choices=False)
            if choice == 'q':
                exit_flag = True
                break
            clear_screen()

    display_stats_fixed(session_correct_count, session_total_attempts, session_total_count)
    console.print("\nAppuyez sur Entrée pour retourner au menu principal.")
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)

def cadence_mode(inport, outport, play_progression_before_start, chord_set):
    """Mode d'entraînement sur les cadences musicales."""

    session_correct_count = 0
    session_total_chords = 0
    exit_flag = False

    while not exit_flag:
        clear_screen()
        console.print(Panel(
            Text("Mode Cadences Musicales", style="bold magenta", justify="center"),
            title="Cadences",
            border_style="magenta"
        ))
        console.print("Jouez la cadence demandée dans la bonne tonalité.")
        console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer.")

        # Boucle pour s'assurer que la cadence peut être jouée avec le jeu d'accords actuel
        while True:
            # 1. Choisir une tonalité au hasard
            tonalite, accords_de_la_gamme = random.choice(list(gammes_majeures.items()))

            # 2. Choisir une cadence au hasard
            nom_cadence, degres_cadence = random.choice(list(cadences.items()))

            # 3. Traduire les degrés en noms d'accords
            try:
                progression_accords = [accords_de_la_gamme[DEGREE_MAP[d]] for d in degres_cadence]
            except (KeyError, IndexError):
                continue # Si un degré n'est pas dans notre map, recommencer

            # 4. Vérifier si tous les accords de la cadence sont dans le `chord_set` autorisé
            if all(accord in chord_set for accord in progression_accords):
                break # La cadence est valide, on peut continuer

        # Afficher la table des degrés de la tonalité actuelle
        gammes_filtrees = [g for g in accords_de_la_gamme if g in chord_set]
        display_degrees_table(tonalite, gammes_filtrees)

        degres_str = ' -> '.join(degres_cadence)
        progression_str = ' -> '.join(progression_accords)
        console.print(f"\nDans la tonalité de [bold yellow]{tonalite}[/bold yellow], jouez la [bold cyan]{nom_cadence}[/bold cyan] ([bold cyan]{degres_str}[/bold cyan]):")
        console.print(f"[bold yellow]{progression_str}[/bold yellow]")

        if play_progression_before_start:
            play_progression_sequence(outport, progression_accords, chord_set)

        progression_correct_count = 0
        skip_progression = False

        # Boucle principale pour la progression
        prog_index = 0
        while prog_index < len(progression_accords) and not exit_flag and not skip_progression:
            chord_name = progression_accords[prog_index]
            target_notes = chord_set[chord_name]
            console.print(f"Jouez l'accord ({prog_index + 1}/{len(progression_accords)}): [bold yellow]{chord_name}[/bold yellow]")

            notes_currently_on = set()
            attempt_notes = set()

            # Boucle pour chaque accord
            while not exit_flag and not skip_progression:
                char = wait_for_input(timeout=0.01)
                if char:
                    char = char.lower()
                    if char == 'q':
                        exit_flag = True
                        break
                    if char == 'r':
                        play_progression_sequence(outport, progression_accords, chord_set)
                        prog_index = 0 # Recommencer la cadence actuelle
                        console.print(f"Reprenons. Jouez l'accord [bold yellow]{progression_accords[prog_index]}[/bold yellow]")
                        break
                    if char == 'n':
                        skip_progression = True
                        break

                for msg in inport.iter_pending():
                    if msg.type == 'note_on' and msg.velocity > 0:
                        notes_currently_on.add(msg.note)
                        attempt_notes.add(msg.note)
                    elif msg.type == 'note_off':
                        notes_currently_on.discard(msg.note)

                if not notes_currently_on and attempt_notes:
                    # Vérification de l'accord - VERSION CORRIGÉE
                    try:
                        recognized_name, recognized_inversion = recognize_chord(attempt_notes)
                        
                        # Utiliser la fonction améliorée pour la comparaison enharmonique
                        is_correct = (recognized_name and 
                                    is_enharmonic_match_improved(recognized_name, chord_name, chord_set) and 
                                    len(attempt_notes) == len(chord_set[chord_name]))
                        
                        if is_correct:
                            colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                            console.print(f"Notes jouées : [{colored_notes}]")
                            console.print("[bold green]Correct ![/bold green]")
                            progression_correct_count += 1
                            prog_index += 1
                            break
                        else:
                            # Section d'affichage d'erreur - VERSION SÉCURISÉE
                            colored_string = get_colored_notes_string(attempt_notes, target_notes)
                            
                            if recognized_name:
                                # Nettoyer les noms pour éviter les conflits de formatage
                                clean_chord_name = str(recognized_name).replace('%', 'pct')
                                clean_inversion = str(recognized_inversion) if recognized_inversion else "position inconnue"
                                clean_inversion = clean_inversion.replace('%', 'pct')
                                
                                # Utiliser des chaînes séparées pour éviter les conflits de formatage
                                error_msg = "[bold red]Incorrect.[/bold red] Vous avez joué : "
                                chord_info = f"{clean_chord_name} ({clean_inversion})"
                                console.print(error_msg + chord_info)
                            else:
                                console.print("[bold red]Incorrect. Réessayez.[/bold red]")
                            # Décrémenter le nombre de bonnes réponses si incorrect
                            if progression_correct_count > 0:
                                progression_correct_count -= 1

                            console.print(f"Notes jouées : [{colored_string}]")
                            attempt_notes.clear()
                            
                    except Exception as e:
                        # Debug en cas d'erreur persistante
                        print(f"ERREUR dans progression_mode: {e}")
                        print(f"attempt_notes: {list(attempt_notes)}")
                        print(f"chord_name cible: {chord_name}")
                        if 'recognized_name' in locals():
                            print(f"recognized_name: {recognized_name}")
                        if 'recognized_inversion' in locals():
                            print(f"recognized_inversion: {recognized_inversion}")
                        # Continuer le jeu malgré l'erreur
                        attempt_notes.clear()

                time.sleep(0.01)

            if exit_flag:
                break
        
        if not exit_flag and not skip_progression:
            session_correct_count += progression_correct_count
            session_total_chords += len(progression_accords)

            choice = Prompt.ask("\nProgression terminée ! Appuyez sur Entrée pour la suivante ou 'q' pour revenir au menu principal...", console=console, choices=["", "q"], show_choices=False)
            if choice == 'q':
                exit_flag = True
                break
            clear_screen()            

        elif skip_progression:
            console.print("\n[bold yellow]Passage à la cadence suivante.[/bold yellow]")
            time.sleep(1)

    display_stats(session_correct_count, session_total_chords)
    console.print("\nAppuyez sur Entrée pour retourner au menu principal.")
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)

def degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    """Mode d'entraînement sur les degrés d'une tonalité."""
    
    session_correct_count = 0
    session_total_count = 0
    session_total_attempts = 0
    
    exit_flag = False
    
    while not exit_flag:
        for _ in inport.iter_pending():
            pass

        clear_screen()
        console.print(Panel(
            Text("Mode Degrés", style="bold green", justify="center"),
            title="Entraînement par Degrés",
            border_style="green"
        ))
        console.print("Jouez l'accord correspondant au degré affiché.")
        console.print("Appuyez sur 'q' pour quitter.")
        
        # Choisir une tonalité aléatoire
        tonalite, gammes = random.choice(list(gammes_majeures.items()))
        gammes_filtrees = [g for g in gammes if g in chord_set]
        
        if len(gammes_filtrees) < 3:
            continue
            
        display_degrees_table(tonalite, gammes_filtrees)
        
        # Choisir un accord aléatoire dans la gamme
        chord_name = random.choice(gammes_filtrees)
        target_notes = chord_set[chord_name]
        degree_number = gammes_filtrees.index(chord_name) + 1
        
        chord_attempts = 0

        # Fonction pour créer l'affichage live
        def create_degree_display(degree_num, tonalite, chord_name):
            return Panel(
                f"Jouez le degré [bold cyan]{degree_num}[/bold cyan]: [bold yellow]{chord_name}[/bold yellow]", 
                title="Degré à jouer", 
                border_style="green"
            )

        # Boucle avec Live display
        with Live(console=console, screen=False, auto_refresh=False) as live:
            live.update(create_degree_display(degree_number, tonalite, chord_name), refresh=True)
            
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

                if not notes_currently_on and attempt_notes:
                    chord_attempts += 1
                    session_total_attempts += 1

                    try:
                        recognized_name, recognized_inversion = recognize_chord(attempt_notes)
                        
                        is_correct = (recognized_name and 
                                    is_enharmonic_match_improved(recognized_name, chord_name, chord_set) and 
                                    len(attempt_notes) == len(chord_set[chord_name]))
                        
                        if is_correct:
                            # Afficher le succès avec les notes jouées
                            colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                            success_msg = f"[bold green]Correct ! Degré {degree_number}: {chord_name}[/bold green]\nNotes jouées : [{colored_notes}]"
                            live.update(success_msg, refresh=True)
                            time.sleep(2)
                            
                            if chord_attempts == 1:
                                session_correct_count += 1
                            
                            session_total_count += 1
                           
                            break
                        else:
                            # Afficher l'erreur avec les notes jouées
                            colored_string = get_colored_notes_string(attempt_notes, target_notes)
                            error_msg = f"[bold red]Incorrect.[/bold red] Vous avez joué : {recognized_name if recognized_name else 'Accord non reconnu'}\nNotes jouées : [{colored_string}]"
                            live.update(error_msg, refresh=True)
                            time.sleep(2)
                            
                            # Remettre l'affichage normal
                            live.update(create_degree_display(degree_number, tonalite, chord_name), refresh=True)
                            attempt_notes.clear()

                    except Exception as e:
                        print(f"ERREUR dans degrees_mode: {e}")
                        attempt_notes.clear()
                
                time.sleep(0.01)

    display_stats_fixed(session_correct_count, session_total_attempts, session_total_count)
    console.print("\nAppuyez sur Entrée pour retourner au menu principal.")
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)

def tonal_progression_mode(inport, outport, chord_set):
    """Mode qui joue une progression d'accords puis demande à l'utilisateur de la rejouer."""
    current_tonalite = None
    current_progression_name = None
    current_progression_accords = None
    
    while True:
        clear_screen()
        console.print(Panel(
            Text("Mode Progression Tonale", style="bold bright_magenta", justify="center"),
            title="Progression Tonale",
            border_style="bright_magenta"
        ))
        
        if current_tonalite is None:
            current_tonalite, gammes = random.choice(list(gammes_majeures.items()))
            gammes_filtrees = [g for g in gammes if g in chord_set]
            
            current_progression_name, degres_progression = random.choice(list(tonal_progressions.items()))
            
            current_progression_accords = []
            for degre in degres_progression:
                index = DEGREE_MAP.get(degre)
                if index is not None and index < len(gammes_filtrees):
                    current_progression_accords.append(gammes_filtrees[index])
        
        console.print(f"Tonalité : [bold yellow]{current_tonalite}[/bold yellow]")
        console.print(f"Progression : [bold cyan]{current_progression_name}[/bold cyan]")
        console.print(f"Accords : [bold yellow]{' → '.join(current_progression_accords)}[/bold yellow]")
        
        console.print("\n[bold green]Écoutez la progression...[/bold green]")
        for chord_name in current_progression_accords:
            console.print(f"Joue : [bold bright_yellow]{chord_name}[/bold bright_yellow]")
            play_chord(outport, chord_set[chord_name], duration=1.0)
            time.sleep(0.3)
        
        console.print("\n[bold green]À vous de jouer! Répétez la progression accord par accord.[/bold green]")
        console.print("Appuyez sur 'r' pour réécouter la progression ou 'q' pour quitter en cours.")
        
        correct_count = 0
        skip_progression = False
        
        for chord_index, chord_name in enumerate(current_progression_accords):
            if skip_progression:
                break

            target_notes = chord_set[chord_name]
            
            with Live(console=console, screen=False, auto_refresh=True) as live:
                live.update(f"\nJouez l'accord ({chord_index+1}/{len(current_progression_accords)}): [bold yellow]{chord_name}[/bold yellow]")
                
                notes_currently_on = set()
                attempt_notes = set()
                
                while True:
                    char = wait_for_input(timeout=0.01)
                    if char:
                        char = char.lower()
                        if char == 'q':
                            skip_progression = True
                            break
                        if char == 'r':
                            live.console.print("[bold blue]Réécoute de la progression...[/bold blue]")
                            for name in current_progression_accords:
                                play_chord(outport, chord_set[name], duration=1.0)
                                time.sleep(0.3)
                            live.update(f"\nJouez l'accord ({chord_index+1}/{len(current_progression_accords)}): [bold yellow]{chord_name}[/bold yellow]")
                            continue
                    
                    for msg in inport.iter_pending():
                        if msg.type == 'note_on' and msg.velocity > 0:
                            notes_currently_on.add(msg.note)
                            attempt_notes.add(msg.note)
                        elif msg.type == 'note_off':
                            notes_currently_on.discard(msg.note)
                    
                    if not notes_currently_on and attempt_notes:
                        recognized_name, inversion_label = recognize_chord(attempt_notes)
                        
                        if recognized_name and is_enharmonic_match_improved(recognized_name, chord_name, None) and len(attempt_notes) == len(target_notes):
                            colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                            live.console.print(f"Notes jouées : [{colored_notes}]")
                            live.console.print("[bold green]Correct ![/bold green]")
                            correct_count += 1
                            time.sleep(1)
                            break
                        else:
                            colored_string = get_colored_notes_string(attempt_notes, target_notes)
                            
                            if recognized_name:
                                live.console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {recognized_name} ({inversion_label})")
                            else:
                                live.console.print("[bold red]Incorrect. Réessayez.[/bold red]")
                            
                            live.console.print(f"Notes jouées : [{colored_string}]")
                            attempt_notes.clear()
                    
                    time.sleep(0.01)
                
                if skip_progression:
                    break
        
        if not skip_progression:
            total_chords = len(current_progression_accords)
            accuracy = (correct_count / total_chords) * 100 if total_chords > 0 else 0
            
            console.print("\n--- Résultats de la progression ---")
            console.print(f"Accords corrects : [bold green]{correct_count}/{total_chords}[/bold green]")
            console.print(f"Précision : [bold cyan]{accuracy:.2f}%[/bold cyan]")
            console.print("----------------------------------")

        choice = Prompt.ask(
            "\nProgression terminée ! Appuyez sur Entrée pour choisir une autre progression ou 'q' pour revenir au menu principal...", 
            console=console, 
            choices=["", "q"], 
            show_choices=False
        )

        if choice == '':
            pass
        elif choice == 'q':
            current_tonalite = None
            current_progression_name = None
            current_progression_accords = None
            break

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
                menu_options.append("[1] Mode Explorateur d'accords (Dictionnaire)\n", style="bold bright_blue")
                menu_options.append("--- Entraînement ---\n", style="dim")
                menu_options.append("[2] Mode Accord Simple\n", style="bold yellow")
                menu_options.append("[3] Mode Écoute et Devine\n", style="bold orange3")
                menu_options.append("[4] Mode Progressions d'accords (aléatoires)\n", style="bold blue")
                menu_options.append("[5] Mode Degrés (aléatoire)\n", style="bold red")
                menu_options.append("[6] Mode Tous les Degrés (gamme)\n", style="bold purple")
                menu_options.append("[7] Mode Cadences (théorie)\n", style="bold magenta")
                menu_options.append("[8] Mode Pop/Rock (célèbres)\n", style="bold cyan")
                menu_options.append("[9] Mode Reconnaissance Libre\n", style="bold bright_cyan")
                menu_options.append("[10] Mode Progression Tonale\n", style="bold bright_magenta")  # NOUVEAU MODE
                menu_options.append("--- Configuration ---\n", style="dim")
                menu_options.append("[11] Options\n", style="bold white")
                menu_options.append("[12] Quitter", style="bold white")                
                menu_panel = Panel(
                    menu_options,
                    title="Menu Principal",
                    border_style="bold blue"
                )
                console.print(menu_panel)
                
                # MODIFIÉ: Mise à jour des choix possibles
                mode_choice = Prompt.ask("Votre choix", choices=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'], show_choices=False, console=console)
                
                if mode_choice == '1':
                    chord_explorer_mode(outport)
                elif mode_choice == '2':
                    single_chord_mode(inport, outport, current_chord_set)
                elif mode_choice == '3':
                    listen_and_reveal_mode(inport, outport, current_chord_set)
                elif mode_choice == '4':
                    progression_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '5':
                    degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '6':
                    all_degrees_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '7':
                    cadence_mode(inport, outport, play_progression_before_start, current_chord_set)
                elif mode_choice == '8':
                    pop_rock_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, current_chord_set)
                elif mode_choice == '9':
                    reverse_chord_mode(inport)
                elif mode_choice == '10':
                    tonal_progression_mode(inport, outport, current_chord_set)                    
                elif mode_choice == '11':
                    use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice = options_menu(use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice)
                elif mode_choice == '12':
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