# coding=utf-8
import mido
import time
import random
import os
import sys
from typing import Set, Tuple, Optional, List, Dict, Any
from dataclasses import dataclass

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

# --- Structures de données ---

@dataclass
class GameSession:
    """Classe pour tracker les statistiques d'une session de jeu."""
    correct_count: int = 0
    total_attempts: int = 0
    total_chords: int = 0
    start_time: Optional[float] = None
    
    def reset(self):
        self.correct_count = 0
        self.total_attempts = 0
        self.total_chords = 0
        self.start_time = None
    
    def get_accuracy(self) -> float:
        return (self.correct_count / self.total_attempts * 100) if self.total_attempts > 0 else 0.0
    
    def get_elapsed_time(self) -> float:
        return time.time() - self.start_time if self.start_time else 0.0

@dataclass
class ChordAttempt:
    """Classe pour représenter une tentative de jeu d'accord."""
    played_notes: Set[int]
    target_chord_name: str
    target_notes: Set[int]
    recognized_name: Optional[str] = None
    recognized_inversion: Optional[str] = None
    is_correct: bool = False

# --- Définition des accords, des cadences et des gammes ---
# (Garder toutes les définitions existantes...)

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
    "c7": "Do 7ème", "c#7": "Do dièse 7ème", "db7": "Do dièse 7ème",
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
    "c6": "Do 6ème", "d6": "Ré 6ème", "e6": "Mi 6ème", "f6": "Fa 6ème",
    "g6": "Sol 6ème", "a6": "La 6ème", "b6": "Si 6ème",
}

# --- Carte des équivalences enharmoniques COMPLÈTE ---
enharmonic_map = {
    # Majeurs
    "Ré dièse Majeur": ["Mi bémol Majeur"],
    "Mi bémol Majeur": ["Ré dièse Majeur"],
    "Fa dièse Majeur": ["Sol bémol Majeur"],
    "Sol bémol Majeur": ["Fa dièse Majeur"],
    "Do dièse Majeur": ["Ré bémol Majeur"],
    "Ré bémol Majeur": ["Do dièse Majeur"],
    "Fa bémol Majeur": ["Mi Majeur"],
    "Mi Majeur": ["Fa bémol Majeur"],
    "Sol dièse Majeur": ["La bémol Majeur"],
    "La bémol Majeur": ["Sol dièse Majeur"],
    
    # Mineurs
    "Ré dièse Mineur": ["Mi bémol Mineur"],
    "Mi bémol Mineur": ["Ré dièse Mineur"],
    "Fa dièse Mineur": ["Sol bémol Mineur"],
    "Sol bémol Mineur": ["Fa dièse Mineur"],
    "Do dièse Mineur": ["Ré bémol Mineur"],
    "Ré bémol Mineur": ["Do dièse Mineur"],
    "Mi dièse Mineur": ["Fa Mineur"],
    "Fa Mineur": ["Mi dièse Mineur"],
    "Sol dièse Mineur": ["La bémol Mineur"],
    "La bémol Mineur": ["Sol dièse Mineur"],
    "La dièse Mineur": ["Si bémol Mineur"],
    "Si bémol Mineur": ["La dièse Mineur"],
    
    # Diminués
    "Si dièse Diminué": ["Do Diminué"],
    "Do Diminué": ["Si dièse Diminué"],
    
    # 7èmes (ajout pour plus de complétude)
    "Do dièse 7ème": ["Ré bémol 7ème"],
    "Ré bémol 7ème": ["Do dièse 7ème"],
    "Ré dièse 7ème": ["Mi bémol 7ème"],
    "Mi bémol 7ème": ["Ré dièse 7ème"],
    "Fa dièse 7ème": ["Sol bémol 7ème"],
    "Sol bémol 7ème": ["Fa dièse 7ème"],
    "Sol dièse 7ème": ["La bémol 7ème"],
    "La bémol 7ème": ["Sol dièse 7ème"],
    "La dièse 7ème": ["Si bémol 7ème"],
    "Si bémol 7ème": ["La dièse 7ème"],
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
    "Progression I-V-vi-IV": ["I", "V", "vi", "IV"]
}

