# data/progression_path.py

"""
Ce fichier définit le parcours de progression pour l'utilisateur.
Chaque étape est un dictionnaire contenant :
- title: Le nom de l'étape, affiché à l'utilisateur.
- description: Une courte explication de l'exercice.
- mode_id: Un identifiant unique pour le mode de jeu associé.
- params: Un dictionnaire d'arguments à passer à la fonction du mode.
"""

progression_path = [
    {
        "title": "1. Reconnaissance de notes",
        "description": "Apprenez à identifier et jouer des notes uniques sur le clavier.",
        "mode_id": "SINGLE_NOTE",
        "params": {}
    },
    {
        "title": "2. Explorateur d'accords",
        "description": "Explorez librement différents types d'accords et écoutez leur sonorité.",
        "mode_id": "CHORD_EXPLORER",
        "params": {}
    },
    {
        "title": "3. Accords simples",
        "description": "Entraînez-vous à reconnaître et jouer les accords majeurs et mineurs de base.",
        "mode_id": "SINGLE_CHORD",
        "params": {"chord_set_choice": "basic"}
    },
    {
        "title": "4. Écoutez et devinez",
        "description": "Développez votre oreille en écoutant un accord puis en le jouant.",
        "mode_id": "LISTEN_AND_REVEAL",
        "params": {"chord_set_choice": "basic"}
    },
    {
        "title": "5. Les degrés de la gamme",
        "description": "Comprenez le rôle de chaque accord dans une tonalité (I, IV, V, etc.).",
        "mode_id": "DEGREES",
        "params": {"chord_set_choice": "basic"}
    },
    {
        "title": "6. Progressions d'accords simples",
        "description": "Commencez à enchaîner des accords pour former des progressions courantes.",
        "mode_id": "PROGRESSION",
        "params": {"chord_set_choice": "basic"}
    },
    {
        "title": "7. Les cadences",
        "description": "Apprenez à reconnaître les cadences, ces formules qui concluent les phrases musicales.",
        "mode_id": "CADENCE",
        "params": {"chord_set_choice": "basic"}
    },
    {
        "title": "8. Progressions Pop/Rock",
        "description": "Jouez les progressions d'accords les plus utilisées dans la musique populaire.",
        "mode_id": "POP_ROCK",
        "params": {}
    },
    {
        "title": "9. Progressions tonales avancées",
        "description": "Explorez des progressions plus complexes dans un contexte tonal.",
        "mode_id": "TONAL_PROGRESSION",
        "params": {}
    },
    {
        "title": "10. Transitions d'accords",
        "description": "Travaillez sur le 'voice leading' pour des transitions d'accords fluides.",
        "mode_id": "CHORD_TRANSITIONS",
        "params": {"use_voice_leading": True}
    }
]
