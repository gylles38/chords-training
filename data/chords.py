# data/chords.py

# Dictionnaire des accords. La clé est le nom de l'accord, et la valeur est un ensemble
# des numéros de notes MIDI pour cet accord, dans une octave de référence.
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
        "name": "Progression 'Pop-Punk'",
        "progression": ["Do Majeur", "Sol Majeur", "La Mineur", "Fa Majeur"],
        "examples": ["'Let It Be' - The Beatles", "'Don't Stop Believin'' - Journey", "'Take On Me' - a-ha"],
        "commentary": "Aussi connue sous le nom de I-V-vi-IV, c'est sans doute la progression la plus utilisée dans la musique pop occidentale de ces dernières décennies."
    },
    "2": {
        "name": "Progression 'Doo-Wop'",
        "progression": ["Do Majeur", "La Mineur", "Fa Majeur", "Sol Majeur"],
        "examples": ["'No Woman, No Cry' - Bob Marley", "'Stand By Me' - Ben E. King", "'I'm Yours' - Jason Mraz"],
        "commentary": "Cette progression I-vi-IV-V, très populaire dans les années 50 et 60, évoque une certaine nostalgie et est toujours très utilisée aujourd'hui."
    },
    "3": {
        "name": "Progression 'Canon de Pachelbel'",
        "progression": ["Sol Majeur", "Ré Majeur", "Mi Mineur", "Do Majeur"],
        "examples": ["'With or Without You' - U2", "'Wake Me Up When September Ends' - Green Day", "'Canon in D' - Pachelbel"],
        "commentary": "Basée sur le célèbre Canon de Pachelbel, cette progression a une sonorité épique et ascendante, souvent utilisée dans les hymnes rock."
    },
    "4": {
        "name": "Progression 'Sensible'",
        "progression": ["Mi Mineur", "Do Majeur", "Sol Majeur", "Ré Majeur"],
        "examples": ["'All of Me' - John Legend", "'Apologize' - OneRepublic", "'Someone Like You' - Adele"],
        "commentary": "Cette progression vi-IV-I-V est très expressive et est souvent utilisée pour les ballades et les chansons émouvantes."
    },
}

tonal_progressions = {
    "Cadence Parfaite": {
        "progression": ["I", "V", "I"],
        "description": "Très conclusive, donne un sentiment de résolution. Souvent utilisée à la fin des phrases musicales."
    },
    "Cadence Plagale": {
        "progression": ["IV", "I"],
        "description": "Aussi conclusive, mais plus douce et moins dramatique. Connue comme la cadence 'Amen'."
    },
    "Progression I-IV-V-I": {
        "progression": ["I", "IV", "V", "I"],
        "description": "Une progression très stable et fréquente dans la musique occidentale, évoquant la clarté et la joie."
    },
    "Progression ii-V-I": {
        "progression": ["ii", "V", "I"],
        "description": "La pierre angulaire de l'harmonie jazz. Crée une forte tension puis une résolution vers la tonique."
    },
    "Progression I-V-vi-IV": {
        "progression": ["I", "V", "vi", "IV"],
        "description": "La progression 'quatre accords magiques', omniprésente en pop et rock. Peut sonner joyeuse ou mélancolique."
    }
}

# --- Génération des gammes mineures ---
# On génère les gammes mineures naturelles à partir des gammes majeures relatives.
# La gamme mineure naturelle commence sur le 6ème degré de la gamme majeure.
gammes_mineures = {}
for major_key, chords in gammes_majeures.items():
    # Le nom de la gamme mineure est le nom de l'accord du 6ème degré (index 5)
    relative_minor_name = chords[5]

    # Les accords de la gamme mineure sont une rotation des accords de la gamme majeure
    # La liste commence par le 6ème degré de la gamme majeure.
    minor_chords = chords[5:] + chords[:5]

    gammes_mineures[relative_minor_name] = minor_chords

# --- Dictionnaire unifié de toutes les gammes ---
# Pour un accès facile dans les modes de jeu.
all_scales = {**gammes_majeures, **gammes_mineures}