# --- Fonctions utilitaires communes ---

class MidiInputHandler:
    """Gestionnaire d'entrées MIDI centralisé."""
    
    def __init__(self, inport):
        self.inport = inport
        self.notes_currently_on = set()
        self.attempt_notes = set()
        self.last_note_off_time = None
        self.note_detection_delay = 0.3  # Délai en secondes pour la détection d'accords
    
    def update(self):
        """Met à jour l'état des notes jouées."""
        for msg in self.inport.iter_pending():
            if msg.type == 'note_on' and msg.velocity > 0:
                self.notes_currently_on.add(msg.note)
                self.attempt_notes.add(msg.note)
                self.last_note_off_time = None
            elif msg.type == 'note_off':
                self.notes_currently_on.discard(msg.note)
                if not self.notes_currently_on and not self.last_note_off_time:
                    self.last_note_off_time = time.time()
    
    def has_chord_ready(self) -> bool:
        """Vérifie si un accord complet a été joué et relâché."""
        return (self.last_note_off_time and 
                time.time() - self.last_note_off_time > self.note_detection_delay and
                len(self.attempt_notes) >= 2)
    
    def get_played_notes(self) -> Set[int]:
        """Retourne les notes jouées et remet à zéro."""
        notes = self.attempt_notes.copy()
        self.attempt_notes.clear()
        self.last_note_off_time = None
        return notes
    
    def clear(self):
        """Remet à zéro l'état du gestionnaire."""
        self.notes_currently_on.clear()
        self.attempt_notes.clear()
        self.last_note_off_time = None

class ChordValidator:
    """Validateur d'accords centralisé."""
    
    @staticmethod
    def validate_chord_attempt(attempt: ChordAttempt) -> ChordAttempt:
        """Valide une tentative d'accord et la met à jour."""
        attempt.recognized_name, attempt.recognized_inversion = recognize_chord(attempt.played_notes)
        
        if attempt.recognized_name:
            attempt.is_correct = (
                is_enharmonic_match_improved(attempt.recognized_name, attempt.target_chord_name, all_chords) and
                len(attempt.played_notes) == len(attempt.target_notes)
            )
        else:
            attempt.is_correct = False
        
        return attempt

class GameModeBase:
    """Classe de base pour tous les modes de jeu."""
    
    def __init__(self, inport, outport, chord_set, name: str, style: str, border_style: str):
        self.inport = inport
        self.outport = outport
        self.chord_set = chord_set
        self.name = name
        self.style = style
        self.border_style = border_style
        self.session = GameSession()
        self.midi_handler = MidiInputHandler(inport)
        self.exit_flag = False
        
    def clear_midi_buffer(self):
        """Vide le tampon MIDI."""
        for _ in self.inport.iter_pending():
            pass
    
    def display_header(self, additional_info: str = ""):
        """Affiche l'en-tête du mode de jeu."""
        clear_screen()
        console.print(Panel(
            Text(self.name, style=self.style, justify="center"),
            title=self.name,
            border_style=self.border_style
        ))
        chord_type = 'Tous' if self.chord_set == all_chords else 'Majeurs/Mineurs'
        console.print(f"Type d'accords: [bold cyan]{chord_type}[/bold cyan]")
        if additional_info:
            console.print(additional_info)
    
    def handle_common_keys(self, char: str) -> bool:
        """Gère les touches communes à tous les modes. Retourne True si le mode doit se terminer."""
        if char and char.lower() == 'q':
            self.exit_flag = True
            return True
        return False
    
    def display_chord_feedback(self, attempt: ChordAttempt, show_target: bool = True):
        """Affiche le feedback pour une tentative d'accord."""
        colored_notes = get_colored_notes_string(attempt.played_notes, attempt.target_notes)
        console.print(f"Notes jouées : [{colored_notes}]")
        
        if attempt.is_correct:
            message = f"[bold green]Correct !"
            if show_target:
                message += f" {attempt.target_chord_name}"
            message += "[/bold green]"
            console.print(message)
            return True
        else:
            if attempt.recognized_name:
                clean_name = str(attempt.recognized_name).replace('%', 'pct').replace('{', '(').replace('}', ')')
                clean_inversion = str(attempt.recognized_inversion) if attempt.recognized_inversion else "position inconnue"
                clean_inversion = clean_inversion.replace('%', 'pct').replace('{', '(').replace('}', ')')
                console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {clean_name} ({clean_inversion})")
            else:
                console.print("[bold red]Incorrect. Réessayez.[/bold red]")
            return False
    
    def display_stats(self):
        """Affiche les statistiques de la session."""
        console.print("\n--- Bilan de la session ---")
        if self.session.total_attempts > 0:
            console.print(f"Tentatives totales : [bold yellow]{self.session.total_attempts}[/bold yellow]")
            console.print(f"Tentatives réussies : [bold green]{self.session.correct_count}[/bold green]")
            console.print(f"Tentatives échouées : [bold red]{self.session.total_attempts - self.session.correct_count}[/bold red]")
            console.print(f"Précision globale : [bold cyan]{self.session.get_accuracy():.2f}%[/bold cyan]")
            
            if self.session.total_chords > 0:
                avg_attempts_per_chord = self.session.total_attempts / self.session.total_chords
                console.print(f"Moyenne tentatives/accord : [bold magenta]{avg_attempts_per_chord:.1f}[/bold magenta]")
        else:
            console.print("Aucune tentative enregistrée.")
        
        if self.session.start_time:
            elapsed = self.session.get_elapsed_time()
            console.print(f"Temps écoulé : [bold cyan]{elapsed:.2f} secondes[/bold cyan]")
        console.print("-------------------------")

# --- Fonctions utilitaires réutilisables ---

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
    return "Inconnu"

def is_enharmonic_match_improved(played_chord_name, target_chord_name, all_chords_dict):
    """Version améliorée qui compare les classes de hauteur ET utilise la carte enharmonique."""
    if played_chord_name == target_chord_name:
        return True
    
    if not played_chord_name or not target_chord_name:
        return False
    if played_chord_name not in all_chords_dict or target_chord_name not in all_chords_dict:
        return False
    
    # 1. Vérifier avec la carte enharmonique
    enharmonic_equivalents = enharmonic_map.get(played_chord_name, [])
    if target_chord_name in enharmonic_equivalents:
        return True
    
    enharmonic_equivalents_reverse = enharmonic_map.get(target_chord_name, [])
    if played_chord_name in enharmonic_equivalents_reverse:
        return True
    
    # 2. Comparer les classes de hauteur
    played_pitch_classes = {note % 12 for note in all_chords_dict[played_chord_name]}
    target_pitch_classes = {note % 12 for note in all_chords_dict[target_chord_name]}
    
    return played_pitch_classes == target_pitch_classes

def get_colored_notes_string(played_notes, correct_notes):
    """Retourne une chaîne avec les notes colorées selon leur justesse."""
    output_parts = []
    correct_pitch_classes = {note % 12 for note in correct_notes}
    
    for note in sorted(played_notes):
        note_name = get_note_name(note)
        
        if note in correct_notes:
            output_parts.append(f"[bold green]{note_name}[/bold green]")
        elif (note % 12) in correct_pitch_classes:
            output_parts.append(f"[bold yellow]{note_name}[/bold yellow]")
        else:
            output_parts.append(f"[bold red]{note_name}[/bold red]")
            
    return ", ".join(output_parts)

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
        if chord_name in chord_set:
            play_chord(outport, chord_set[chord_name], duration=0.8)
            time.sleep(0.5)
        else:
            console.print(f"[bold red]L'accord {chord_name} n'a pas pu être joué.[/bold red]")

def wait_for_input(timeout=0.01):
    """Saisie de caractère non-bloquante."""
    if 'msvcrt' in sys.modules:
        if msvcrt.kbhit():
            return msvcrt.getch().decode('utf-8')
    else:
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
        for _ in inport.iter_pending():
            pass

def recognize_chord(played_notes_set):
    """Reconnaît un accord à partir d'un ensemble de notes MIDI jouées."""
    if len(played_notes_set) < 2:
        return None, None

    played_notes_sorted = sorted(list(played_notes_set))
    lowest_note_midi = played_notes_sorted[0]
    played_pitch_classes = frozenset(note % 12 for note in played_notes_set)
    lowest_note_pc = lowest_note_midi % 12
    
    best_match = None
    lowest_inversion_index = float('inf')

    for chord_name, ref_notes in all_chords.items():
        ref_pitch_classes = frozenset(note % 12 for note in ref_notes)

        if played_pitch_classes == ref_pitch_classes:
            root_note_pc = min(ref_notes) % 12
            sorted_ref_pcs = sorted(list(ref_pitch_classes))
            root_index_in_sorted = sorted_ref_pcs.index(root_note_pc)
            ordered_chord_pcs = sorted_ref_pcs[root_index_in_sorted:] + sorted_ref_pcs[:root_index_in_sorted]
            
            try:
                inversion_index = ordered_chord_pcs.index(lowest_note_pc)
            except ValueError:
                continue

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
        console.print(f"[bold red]Aucun port {port_type} MIDI trouvé.[/bold red]")
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

def display_degrees_table(tonalite, gammes_filtrees):
    """Affiche un tableau des accords de la gamme pour une tonalité donnée."""
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

# --- Modes de jeu refactorisés ---

class SingleChordMode(GameModeBase):
    """Mode Accord Simple refactorisé."""
    
    def __init__(self, inport, outport, chord_set):
        super().__init__(inport, outport, chord_set, "Mode Accords Simples", "bold yellow", "yellow")
        self.last_chord_name = None
    
    def run(self):
        """Lance le mode accord simple."""
        self.display_header("Jouez l'accord affiché. Appuyez sur 'q' pour quitter.")
        
        while not self.exit_flag:
            self.clear_midi_buffer()
            chord_name, chord_notes = self.get_next_chord()
            self.display_current_chord(chord_name)
            
            # Continuer à jouer le même accord jusqu'à ce qu'il soit réussi
            if self.play_chord_until_success(chord_name, chord_notes):
                self.session.correct_count += 1
                self.session.total_chords += 1
                console.print("[bold green]Bravo ! Accord suivant...[/bold green]")
                
                if not self.exit_flag:
                    time.sleep(2)
        
        self.display_stats()
        console.print("\nAppuyez sur une touche pour retourner au menu principal.")
        wait_for_any_key(self.inport)
    
    def get_next_chord(self):
        """Sélectionne le prochain accord différent du précédent."""
        chord_name, chord_notes = random.choice(list(self.chord_set.items()))
        while chord_name == self.last_chord_name:
            chord_name, chord_notes = random.choice(list(self.chord_set.items()))
        self.last_chord_name = chord_name
        return chord_name, chord_notes
    
    def display_current_chord(self, chord_name):
        """Affiche l'accord actuel à jouer."""
        self.display_header("Jouez l'accord affiché. Appuyez sur 'q' pour quitter.")
        console.print(f"\nJouez : [bold bright_yellow]{chord_name}[/bold bright_yellow]")
    
    def play_chord_until_success(self, chord_name, chord_notes):
        """Continue à jouer jusqu'à ce que l'accord soit réussi ou que l'utilisateur quitte."""
        while not self.exit_flag:
            result = self.play_chord_round(chord_name, chord_notes)
            if result is True:  # Accord réussi
                return True
            elif result is None:  # Utilisateur a quitté
                break
            # Si result is False, on continue la boucle pour réessayer le même accord
        
        return False
    
    def play_chord_round(self, chord_name, chord_notes):
        """Joue un round d'accord et retourne True si correct, False si incorrect, None si quit."""
        self.midi_handler.clear()
        
        while not self.exit_flag:
            char = wait_for_input(timeout=0.01)
            if self.handle_common_keys(char):
                return None  # Utilisateur veut quitter
            
            self.midi_handler.update()
            
            if self.midi_handler.has_chord_ready():
                played_notes = self.midi_handler.get_played_notes()
                attempt = ChordAttempt(played_notes, chord_name, chord_notes)
                
                try:
                    attempt = ChordValidator.validate_chord_attempt(attempt)
                    self.session.total_attempts += 1
                    
                    if attempt.is_correct:
                        self.display_chord_feedback(attempt, show_target=True)
                        return True
                    else:
                        self.display_chord_feedback(attempt, show_target=False)
                        console.print("[bold yellow]Réessayez le même accord...[/bold yellow]")
                        return False
                        
                except Exception as e:
                    console.print(f"[bold red]Erreur lors de l'évaluation : {e}[/bold red]")
                    console.print(f"Notes jouées : {list(played_notes)}")
                    continue
            
            time.sleep(0.01)
        
        return None

class ListenAndGuessMode(GameModeBase):
    """Mode Écoute et Devine refactorisé."""
    
    def __init__(self, inport, outport, chord_set):
        super().__init__(inport, outport, chord_set, "Mode Écoute et Devine", "bold orange3", "orange3")
    
    def run(self):
        """Lance le mode écoute et devine."""
        while not self.exit_flag:
            self.clear_midi_buffer()
            chord_name, chord_notes = random.choice(list(self.chord_set.items()))
            
            self.display_header("Écoutez l'accord joué et essayez de le reproduire.\nAppuyez sur 'q' pour quitter, 'r' pour répéter l'accord.")
            
            console.print(f"\n[bold yellow]Lecture de l'accord...[/bold yellow]")
            play_chord(self.outport, chord_notes)
            console.print("Jouez l'accord que vous venez d'entendre.")
            
            if self.play_guess_round(chord_name, chord_notes):
                self.session.correct_count += 1
                console.print("\n[bold green]Bravo ! Accord suivant...[/bold green]")
                time.sleep(1.5)
                # Suppression du break pour continuer avec d'autres accords
            else:
                console.print("\n[bold yellow]Accord suivant...[/bold yellow]")
                time.sleep(1.5)
        
        self.display_stats()
        console.print("\nAppuyez sur une touche pour retourner au menu principal.")
        wait_for_any_key(self.inport)
    
    def play_guess_round(self, chord_name, chord_notes):
        """Joue un round de devinette et retourne True si correct."""
        self.midi_handler.clear()
        incorrect_attempts = 0
        
        while not self.exit_flag:
            char = wait_for_input(timeout=0.01)
            if self.handle_common_keys(char):
                return False  # Sortie demandée par l'utilisateur
            if char and char.lower() == 'r':
                console.print(f"[bold blue]Répétition de l'accord...[/bold blue]")
                play_chord(self.outport, chord_notes)
                continue
            
            self.midi_handler.update()
            
            if self.midi_handler.has_chord_ready():
                played_notes = self.midi_handler.get_played_notes()
                attempt = ChordAttempt(played_notes, chord_name, chord_notes)
                
                try:
                    attempt = ChordValidator.validate_chord_attempt(attempt)
                    self.session.total_attempts += 1
                    
                    if attempt.is_correct:
                        self.display_chord_feedback(attempt, show_target=True)
                        return True
                    else:
                        incorrect_attempts += 1
                        self.display_chord_feedback(attempt, show_target=False)
                        
                        if incorrect_attempts >= 3:
                            tonic_note = sorted(list(chord_notes))[0]
                            tonic_name = get_note_name(tonic_note)
                            console.print(f"Indice : La tonique est [bold cyan]{tonic_name}[/bold cyan].")
                        
                        if incorrect_attempts >= 7:
                            revealed_type = get_chord_type_from_name(chord_name)
                            console.print(f"Indice : C'est un accord de type [bold yellow]{revealed_type}[/bold yellow].")
                            console.print(f"[bold magenta]La réponse était : {chord_name}[/bold magenta]")
                            Prompt.ask("\nAppuyez sur Entrée pour continuer...", console=console)
                            return False
                
                except Exception as e:
                    console.print(f"[bold red]Erreur lors de la reconnaissance : {e}[/bold red]")
                    console.print(f"Notes jouées : {list(played_notes)}")
                    continue
            
            time.sleep(0.01)
        
        return False

# --- Mode Explorateur d'Accords (inchangé car déjà simple) ---
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

            lookup_key = user_input.lower().replace(" ", "")
            full_chord_name = chord_aliases.get(lookup_key)

            if full_chord_name and full_chord_name in all_chords:
                chord_notes_midi = all_chords[full_chord_name]
                sorted_notes_midi = sorted(list(chord_notes_midi))
                note_names = [get_note_name(n) for n in sorted_notes_midi]
                notes_str = ", ".join(note_names)

                console.print(f"L'accord [bold green]{full_chord_name}[/bold green] est composé des notes : [bold yellow]{notes_str}[/bold yellow]")
                console.print("Lecture de l'accord...")
                play_chord(outport, chord_notes_midi, duration=1.2)
            else:
                console.print(f"[bold red]Accord '{user_input}' non reconnu.[/bold red] Veuillez réessayer.")

        except Exception as e:
            console.print(f"[bold red]Une erreur est survenue : {e}[/bold red]")
            time.sleep(2)

    console.print("\nRetour au menu principal.")
    time.sleep(1)

# --- Mode Reconnaissance Libre (simplifié) ---
def reverse_chord_mode(inport):
    """Mode de reconnaissance d'accords joués par l'utilisateur."""
    clear_screen()
    console.print(Panel(
        Text("Mode Reconnaissance d'accords (Tous les accords)", style="bold cyan", justify="center"),
        title="Reconnaissance d'accords",
        border_style="cyan"
    ))
    console.print("Jouez un accord sur votre clavier MIDI.")
    console.print("Appuyez sur 'q' pour quitter.")

    midi_handler = MidiInputHandler(inport)

    while True:
        char = wait_for_input(timeout=0.01)
        if char and char.lower() == 'q':
            break

        midi_handler.update()

        if midi_handler.has_chord_ready():
            played_notes = midi_handler.get_played_notes()
            
            if len(played_notes) > 1:
                chord_name, inversion_label = recognize_chord(played_notes)
                
                if chord_name:
                    enharmonic_name = enharmonic_map.get(chord_name, [])
                    if enharmonic_name:
                        console.print(f"Accord reconnu : [bold green]{chord_name}[/bold green] ou [bold green]{enharmonic_name[0]}[/bold green] ({inversion_label})")
                    else:
                        console.print(f"Accord reconnu : [bold green]{chord_name}[/bold green] ({inversion_label})")
                else:
                    colored_string = ", ".join([f"[bold red]{get_note_name(n)}[/bold red]" for n in sorted(list(played_notes))])
                    console.print(f"[bold red]Accord non reconnu.[/bold red] Notes jouées : [{colored_string}]")
            else:
                console.print("[bold yellow]Veuillez jouer au moins 2 notes pour former un accord.[/bold yellow]")
        
        time.sleep(0.01)

# --- Fonctions principales et menu (simplifiées) ---
def options_menu(use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set_choice):
    """Menu d'options pour configurer le programme."""
    while True:
        clear_screen()
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
        
        panel = Panel(panel_content, title="Menu Options", border_style="cyan")
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
        console.print("[bold red]Annulation de la sélection du port d'entrée.[/bold red]")
        return

    outport_name = select_midi_port("output")
    if not outport_name:
        console.print("[bold red]Annulation de la sélection du port de sortie.[/bold red]")
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
                
                menu_panel = Panel(menu_options, title="Menu Principal", border_style="bold blue")
                console.print(menu_panel)
                
                # MODIFIÉ: Mise à jour des choix possibles
                mode_choice = Prompt.ask("Votre choix", choices=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'], show_choices=False, console=console)
                
                if mode_choice == '1':
                    chord_explorer_mode(outport)
                elif mode_choice == '2':
                    mode = SingleChordMode(inport, outport, current_chord_set)
                    mode.run()
                elif mode_choice == '3':
                    mode = ListenAndGuessMode(inport, outport, current_chord_set)
                    mode.run()
                elif mode_choice == '4':
                    reverse_chord_mode(inport)
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